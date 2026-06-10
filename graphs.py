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
    adj_lst = defaultdict(set)

    for (u,v) in graph:
        adj_lst[u].add(v)
        adj_lst[v].add(u)

    capacities = dict(graph) #original capacities
    flow = defaultdict(int) # flow on every edge (incl. reverse)

    def residual(u, v):
        return capacities.get((u,v), 0) - flow[(u,v)] + flow[(v,u)]
    
    def bfs_path():
        """Return a list [s, ..., t] of nodes forming an augmenting path, or None."""
        parent = {s: None}
        q = deque([s])
        while q:
            u = q.popleft()
            if u == t: 
                break
            for v in adj_lst[u]:
                if v not in parent and residual(u,v) > 0:
                    parent[v] = u
                    q.append(v)
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
    """Return (S, T, cut_edges) from the residual graph after max flow."""

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
