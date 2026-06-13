from collections import defaultdict, deque

graph = {}

def edmonds_karp(graph, s, t):

    """
        Args:
            graph_caps: dict (u, v) -> capacity (only forward edges listed).
            s: source name; t: sink name.
        Returns:
            (max_flow, flow_dict) where flow_dict[(u, v)] is the flow on edge (u,v).
    """

    # Storing the neighbours of the node
    adj_lst = defaultdict(set) #{ v : ()}, alternative approach { v: {l: 10}, u: {}}
 
    for (u,v) in graph:
        adj_lst[u].add(v)
        adj_lst[v].add(u)

    capacities = dict(graph) #original capacities
    flow = defaultdict(int) # flow on every edge (incl. reverse), initially, everything set to 0

    def residual(u, v):
        return capacities.get((u,v), 0) - flow[(u,v)] + flow[(v,u)]
    
    def bfs_path():
        """Return a list [s, ..., t] of nodes forming an augmenting path, or None."""
        parent = {s: None}
        q = deque([s])
        while q:
            #FIFO
            u = q.popleft()
            if u == t: 
                break
            for v in adj_lst[u]:
                if v not in parent and residual(u,v) > 0:
                    parent[v] = u
                    q.append(v)
        # After exploring the whole q, if t is not in parent -> we did not reach it
        if t not in parent:
            return None
        path, cur = [] , t
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        return path[::-1]

    max_flow = 0
    while True:
        path = bfs_path()
        if path is None:
            break

        bottleneck = min(residual(path[i], path[i+1]) for i in range(len(path) - 1))

        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            # Cancel reverse flow first, then add forward
            cancel = min(bottleneck, flow[(v,u)])
            flow[(v,u)] -= cancel
            flow[(u,v)] += bottleneck - cancel

        max_flow += bottleneck
    return max_flow, dict(flow)

def min_cut(graph, flow, s):
    """Return (S, T, cut_edges) from the RESIDUAL graph after max flow."""

    nbrs = defaultdict(set)
    for (u,v) in graph:
        nbrs[u].add(v)
        nbrs[v].add(u)

    def residual(u, v):
        return graph.get((u,v), 0) - flow.get((u,v), 0) + flow.get((v,u), 0) 
    
    S = {s}
    q = deque([s])

    while q: 
        u = q.popleft() 
        for v in nbrs[u]:
            if v not in S and residual(u, v) > 0:
                S.add(v)
                q.append(v)
    T = set(nbrs.keys()) - S
    cut = [(u,v) for (u,v) in graph if u in S and v in T]
    return S, T, cut


caps = {
("s", "a"): 10, ("s", "b"): 8,
("a", "c"): 5, ("a", "b"): 4,
("b", "d"): 9, ("b", "c"): 6,
("c", "t"): 10, ("d", "t"): 7,
("c", "d"): 2,
}
mf, fl = edmonds_karp(caps, "s", "t")
print(f"Maximum flow s -> t : {mf} Gb/s")
for (u, v), f in sorted(fl.items()):
    if f > 0 and (u, v) in caps:
        print(f" {u} -> {v} : {f} / {caps[(u, v)]}")

S, T, cut = min_cut(caps, fl, "s")
print(f"S = {sorted(S)}")
print(f"T = {sorted(T)}")
print(f"Cut edges (to upgrade): {cut}")
print(f"Sum of cut capacities: {sum(caps[e] for e in cut)}")