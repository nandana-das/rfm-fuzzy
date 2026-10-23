"""Fuzzy RFM context and fuzzy concept lattice (Bělohlávek) over a finite chain.

Truth degrees are stored as integer level indices 0..n_levels-1 (degree =
index / (n_levels - 1)). With n_levels = 2 every operation reduces to classical
FCA, which is how the crisp base-paper method is expressed here as well.
"""
import numpy as np
import pandas as pd

from rfmfca.rfm import DIMENSIONS

CENTRES = np.array([0.1, 0.3, 0.5, 0.7, 0.9])   # quintile midpoints on the rank scale
HALF_WIDTH = 0.2
ATTRIBUTES = [f"{d}{k}" for d in DIMENSIONS for k in range(1, 6)]
VALUE_COLUMNS = {"R": "recency_days", "F": "transaction_count", "M": "amount"}


# -- rank scale ---------------------------------------------------------------

class RankScaler:
    """Map R, F, M to mid-rank percentiles of the fitted customers (higher = better)."""

    def fit(self, rfm):
        self.sorted_ = {d: np.sort(self._oriented(rfm, d)) for d in DIMENSIONS}
        return self

    @staticmethod
    def _oriented(rfm, dim):
        x = rfm[VALUE_COLUMNS[dim]].to_numpy(float)
        return -x if dim == "R" else x     # low recency is good

    def transform(self, rfm):
        out = {}
        for d in DIMENSIONS:
            ref = self.sorted_[d]
            x = self._oriented(rfm, d)
            less = np.searchsorted(ref, x, side="left")
            equal = np.searchsorted(ref, x, side="right") - less
            # Mid-rank; an unseen value (equal == 0) sits half a rank above `less`.
            out[d] = np.minimum((less + (equal + 1) / 2) / len(ref), 1.0)
        return pd.DataFrame(out, index=rfm.index)

    def transform_intervals(self, rfm):
        """Rank interval [lo, hi] each customer's tied block occupies among the fitted customers.

        A block of `equal` > 1 tied values spans `equal` ranks, centred on the same
        mid-rank `transform` returns. Untied and unseen values get a zero-width
        interval at that mid-rank, so for them nothing changes.
        """
        mid = self.transform(rfm)
        lo, hi = {}, {}
        for d in DIMENSIONS:
            ref = self.sorted_[d]
            x = self._oriented(rfm, d)
            less = np.searchsorted(ref, x, side="left")
            equal = np.searchsorted(ref, x, side="right") - less
            tied = equal > 1
            lo[d] = np.where(tied, (less + 0.5) / len(ref), mid[d])
            hi[d] = np.where(tied, np.minimum((less + equal + 0.5) / len(ref), 1.0), mid[d])
        return pd.DataFrame(lo, index=rfm.index), pd.DataFrame(hi, index=rfm.index)


# -- contexts -----------------------------------------------------------------

def term_memberships(u):
    """Five triangular memberships with saturating shoulders; rows sum to 1."""
    u = np.asarray(u, float)[:, None]
    m = np.clip(1 - np.abs(u - CENTRES) / HALF_WIDTH, 0, 1)
    m[:, 0] = np.where(u[:, 0] <= CENTRES[0], 1, m[:, 0])
    m[:, 4] = np.where(u[:, 0] >= CENTRES[4], 1, m[:, 4])
    return m


def fuzzy_context(ranks, n_levels=3):
    """Fuzzy context as level indices (n x 15), memberships rounded to the chain."""
    grid = np.linspace(0, 1, n_levels)
    cols = []
    for d in DIMENSIONS:
        m = term_memberships(ranks[d])
        cols.append(np.abs(m[:, :, None] - grid).argmin(axis=2))
    return pd.DataFrame(np.hstack(cols).astype(np.int16), index=ranks.index, columns=ATTRIBUTES)


def interval_memberships(lo, hi, n_points=101):
    """Triangular memberships averaged over u ~ Uniform[lo, hi] (midpoint rule)."""
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    t = (np.arange(n_points) + 0.5) / n_points
    out = np.zeros((len(lo), 5))
    for k in range(n_points):
        out += term_memberships(lo + t[k] * (hi - lo))
    return out / n_points


def tie_aware_fuzzy_context(intervals, n_levels=3):
    """Like fuzzy_context, but a tied block's membership is averaged over its rank interval."""
    lo, hi = intervals
    grid = np.linspace(0, 1, n_levels)
    cols = []
    for d in DIMENSIONS:
        m = interval_memberships(lo[d], hi[d])
        cols.append(np.abs(m[:, :, None] - grid).argmin(axis=2))
    return pd.DataFrame(np.hstack(cols).astype(np.int16), index=lo.index, columns=ATTRIBUTES)


def crisp_context(ranks):
    """Binary quintile context (levels 0/1): term = quintile of the rank, right-closed."""
    cols = []
    for d in DIMENSIONS:
        q = np.clip(np.ceil(np.asarray(ranks[d]) * 5 - 1e-9).astype(int) - 1, 0, 4)
        cols.append(np.eye(5, dtype=np.int16)[q])
    return pd.DataFrame(np.hstack(cols), index=ranks.index, columns=ATTRIBUTES)


# -- residuated implications on level indices ---------------------------------

def implication(a, b, top, residuum):
    if residuum == "lukasiewicz":
        return np.minimum(top, top - a + b)
    if residuum == "godel":
        return np.where(a <= b, top, b)
    raise ValueError(residuum)


# -- lattice ------------------------------------------------------------------

