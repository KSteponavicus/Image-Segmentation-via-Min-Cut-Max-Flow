from collections import defaultdict, deque

def boykov_kolmogorov(graph, s, t):

    # Storing the neighbours of the node
    adj_lst = defaultdict(list) #{ node : [neighbours]}
    capacities = dict(graph) # original capacities

    # filling the adjacency list
    for (u,v) in graph:
        adj_lst[u].append(v)

    flow = defaultdict(int)

    # putting both s and t in the active state    
    active = deque([s,t])
    active_set = {s, t}

    tree = defaultdict(str) # storing the type of tree: "S", "T", ""
    parent = {s: None, t: None}

    tree[s] = "S"
    tree[t] = "T"
    max_flow = 0

    def residual(u, v):
        return capacities.get((u,v), 0) - flow[(u,v)] + flow[(v,u)]
    

    # finding the path from a given node to either s or t
    def path_to_root(node):
        path = []
        while node is not None:
            path.append(node)
            node = parent.get(node, None)
        return path

        
    # checks if a node belongs to the tree of a given type
    def is_in_tree(node, type):

        curr = node
        while curr is not None:
            if curr == s and type == "S":
                return True
            if curr == t and type == "T":
                return True
            curr = parent.get(curr, None)
        return False

    # augmenting the flow in the path by the bottleneck and searching for the orphans
    def augment(node_S, node_T):
        path_S = path_to_root(node_S) # starts from the node to the source
        path_S = path_S[::-1]              # now goes s → … → node_s

        path_T = path_to_root(node_T) # goes node_t → … → t
 
        full_path = path_S + path_T   
 
        bottleneck = min(residual(full_path[i], full_path[i + 1]) for i in range(len(full_path) - 1))

        orphans = set()

        # checking for orphans (main condition - residual is 0)
        for i in range(len(full_path) - 1):
            
            u, v = full_path[i], full_path[i + 1]
            flow[(u, v)] += bottleneck

            if residual(u, v) == 0:
                if tree[u] == "S" and tree[v] == "S" and parent[v] == u:
                    parent[v] = None
                    orphans.add(v)
                elif tree[u] == "T" and tree[v] == "T" and parent[u] == v:
                    parent[u] = None
                    orphans.add(u)
 
        return bottleneck, orphans
    

    def adopt(orphans): # orphans given in a set, but used as a list

        orp_queue = deque(orphans)

        while orp_queue:
            orp = orp_queue.popleft() # why not popleft()
            orp_tree = tree[orp]
            parent_found = False

            for nbr in adj_lst[orp]:

                if tree[nbr] != tree[orp]:
                    continue

            
                if is_in_tree(nbr, orp_tree): 

                    if (residual(nbr, orp) > 0 and orp_tree == "S") or (residual(orp, nbr) > 0 and orp_tree == "T"):
                        parent[orp] = nbr
                        parent_found = True
                        break

            if not parent_found:
                


                for nbr in list(adj_lst[orp]):
                    if tree[nbr] == orp_tree and parent[nbr] == orp:
                        orp_queue.append(nbr)
                        parent[nbr] = None

                    if tree[nbr] != orp_tree and tree[nbr] != "":

                        if (residual(orp, nbr) > 0 and tree[nbr] == "T") or (residual(nbr, orp) > 0 and tree[nbr] == "S"):
                            if nbr not in active_set:
                                active.append(nbr)
                                active_set.add(nbr)
                tree[orp] = ""
                active_set.discard(orp)
                parent.pop(orp, None)


    while True:

        node_S, node_T = None, None # (node_S, node_T) will be the edge between the trees

        #Growth stage
        while active:
            
            curr = active[0]

            if tree[curr] == "":
                active.popleft()
                active_set.discard(curr)
                continue

            found = False

            for q in adj_lst[curr]:
                if (residual(curr, q) > 0 and tree[curr] == "S") or (residual(q, curr) > 0 and tree[curr] == "T") :
                    if tree[q] == "":
                        tree[q] = tree[curr]
                        parent[q] = curr
                        if q not in active_set:
                            active_set.add(q)
                            active.append(q)
                    elif tree[q] != tree[curr]:
                        node_S, node_T = (curr, q) if tree[curr] == "S" else (q, curr)
                        found = True 
                        break
                    
            if found:
                break

            active.popleft()
            active_set.discard(curr)


        if node_S is None:
            break

        bottleneck, orphans = augment(node_S, node_T)
        max_flow += bottleneck  

        adopt(orphans)

        if s not in active_set:
            active.append(s); active_set.add(s)
        if t not in active_set:
            active.append(t); active_set.add(t)

    visited = {s}
    queue = deque([s])
    while queue:
        u = queue.popleft()
        for v in adj_lst[u]:
            if v not in visited and residual(u, v) > 0:
                visited.add(v)
                queue.append(v)

    S = visited - {'s', 't'}
    T = set(adj_lst.keys()) - visited - {'s', 't'}

    return max_flow, flow, S, T



 
if __name__ == "__main__":
    tests = [
        # (graph, s, t, expected_max_flow, description)
        ({(0, 1): 10, (1, 2): 5},                                     0,   2, 5,  "simple chain, bottleneck at end"),
        ({(0, 1): 3,  (1, 2): 10},                                    0,   2, 3,  "simple chain, bottleneck at start"),
        ({(0, 1): 10, (1, 3): 10, (0, 2): 10, (2, 3): 10},           0,   3, 20, "two parallel paths"),
        ({("s","a"):10,("s","b"):10,("a","b"):2,("a","t"):10,("b","t"):10}, "s","t", 20, "classic textbook graph"),
        ({(0, 1): 5,  (2, 3): 5},                                     0,   3, 0,  "disconnected graph"),
    ]
 
    all_pass = True
    for graph, s, t, expected, desc in tests:
        max_flow, flow, S, T = boykov_kolmogorov(graph, s, t)
        status = "PASS" if max_flow == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"[{status}] {desc}: got {max_flow}, expected {expected}")
 
    print("\nAll tests passed!" if all_pass else "\nSome tests FAILED.")