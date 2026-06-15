from collections import defaultdict, deque

def boykov_kolmogorov(graph, s, t):

    # Storing the neighbours of the node
    adj_lst = defaultdict(list) #{ node : [neighbours]}
    capacities = dict(graph) # original capacities

    # filling the adjacency list
    for (u,v) in graph:
        adj_lst[u].append(v)
        adj_lst[v].append(u)

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


            # checking if it is an orphan
            if residual(u, v) == 0:
                if tree[u] == "S" and tree[v] == "S" and parent[v] == u:
                    parent[v] = None
                    orphans.add(v)
                elif tree[u] == "T" and tree[v] == "T" and parent[u] == v:
                    parent[u] = None
                    orphans.add(u)
 
        return bottleneck, orphans
    

    def adopt(orphans): 
        # FIFO for orphans
        orp_queue = deque(orphans)

        while orp_queue:
            orp = orp_queue.popleft() 
            orp_tree = tree[orp]
            parent_found = False

            # checking for possible parents
            for nbr in adj_lst[orp]:

                # a node cannot have a parent from a different tree
                if tree[nbr] != tree[orp]:
                    continue

                # we check if the possible parent is in that tree because it might be in a forest
                if is_in_tree(nbr, orp_tree): 

                    # if the residual > 0 and based on the type of the tree we assign it 
                    if (residual(nbr, orp) > 0 and orp_tree == "S") or (residual(orp, nbr) > 0 and orp_tree == "T"):
                        parent[orp] = nbr
                        parent_found = True
                        break


            # if we do not find a parent, we set the orp to be a free node and its children become orphans
            if not parent_found:
                

                for nbr in adj_lst[orp]:
                    # check if orp is the parent of nbr
                    if tree[nbr] == orp_tree and parent[nbr] == orp:
                        orp_queue.append(nbr)
                        parent[nbr] = None

                    if tree[nbr] != orp_tree and tree[nbr] != "":
                        
                        # if the child is of different tree type, it does not become an orphan as it is connected to a root
                        if (residual(orp, nbr) > 0 and tree[nbr] == "T") or (residual(nbr, orp) > 0 and tree[nbr] == "S"):
                            # hence it still may have unexplored neighbors, so we keep it in an active set
                            if nbr not in active_set:
                                active.append(nbr)
                                active_set.add(nbr)

                # at last, we set the node free
                tree[orp] = ""
                active_set.discard(orp)
                parent.pop(orp, None)


    while True:

        node_S, node_T = None, None # (node_S, node_T) will be the edge between the S and T trees

        #Growth stage (while active nodes exist)
        while active:
            
            curr = active[0]

            if tree[curr] == "": # a tree without its tree cannot be active
                active.popleft()
                active_set.discard(curr)
                continue

            found = False

            # we assign a tree type based on the residual and the type of curr
            for q in adj_lst[curr]:
                if (residual(curr, q) > 0 and tree[curr] == "S") or (residual(q, curr) > 0 and tree[curr] == "T") :
                    if tree[q] == "":
                        tree[q] = tree[curr]
                        parent[q] = curr
                        if q not in active_set:
                            active_set.add(q)
                            active.append(q)
                    # if the tree types differ, it means we found an egde between two trees
                    elif tree[q] != tree[curr]:
                        node_S, node_T = (curr, q) if tree[curr] == "S" else (q, curr)
                        found = True 
                        break
                    
            if found:
                break

            # if we did not find anything, it means the node is fully explored and it becomes passive
            active.popleft()
            active_set.discard(curr)

        # Test if we found a path
        if node_S is None:
            break

        # if we found a path, we find the bottleneck and the orphans after incrementing the flow
        bottleneck, orphans = augment(node_S, node_T)
        max_flow += bottleneck  

        # adopting orphans
        adopt(orphans)

        if s not in active_set:
            active.append(s); active_set.add(s)
        if t not in active_set:
            active.append(t); active_set.add(t)

    # find the first part of the min-cut from the source with BFS
    visited = {s}
    queue = deque([s])
    while queue:
        u = queue.popleft()
        for v in adj_lst[u]:
            if v not in visited and residual(u, v) > 0:
                visited.add(v)
                queue.append(v)

    S = visited - {'s', 't'}
    T = set(adj_lst.keys()) - visited - {'s', 't'} # Find the other cut by subtracting the other cut

    return max_flow, flow, S, T


