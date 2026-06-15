from graphs import edmonds_karp, min_cut
from boykov_kolmogorov import boykov_kolmogorov
 
 
def test_ek_classic():
    caps = {('s','a'):10,('s','b'):8,('a','c'):5,('a','b'):4,('b','d'):9,('b','c'):6,('c','t'):10,('d','t'):7,('c','d'):2}
    mf, fl = edmonds_karp(caps, 's', 't')
    assert mf == 17, f'Expected 17, got {mf}'
    S, T, cut = min_cut(caps, fl, 's')
    assert 's' in S and 't' in T
    assert S.isdisjoint(T)
    assert sum(caps[e] for e in cut) == mf
 
 
def test_bk_classic():
    caps = {('s','a'):10,('s','b'):8,('a','c'):5,('a','b'):4,('b','d'):9,('b','c'):6,('c','t'):10,('d','t'):7,('c','d'):2}
    mf, flow, S, T = boykov_kolmogorov(caps, 's', 't')
    assert mf == 17, f'Expected 17, got {mf}'
    S2, T2, cut = min_cut(caps, flow, 's')
    assert 's' in S2 and 't' in T2
    assert S2.isdisjoint(T2)
    assert sum(caps[e] for e in cut) == mf
 
 
def test_both_agree_on_flow_value():
    # Both algorithms must find the same max flow value
    caps = {('s','a'):10,('s','b'):8,('a','c'):5,('a','b'):4,('b','d'):9,('b','c'):6,('c','t'):10,('d','t'):7,('c','d'):2}
    mf_ek, _ = edmonds_karp(caps, 's', 't')
    mf_bk, _, _, _ = boykov_kolmogorov(caps, 's', 't')
    assert mf_ek == mf_bk, f'EK={mf_ek} BK={mf_bk} disagree'
 
 
def test_chain_bottleneck_end():
    g = {(0,1):10, (1,2):5}
    mf, _, _, _ = boykov_kolmogorov(g, 0, 2)
    assert mf == 5, f'Expected 5, got {mf}'
 
 
def test_chain_bottleneck_start():
    g = {(0,1):3, (1,2):10}
    mf, _, _, _ = boykov_kolmogorov(g, 0, 2)
    assert mf == 3, f'Expected 3, got {mf}'
 
 
def test_two_parallel_paths():
    g = {(0,1):10,(1,3):10,(0,2):10,(2,3):10}
    mf, _, _, _ = boykov_kolmogorov(g, 0, 3)
    assert mf == 20, f'Expected 20, got {mf}'
 
 
def test_disconnected_graph():
    # No path from s to t -> max flow = 0
    g = {(0,1):5, (2,3):5}
    mf, _, S, T = boykov_kolmogorov(g, 0, 3)
    assert mf == 0, f'Expected 0, got {mf}'
 
 
def test_back_edge_cancellation():
    # Tests that augmenting along a residual back-edge works correctly.
    # The bug was: if capacities[(u,v)] treated cap=0 as a signal to update
    # the reverse edge, which is wrong — flow[(u,v)] += bottleneck always applies.
    g = {('s','a'):5, ('a','b'):5, ('b','t'):5, ('s','b'):3, ('b','a'):0}
    mf_ek, fl_ek = edmonds_karp(g, 's', 't')
    mf_bk, fl_bk, _, _ = boykov_kolmogorov(g, 's', 't')
    assert mf_ek == mf_bk, f'Back-edge: EK={mf_ek} BK={mf_bk} disagree'
 
 
def test_s_t_not_in_pixel_sets():
    # s and t should never appear in the returned S or T pixel sets
    caps = {('s','a'):10,('s','b'):8,('a','c'):5,('a','b'):4,('b','d'):9,('b','c'):6,('c','t'):10,('d','t'):7,('c','d'):2}
    _, _, S, T = boykov_kolmogorov(caps, 's', 't')
    assert 's' not in S and 's' not in T, 's should not be in pixel sets'
    assert 't' not in S and 't' not in T, 't should not be in pixel sets'
 
 
def test_partition_is_complete():
    # Every node except s and t must be in exactly one of S or T
    caps = {('s','a'):10,('s','b'):8,('a','c'):5,('a','b'):4,('b','d'):9,('b','c'):6,('c','t'):10,('d','t'):7,('c','d'):2}
    _, _, S, T = boykov_kolmogorov(caps, 's', 't')
    all_nodes = {'a', 'b', 'c', 'd'}
    assert S | T == all_nodes, f'Missing nodes: {all_nodes - S - T}'
    assert S.isdisjoint(T), f'Overlap: {S & T}'
 
 
def test_large_capacity():
    # Should handle large capacity values without overflow
    g = {('s','a'):10**9, ('a','t'):10**9}
    mf, _, _, _ = boykov_kolmogorov(g, 's', 't')
    assert mf == 10**9, f'Expected 1e9, got {mf}'
 
 
def test_single_edge():
    g = {('s','t'):7}
    mf, _, _, _ = boykov_kolmogorov(g, 's', 't')
    assert mf == 7, f'Expected 7, got {mf}'