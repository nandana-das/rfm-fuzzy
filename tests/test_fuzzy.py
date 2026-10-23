import numpy as np
import pandas as pd

from rfmfca.fca import ConceptLattice
from rfmfca.fuzzy import (FuzzyConceptLattice, RankScaler, crisp_context, fuzzy_context,
                          implication, term_memberships)


def test_memberships_partition_and_argmax_is_quintile():
    u = np.linspace(0.001, 1, 500)
    m = term_memberships(u)
    assert np.allclose(m.sum(axis=1), 1)
    q = np.clip(np.ceil(u * 5 - 1e-9).astype(int) - 1, 0, 4)
    off_boundary = np.abs(u * 5 - np.round(u * 5)) > 1e-6
    assert (m.argmax(axis=1) == q)[off_boundary].all()


def test_rank_scaler_orientation_and_unseen_values():
    rfm = pd.DataFrame({"recency_days": [0, 10, 20, 30],
                        "transaction_count": [1, 2, 3, 4], "amount": [1.0, 2, 3, 4]})
    sc = RankScaler().fit(rfm)
    u = sc.transform(rfm)
    assert list(u["R"]) == list(u["F"])[::-1]    # most recent ranks highest
    new = pd.DataFrame({"recency_days": [15], "transaction_count": [2.5], "amount": [100.0]})
    v = sc.transform(new)
    assert v.loc[0, "F"] == 0.625 and v.loc[0, "M"] == 1.0


def test_implications():
    a, b = np.array([0, 1, 2, 2]), np.array([2, 0, 1, 2])
    assert list(implication(a, b, 2, "lukasiewicz")) == [2, 1, 1, 2]
    assert list(implication(a, b, 2, "godel")) == [2, 0, 1, 2]


def toy():
    return pd.DataFrame([[1, 1, 0], [1, 0, 1], [1, 1, 1], [0, 1, 0]],
                        columns=["a", "b", "c"]).astype(np.int16)


def test_two_levels_reduce_to_crisp_fca():
    ctx = toy()
    fz = FuzzyConceptLattice(ctx, n_levels=2)
    cr = ConceptLattice(ctx.astype(bool))
    assert len(fz.intents) == len(cr.concepts)
    sizes = sorted(np.round(fz.support * 4).astype(int))
    assert sizes == sorted(c.extent_size for c in cr.concepts)


def test_fuzzy_intents_are_closed():
    rng = np.random.default_rng(0)
    ctx = pd.DataFrame(rng.integers(0, 3, size=(30, 4)), columns=list("abcd")).astype(np.int16)
    for res in ("lukasiewicz", "godel"):
        lat = FuzzyConceptLattice(ctx, n_levels=3, residuum=res)
        q = ctx.to_numpy()
        for b in lat.intents:
            ext = implication(b, q, 2, res).min(axis=1)             # B-down
            up = implication(ext[:, None], q, 2, res).min(axis=0)   # A-up
            assert (up == b).all()


def test_fuzzy_covers_and_rules():
    ctx = pd.DataFrame([[2, 1], [2, 2], [0, 2]], columns=["a", "b"]).astype(np.int16)
    lat = FuzzyConceptLattice(ctx, n_levels=3)
    covers = lat.lower_covers()
    for i, low in enumerate(covers):
        for j in low:
            assert (lat.intents[j] >= lat.intents[i]).all()
    rules = lat.association_rules()
    assert ((rules.confidence > 0) & (rules.confidence <= 1 + 1e-12)).all()


def test_crisp_context_one_hot():
    ranks = pd.DataFrame({"R": [0.1, 0.2, 0.21, 1.0], "F": [0.5] * 4, "M": [0.99] * 4})
    c = crisp_context(ranks)
    assert (c.sum(axis=1) == 3).all()
    assert list(c[["R1", "R2", "R5"]].idxmax(axis=1)) == ["R1", "R1", "R2", "R5"]
    f = fuzzy_context(ranks)
    assert f.loc[1, "R1"] == 1 and f.loc[1, "R2"] == 1   # u = 0.2 sits on the boundary: 0.5 / 0.5


def test_core_support_equals_support_when_crisp():
    lat = FuzzyConceptLattice(toy(), n_levels=2)
    assert np.allclose(lat.core_support, lat.support)
    assert list(lat.frequent(0.5, "core")) == list(lat.frequent(0.5))


def test_core_support_counts_full_members_only():
    ctx = pd.DataFrame([[2, 0], [1, 2], [0, 2]], columns=["a", "b"]).astype(np.int16)
    lat = FuzzyConceptLattice(ctx, n_levels=3)
    half_a = [i for i, b in enumerate(lat.intents) if list(b) == [1, 0]][0]
    # Lukasiewicz: degrees in {1/2 a} are 1, 1, 1/2 -> sigma 2.5/3, core 2/3.
    assert np.isclose(lat.support[half_a], 2.5 / 3)
    assert np.isclose(lat.core_support[half_a], 2 / 3)
    rules = lat.induced_cover_rules(lat.frequent(0.01, "core"))
    assert len(rules) > 0
    assert ((rules.confidence > 0) & (rules.confidence <= 1)).all()


def test_interval_memberships():
    from rfmfca.fuzzy import interval_memberships
    # A point interval equals the point membership.
    assert np.allclose(interval_memberships([0.42], [0.42]), term_memberships([0.42]))
    # Averaged over the whole scale each of the five terms gets mass 0.2.
    m = interval_memberships([0.0], [1.0], n_points=10001)[0]
    assert np.isclose(m.sum(), 1) and np.allclose(m, m[::-1], atol=1e-3)
    assert np.isclose(m[0], 0.2, atol=1e-3) and np.isclose(m[2], 0.2, atol=1e-3)


def test_tie_aware_context_spreads_tied_block():
    from rfmfca.fuzzy import tie_aware_fuzzy_context
    # 13 of 20 customers tied at the bottom of F (like one-time buyers in CDNOW).
    rfm = pd.DataFrame({"recency_days": np.arange(20), "transaction_count": [1] * 13 + list(range(2, 9)),
                        "amount": np.arange(20.0)})
    sc = RankScaler().fit(rfm)
    lo, hi = sc.transform_intervals(rfm)
    assert np.isclose(lo.loc[0, "F"], 0.025) and np.isclose(hi.loc[0, "F"], 0.675)
    assert np.isclose((lo.loc[0, "F"] + hi.loc[0, "F"]) / 2, sc.transform(rfm).loc[0, "F"])
    plain = fuzzy_context(sc.transform(rfm))
    tie = tie_aware_fuzzy_context((lo, hi))
    f_cols = [f"F{k}" for k in range(1, 6)]
    assert list(plain.loc[0, f_cols] > 0) == [False, True, False, False, False]   # mid-rank: F2 only
    assert list(tie.loc[0, f_cols]) == [1, 1, 1, 0, 0]         # interval: partly F1, F2, F3
    untied = [c for c in tie.columns if c[0] in "RM"]
    assert (tie[untied] == plain[untied]).all().all()          # untied dimensions unchanged
    assert (tie.loc[13:, f_cols] == plain.loc[13:, f_cols]).all().all()
