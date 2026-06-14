from collections import defaultdict, deque

def boykov_kolmogorov(graph, s, t):

    # Storing the neighbours of the node
    adj_lst = defaultdict(set) #{ v : ()}, alternative approach { v: {l: 10}, u: {}}
    capacities = dict(graph) #original capacities

 
    for (u,v) in graph:
        adj_lst[u].add(v)
        adj_lst[v].add(u)
        if (v,u) not in capacities:
            capacities[(v,u)] = 0 

    flow = defaultdict(int)

        
    active = deque([s,t])
    active_set = {s, t}

    tree = defaultdict(str) # "S" "T" ""
    parent = {s: None, t: None}

    tree[s] = "S"
    tree[t] = "T"
    max_flow = 0

    def residual(u, v):
        return capacities.get((u,v), 0) - flow[(u,v)] + flow[(v,u)]

    def path_to_root(node):
        path = []
        while node is not None:
            path.append(node)
            node = parent.get(node, None)
        return path

        

    def is_in_tree(node, type):

        curr = node
        while curr is not None:
            if curr == s and type == "S":
                return True
            if curr == t and type == "T":
                return True
            curr = parent.get(curr, None)
        return False

    def augment(node_S, node_T):
        path_S = path_to_root(node_S)
        path_S = path_S[::-1]              # now goes s → … → node_s

        path_T = path_to_root(node_T) # goes node_t → … → t
 
        full_path = path_S + path_T   
 
        bottleneck = min(residual(full_path[i], full_path[i + 1]) for i in range(len(full_path) - 1))

        orphans = set()
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

    return max_flow


 
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
        result = boykov_kolmogorov(graph, s, t)
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"[{status}] {desc}: got {result}, expected {expected}")
 
    print("\nAll tests passed!" if all_pass else "\nSome tests FAILED.")