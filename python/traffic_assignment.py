import numpy as np
import heapq
import pandas as pd

def load_matod(filename):
    # read matod
    table = pd.read_csv(filename, sep=' ')
    matod = {}
    for index, row in table.iterrows():
        if (not matod.has_key(row.o)):
            matod[row.o] = {}
        if (not matod[row.o].has_key(row.o)):
            matod[row.o][row.d] = row.vol
        else:
            matod[row.o][row.d] += row.vol
    return matod


def dijkstra(G, i, verbose=False):
    assert isinstance(G, dict)
    d = {}
    p = {}
    v = {}
    for j in G.keys():
        d[j] = np.inf  # d[i] = distance to node i
        p[j] = 0  # p[i] = predecessor of node i
        v[j] = False  # v[i] is True if node is already visited False otherwise

    # init
    h = []
    heapq.heappush(h, (0, i))
    d[i] = 0
    p[i] = i
    while len(h) > 0:
        (dij, j) = heapq.heappop(h)
        if verbose: print 'j = %2d, dij = %4.2lf' % (j, dij)
        if v[j]: continue
        for k in G[j]:
            dijk = dij + G[j][k]
            if dijk < d[k]:
                if verbose: print '   k = %2d, dijk = %4.2lf' % (k, dijk)
                d[k] = dijk
                p[k] = j
                heapq.heappush(h, (dijk, k))
        v[j] = True
    return d, p


def dijkstra_path(i, j, p):
    s = [j]
    while True:
        j = p[j]
        s.append(j)
        # origin (i) has been found
        if j == i: break
    s.reverse()
    print(s)
    return s


def ita(edges, matod, cost, fracs=None):
    if fracs is None:
        fracs = np.linspace(0, 1)

    print 'ITA'
    assert isinstance(edges, pd.DataFrame)
    print '   Creating data structures'
    T = {}  # time
    K = {}  # capacity
    V = {}  # volumes
    for index, row in edges.iterrows():
        i = int(row.o)
        j = int(row.d)
        if i not in T.keys():
            T[i] = {}
            K[i] = {}
            V[i] = {}
        if j not in T[i]:
            T[i][j] = row.ftt
            K[i][j] = row.capacity
            V[i][j] = 0
    C = T.copy() # init costs (free travel time)

    print '   Finding shortest paths'
    assert isinstance(matod, dict)
    for f in fracs:
        for i in matod.keys():
            # find shortest path from i to all nodes
            c, p = dijkstra(C, i) # cost and predecessors

            # update volumes
            for j in matod[i].keys():
                ej = j # edge end node
                while True:
                    ei = p[ej] # edge begin node
                    # update volume
                    V[ei][ej] += matod[i][j] * f
                    # path origin has been found
                    if ei == i: break
                    ej = ei

        # update costs
        for i in V.keys():
            for j in V[i].keys():
                C[i][j] = cost(V[i][j], T[i][j], K[i][j])

    traffic_assignment_quality(matod, V, C)
    return V, C


def traffic_assignment_quality(matod, V, C):
    assert isinstance(matod, dict)
    assert isinstance(C, dict)

    total_path_cost = 0
    for i in matod.keys():
        # cost and predecessors
        c, p = dijkstra(C, i)
        # update total path cost
        for j in matod[i].keys():
            ej = j
            while True:
                ei = p[ej]
                total_path_cost += C[ei][ej] * V[ei][ej]
                # path origin has been found
                if ei == i: break
                ej = ei

    total_edge_cost = 0
    for i in C.keys():
        for j in C[i].keys():
            total_edge_cost += C[i][j] * V[i][j]

    print ''
    print 'Traffic assignment quality'
    print '   Total edge cost %g' % total_edge_cost
    print '   Total path cost %g' % total_path_cost
    print '   Accuracy        %g' % (total_path_cost/total_edge_cost)
def __test_dial__():
    # load instance
    edges = pd.read_csv('../instances/dial_edges.txt', sep=' ')
    # load matod
    matod = load_matod('../instances/dial_od.txt')
    # cost function from Dial2006
    cost = lambda xij, tij, kij: tij * (1 + 0.15 * (xij / kij) ** 4)
    ita(edges, matod, cost)

def print_dict(V, label):
    print label
    assert isinstance(V, dict)
    for i in V.keys():
        for j in V[i].keys():
            print '   i = %2d, j = %2d value = %g' % (i, j, V[i][j])

def __test_smallA__():
    # load instance
    edges = pd.read_csv('../instances/smallA_edges.txt', sep=' ')
    # load matod
    matod = load_matod('../instances/smallA_od.txt')
    # cost function
    cost = lambda xij, tij, kij: tij + (xij / kij)
    V, C = ita(edges, matod, cost)
    # print edges
    # print 'matod = ', matod
    print_dict(V, 'Edges volume -------------')
    print_dict(C, 'Edges cost ---------------')

def __test_dijkstra__():
    G = {0: {1: 2, 3: 1},
         1: {0: 2, 2: 1, 3: 1, 4: 2},
         2: {1: 1, 4: 2, 5: 5},
         3: {0: 1, 1: 1, 4: 3},
         4: {1: 2, 2: 2, 3: 3, 5: 2},
         5: {4: 2, 2: 5}}

    d, p = dijkstra(G, 0)
    print d, p


if __name__ == '__main__':
    # __test_dial__()
    __test_smallA__()