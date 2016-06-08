import numpy as np
import heapq
import pandas as pd

def dijkstra(G, i, etol=0):
    n = len(G.keys())              # number of nodes
    d = [np.inf for k in range(n)] # d[i] = distance to node i
    p = np.zeros(n, dtype=np.int)  # p[i] = predecessor of node i
    v = np.zeros(n, dtype=np.int8) # v[i] is True if node is already visited False otherwise
    h = []

    # init
    heapq.heappush(h, (0, i))
    d[i] = 0
    p[i] = i
    while len(h) > 0:
        (dij, j) = heapq.heappop(h)
        if v[j] : continue
        for k in G[j]:
            dijk = dij + G[j][k]
            if dijk < d[k]:
                d[k] = dijk
                p[k] = j
                heapq.heappush(h, (dijk, k))
        v[j] = True
    return d, p

def __test_dial():
    # load dial instance
    edges = pd.read_csv('../instances/dial_edges.txt', sep=' ')
    print(edges)

def __test_dijkstra():
    G = {0: {1: 2, 3: 1},
         1: {0: 2, 2: 1, 3: 1, 4: 2},
         2: {1: 1, 4: 2, 5: 5},
         3: {0: 1, 1: 1, 4: 3},
         4: {1: 2, 2: 2, 3: 3, 5: 2},
         5: {4: 2, 2: 5}}

    d, p = dijkstra(G, 0)
    print d, p


if __name__== '__main__':
    __test_dial()