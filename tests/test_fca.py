import pandas as pd

from rfmfca.fca import ConceptLattice


def toy_context():
    # Classic 4-object example: the closed intents are {}, {a}, {b}, {a,b}, {a,c}, {a,b,c}.
    return pd.DataFrame(
        [[1, 1, 0], [1, 0, 1], [1, 1, 1], [0, 1, 0]],
        columns=["a", "b", "c"], index=list("wxyz"),
    ).astype(bool)


def test_concepts_are_all_closed_intents():
    lat = ConceptLattice(toy_context())
    got = {lat.label(c.intent): c.extent_size for c in lat.concepts}
    assert got == {"{}": 4, "{b}": 3, "{a}": 3, "{a, b}": 2, "{a, c}": 2, "{a, b, c}": 1}


def test_every_intent_equals_its_closure():
    lat = ConceptLattice(toy_context())
    for c in lat.concepts:
        assert lat._closure(c.intent) == c.intent or c.extent_size == 0


def test_lower_covers():
    lat = ConceptLattice(toy_context())
    m = {name: 1 << k for k, name in enumerate("abc")}
    covers = {lat.label(j) for j in lat.lower_covers[m["a"]]}
    assert covers == {"{a, b}", "{a, c}"}
    assert lat.lower_covers[m["a"] | m["b"] | m["c"]] == []


def test_rules_confidence():
    lat = ConceptLattice(toy_context())
    rules = lat.association_rules()
    row = rules[(rules.premise == "a") & (rules.conclusion == "b")].iloc[0]
    assert row.premise_customers == 3 and row.rule_customers == 2
    assert abs(row.confidence - 2 / 3) < 1e-12


def test_bottom_concept_with_empty_extent():
    ctx = pd.DataFrame([[1, 0], [0, 1]], columns=["a", "b"]).astype(bool)
    lat = ConceptLattice(ctx)
    assert {lat.label(c.intent): c.extent_size for c in lat.concepts} == \
        {"{}": 2, "{a}": 1, "{b}": 1, "{a, b}": 0}
