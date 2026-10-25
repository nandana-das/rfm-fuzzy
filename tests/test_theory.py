"""Numerical checks of the theoretical properties of fuzzy RFM-FCA (special case, core support,
Łukasiewicz floor, greedy summary guarantee, tie-aware partition)."""
import itertools

import numpy as np
import pandas as pd

from rfmfca.fuzzy import (FuzzyConceptLattice, implication, interval_memberships, select_concepts,
                          term_memberships)

RNG = np.random.default_rng(42)


def random_context(n=60, m=6, levels=3):
    return pd.DataFrame(RNG.integers(0, levels, size=(n, m)), columns=[f"a{i}" for i in range(m)]).astype(np.int16)


def test_prop1_partition_and_cut():
    u = RNG.random(2000)
    m = term_memberships(u)
    assert np.allclose(m.sum(axis=1), 1)                       # Ruspini partition
    assert ((m > 0).sum(axis=1) <= 2).all()                    # at most two adjacent terms


def test_prop2_core_is_inclusion_for_both_residua():
    ctx = random_context()
    q = ctx.to_numpy()
    for res in ("lukasiewicz", "godel"):
        lat = FuzzyConceptLattice(ctx, 3, res)
        for b in lat.intents:
            deg = implication(b, q, 2, res).min(axis=1)
            assert ((deg == 2) == (q >= b).all(axis=1)).all()


def test_prop2_core_support_antimonotone():
    ctx = random_context()
    lat = FuzzyConceptLattice(ctx, 3, "lukasiewicz")
    for i, j in itertools.product(range(len(lat.intents)), repeat=2):
        if (lat.intents[j] >= lat.intents[i]).all():
            assert lat.core_support[j] <= lat.core_support[i] + 1e-12


def test_prop3_lukasiewicz_floor():
    ctx = random_context()
    lat = FuzzyConceptLattice(ctx, 3, "lukasiewicz")
    deg = lat.degrees(ctx.to_numpy())
    floor = 1 - lat.intents.max(axis=1) / 2
    assert (deg >= floor[None, :] - 1e-12).all()
    assert (lat.support >= floor - 1e-12).all()


def explained_mass(full, mass, s):
    return (full[:, s] * mass[s]).max(axis=1).sum() if len(s) else 0.0


def test_prop4_explained_mass_is_monotone_submodular():
    full = RNG.random((40, 8)) < 0.4
    mass = RNG.random(8) * 3
    for _ in range(300):
        a = list(np.flatnonzero(RNG.random(8) < 0.3))
        b = sorted(set(a) | set(np.flatnonzero(RNG.random(8) < 0.3)))
        x = int(RNG.integers(8))
        if x in b:
            continue
        fa, fb = explained_mass(full, mass, a), explained_mass(full, mass, b)
        assert fb >= fa - 1e-12                                                          # monotone
        assert explained_mass(full, mass, a + [x]) - fa >= explained_mass(full, mass, b + [x]) - fb - 1e-12


def test_prop4_greedy_is_within_one_minus_one_over_e():
    ctx = random_context(n=80, m=5)
    lat = FuzzyConceptLattice(ctx, 3, "lukasiewicz")
    cand = lat.frequent(0.05, "core")
    full = lat.degrees(lat.rows_, lat.intents[cand]) >= 1
    mass = lat.intents[cand].sum(axis=1) / 2
    w = lat.row_counts_
    f = lambda s: ((full[:, s] * mass[s]).max(axis=1) * w).sum() if len(s) else 0.0  # noqa: E731
    k = 3
    greedy = [list(cand).index(c) for c in select_concepts(lat, cand, k)]
    best = max(f(list(s)) for s in itertools.combinations(range(len(cand)), k))
    assert f(greedy) >= (1 - 1 / np.e) * best - 1e-9


def test_prop5_tie_averaging_keeps_partition():
    lo = RNG.random(500) * 0.7
    hi = lo + RNG.random(500) * 0.3
    m = interval_memberships(lo, hi)
    assert np.allclose(m.sum(axis=1), 1)
