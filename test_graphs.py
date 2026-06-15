from graphs import edmonds_karp, min_cut
from boykov_kolmogorov import boykov_kolmogorov

def test_edmonds_karp_max_flow_value_and_min_cut():
    caps = {
        ("s", "a"): 10,
        ("s", "b"): 8,
        ("a", "c"): 5,
        ("a", "b"): 4,
        ("b", "d"): 9,
        ("b", "c"): 6,
        ("c", "t"): 10,
        ("d", "t"): 7,
        ("c", "d"): 2,
    }

    mf, fl = edmonds_karp(caps, "s", "t")

    assert mf == 17

    S, T, cut = min_cut(caps, fl, "s")

    assert "s" in S
    assert "t" in T
    assert S.isdisjoint(T)

    # Max-flow min-cut theorem: cut capacity equals max flow
    assert sum(caps[e] for e in cut) == mf

def test_bk_max_flow_value_and_min_cut():
    caps = {
        ("s", "a"): 10,
        ("s", "b"): 8,
        ("a", "c"): 5,
        ("a", "b"): 4,
        ("b", "d"): 9,
        ("b", "c"): 6,
        ("c", "t"): 10,
        ("d", "t"): 7,
        ("c", "d"): 2,
    }

    mf, flow, S, T = boykov_kolmogorov(caps, "s", "t")

    assert mf == 17

    S, T, cut = min_cut(caps, flow, "s")

    assert "s" in S
    assert "t" in T
    assert S.isdisjoint(T)

    # Max-flow min-cut theorem: cut capacity equals max flow
    assert sum(caps[e] for e in cut) == mf
