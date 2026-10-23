"""Formal concept analysis on a binary context.

Intents are stored as integer bitmasks over the attribute list, so the
attribute count is limited to what fits comfortably in a Python int (any size
works, but the RFM contexts here have 15 attributes).
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Concept:
    intent: int          # bitmask over context attributes
    extent_size: int


class ConceptLattice:
    """All formal concepts of a binary context, with the cover relation."""

    def __init__(self, context: pd.DataFrame):
        self.attributes = list(context.columns)
        self.n_objects = len(context)
        bits = 1 << np.arange(len(self.attributes), dtype=object)
        rows = context.to_numpy(dtype=bool)
        row_masks = [int(sum(bits[row])) for row in rows]
        self._masks, self._counts = np.unique(np.array(row_masks, dtype=object), return_counts=True)
        self._object_masks = row_masks
        self.concepts = self._build_concepts()
        self.lower_covers = self._covers()

    # -- construction -------------------------------------------------------

    def _build_concepts(self):
        # Closed intents are exactly the intersections of object intents, plus
        # the full attribute set (the bottom concept, empty when no object has
        # every attribute).
        closed = set()
        for mask in self._masks:
            closed |= {mask & other for other in closed}
            closed.add(mask)
        full = (1 << len(self.attributes)) - 1
        closed.add(full)
        if self.n_objects:
            closed.add(self._closure(0))
        concepts = [Concept(i, self.extent_size(i)) for i in closed]
        # Top first: largest extent, then fewest attributes.
        concepts.sort(key=lambda c: (-c.extent_size, bin(c.intent).count("1"), c.intent))
        return concepts

    def _closure(self, intent):
        common = -1
        for mask in self._masks:
            if mask & intent == intent:
                common &= mask
        return common & ((1 << len(self.attributes)) - 1)

    def _covers(self):
        intents = [c.intent for c in self.concepts]
        covers = {}
        for i in intents:
            supers = [j for j in intents if j != i and j & i == i]
            covers[i] = [j for j in supers
                         if not any(k != j and j & k == k for k in supers)]
        return covers

    # -- queries ------------------------------------------------------------

    def extent_size(self, intent):
        hit = np.fromiter((m & intent == intent for m in self._masks), bool, len(self._masks))
        return int(self._counts[hit].sum())

    def extent(self, intent, index):
        """Labels (from `index`) of the objects having every attribute in `intent`."""
        hit = [m & intent == intent for m in self._object_masks]
        return index[np.array(hit, dtype=bool)]

    def support(self, intent):
        return self.extent_size(intent) / self.n_objects

    def names(self, intent):
        return [a for k, a in enumerate(self.attributes) if intent >> k & 1]

    def label(self, intent):
        return "{" + ", ".join(self.names(intent)) + "}"

    def table(self):
        return pd.DataFrame({
            "concept": range(1, len(self.concepts) + 1),
            "attributes": [self.label(c.intent) for c in self.concepts],
            "support": [c.extent_size / self.n_objects for c in self.concepts],
            "customers": [c.extent_size for c in self.concepts],
        })

    def association_rules(self, min_confidence=0.0):
        """Partial implications along lattice covers (Luxenburger basis).

        Each rule goes from a concept's intent P to one of its lower covers'
        intents Q, with conclusion Q \\ P and confidence |ext Q| / |ext P|.
        This is the "<N> P =[C]=> <N'> C'" form of the base paper's Table 5.
        """
        rows = []
        for c in self.concepts:
            if c.extent_size == 0:
                continue
            for lower in self.lower_covers[c.intent]:
                n_lower = self.extent_size(lower)
                conf = n_lower / c.extent_size
                if n_lower and conf >= min_confidence and c.intent:
                    rows.append({
                        "premise": " ".join(self.names(c.intent)),
                        "premise_customers": c.extent_size,
                        "conclusion": " ".join(self.names(lower & ~c.intent)),
                        "rule_customers": n_lower,
                        "confidence": conf,
                    })
        out = pd.DataFrame(rows, columns=["premise", "premise_customers", "conclusion",
                                          "rule_customers", "confidence"])
        return out.sort_values("confidence", ascending=False, ignore_index=True)

    def frequent(self, min_support):
        """Concepts with support >= min_support, excluding the top concept."""
        return [c for c in self.concepts
                if c.intent and c.extent_size / self.n_objects >= min_support]

    def induced_covers(self, concepts):
        """Cover relation of the sub-order on `concepts` (for drawing a pruned Hasse diagram)."""
        intents = [c.intent for c in concepts]
        edges = []
        for i in intents:
            supers = [j for j in intents if j != i and j & i == i]
            for j in supers:
                if not any(k != j and j & k == k for k in supers):
                    edges.append((i, j))
        return edges