class FuzzyConceptLattice:
    """All fuzzy concepts of a context given as level indices.

    Intents are the pointwise-min closure of {a -> I(g, .) : g, a > 0} plus the
    all-top intent; this set is closed under the concept-forming operators for
    any residuated implication on a finite chain.
    """

    def __init__(self, context: pd.DataFrame, n_levels, residuum="lukasiewicz"):
        self.attributes = list(context.columns)
        self.n_levels, self.top, self.residuum = n_levels, n_levels - 1, residuum
        q = context.to_numpy(np.int16)
        self.rows_, self.row_counts_ = np.unique(q, axis=0, return_counts=True)
        self.n_objects = len(q)
        self.intents = self._closure_system()
        degrees = self.degrees(self.rows_)
        self.support = (degrees * self.row_counts_[:, None]).sum(axis=0) / self.n_objects
        # Core support: share of objects fully in the concept (1-cut of the extent).
        self.core_support = ((degrees >= 1) * self.row_counts_[:, None]).sum(axis=0) / self.n_objects
        self._lower_covers = None

    def _closure_system(self):
        gens = [implication(a, self.rows_, self.top, self.residuum) for a in range(1, self.n_levels)]
        gens = np.unique(np.vstack(gens).astype(np.int16), axis=0)
        closed = np.full((1, len(self.attributes)), self.top, np.int16)
        for g in gens:
            closed = np.unique(np.vstack([closed, np.minimum(closed, g)]), axis=0)
        # Top concept (empty intent, i.e. all zeros) first, then by size.
        order = np.lexsort((closed.sum(axis=1),))
        return closed[order]

    def degrees(self, context_levels, intents=None):
        """Membership degree in [0, 1] of each object (row) in each concept (column)."""
        intents = self.intents if intents is None else intents
        q = np.asarray(context_levels, np.int16)
        out = np.empty((len(q), len(intents)), np.float64)
        for j, b in enumerate(intents):
            out[:, j] = implication(b, q, self.top, self.residuum).min(axis=1)
        return out / self.top

    def frequent(self, min_support, kind="sigma"):
        """Indices of non-top concepts whose support (sigma-count or core) >= min_support."""
        support = {"sigma": self.support, "core": self.core_support}[kind]
        nonempty = self.intents.sum(axis=1) > 0
        return np.flatnonzero(nonempty & (support >= min_support - 1e-12))

    def induced_cover_rules(self, idx, min_confidence=0.0):
        """Rules along the covers of the sub-order on concepts `idx`, by core counts."""
        idx = np.asarray(idx)
        X = self.intents[idx]
        rows = []
        for a in range(len(idx)):
            sup = np.flatnonzero((X >= X[a]).all(axis=1))
            sup = sup[sup != a]
            below = (X[sup][:, None, :] <= X[sup][None, :, :]).all(axis=2)
            np.fill_diagonal(below, False)
            for b in sup[~below.any(axis=0)]:
                i, j = idx[a], idx[b]
                if self.core_support[i] == 0:
                    continue
                conf = self.core_support[j] / self.core_support[i]
                if conf >= min_confidence:
                    rows.append({"premise": self.label(self.intents[i]),
                                 "premise_core_count": self.core_support[i] * self.n_objects,
                                 "consequent_intent": self.label(self.intents[j]),
                                 "rule_core_count": self.core_support[j] * self.n_objects,
                                 "confidence": conf})
        cols = ["premise", "premise_core_count", "consequent_intent", "rule_core_count", "confidence"]
        return pd.DataFrame(rows, columns=cols).sort_values("confidence", ascending=False, ignore_index=True)

    def label(self, intent):
        parts = []
        for name, lv in zip(self.attributes, intent):
            if lv == self.top:
                parts.append(name)
            elif lv > 0:
                parts.append(f"{lv / self.top:g}/{name}")
        return "{" + ", ".join(parts) + "}"

    def table(self, index=None):
        idx = np.arange(len(self.intents)) if index is None else np.asarray(index)
        return pd.DataFrame({
            "concept": idx + 1,
            "intent": [self.label(self.intents[i]) for i in idx],
            "intent_size": self.intents[idx].sum(axis=1) / self.top,
            "support": self.support[idx],
            "sigma_count": self.support[idx] * self.n_objects,
            "core_support": self.core_support[idx],
        })

    def lower_covers(self):
        """For each concept, the indices of the concepts directly below it (larger intents)."""
        if self._lower_covers is None:
            X = self.intents
            covers = []
            for i in range(len(X)):
                sup = np.flatnonzero((X >= X[i]).all(axis=1))
                sup = sup[sup != i]
                S = X[sup]
                # j covers i iff no other k in sup has S[k] <= S[j].
                below = (S[:, None, :] <= S[None, :, :]).all(axis=2)
                np.fill_diagonal(below, False)
                covers.append(sup[~below.any(axis=0)])
            self._lower_covers = covers
        return self._lower_covers

    def association_rules(self, min_confidence=0.0):
        """Rules along covers: intent(upper) => intent(lower), confidence by sigma-counts."""
        rows = []
        for i, lowers in enumerate(self.lower_covers()):
            if self.intents[i].sum() == 0 or self.support[i] == 0:
                continue
            for j in lowers:
                conf = self.support[j] / self.support[i]
                if self.support[j] > 0 and conf >= min_confidence:
                    rows.append({"premise": self.label(self.intents[i]),
                                 "premise_sigma_count": self.support[i] * self.n_objects,
                                 "consequent_intent": self.label(self.intents[j]),
                                 "rule_sigma_count": self.support[j] * self.n_objects,
                                 "confidence": conf})
        cols = ["premise", "premise_sigma_count", "consequent_intent", "rule_sigma_count", "confidence"]
        return pd.DataFrame(rows, columns=cols).sort_values("confidence", ascending=False, ignore_index=True)
