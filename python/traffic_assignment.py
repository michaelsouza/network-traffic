import numpy as np
import heapq
import pandas as pd
import matplotlib.pyplot as plt

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


def dijkstra_multipath(G, i, verbose=False):
    assert isinstance(G, dict)
    dtol = 0.01
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
        J = []
        D = []
        # find all equivalent paths
        while len(h) > 0:
            (dij, j) = heapq.heappop(h)
            # add alternative node
            if (len(J) == 0) or ((dij - D[0])/D[0] < dtol): 
                J.append(j)
                D.append(dij)
                continue
            # reinsert node j - it's not an equivalent alternative
            heappush(h, (dij, j))
            break

        if verbose: 
            for k in range(len(J)):
                print 'j = %2d, dij = %4.2lf' % (J[k], D[k])
        
        for q in range(len(J)):
            j = J[q]
            # already visited
            if v[j]: continue
            dij = D[q]
            for k in G[j]:
                dijk = dij + G[j][k]
                if dijk < d[k]:
                    if verbose: print '   k = %2d, dijk = %4.2lf' % (k, dijk)
                    d[k] = dijk
                    p[k] = j
                    heapq.heappush(h, (dijk, k))
            v[j] = True
    return d, p

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


def print_dijkstra_path(i, j, p):
    s = [j]
    while True:
        k = p[j]
        s.append(k)
        # origin has been found
        if k == i: break
        j = k
    s.reverse()
    print(s)
    return s


def ita(edges, matod, cost, fracs=None, verbose=False):
    if fracs is None:
        fracs = np.ones(100)/100

    if sum(fracs) < 0.99:
        raise Exception('The input sum(fracs) must be equal to one.')

    assert isinstance(edges, pd.DataFrame)

    # read nodes from edges
    nodes = []

    if verbose: print 'ITA'
    if verbose: print '   Creating data structures'
    T = {}  # time
    K = {}  # capacity
    V = {}  # volumes
    C = {}  # cost
    for index, row in edges.iterrows():
        i = int(row.o)
        j = int(row.d)
        if i not in T.keys():
            T[i] = {}
            K[i] = {}
            V[i] = {}
            C[i] = {}
        if j not in T.keys():
            T[j] = {}
            K[j] = {}
            V[j] = {}
            C[j] = {}
        if j not in T[i]:
            T[i][j] = row.ftt
            K[i][j] = row.capacity
            V[i][j] = 0
            C[i][j] = 0

    assert isinstance(matod, dict)
    if verbose: print '   Finding shortest paths'
    iter = 0
    for f in fracs:
        for i in matod.keys():
            if verbose: print 'Find paths from node %d' % i
            # find shortest path from i to all nodes
            c, p = dijkstra(C, i) # cost and predecessors

            # update volumes
            for j in matod[i].keys():
                if verbose: print_dijkstra_path(i, j, p)
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

        # view V and C
        if verbose: print_dict(V, 'Vols iter %d' % iter)
        if verbose: print_dict(C, 'Cost iter %d' % iter)
        iter += 1

    quality = traffic_assignment_quality(matod, V, C)
    return V, C, quality


def traffic_assignment_quality(matod, V, C, verbose=False):
    assert isinstance(matod, dict)
    assert isinstance(C, dict)

    total_path_cost = 0
    for i in matod.keys():
        # cost and predecessors
        c, p = dijkstra(C, i)
        # update total path cost
        for j in matod[i].keys():
            total_path_cost += matod[i][j] * c[j]

    total_edge_cost = 0
    for i in C.keys():
        for j in C[i].keys():
            total_edge_cost += C[i][j] * V[i][j]

    quality = total_path_cost/total_edge_cost
    if verbose: print 'Traffic assignment quality'
    if verbose: print '   Total path cost %g' % total_path_cost
    if verbose: print '   Total edge cost %g' % total_edge_cost
    if verbose: print '   Accuracy        %g' % quality

    return quality

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


def __test_small__():
    # load instance
    edges = pd.read_csv('../instances/dial_edges.txt', sep=' ')
    # load matod
    matod = load_matod('../instances/dial_od.txt')
    # cost function
    cost = lambda xij, tij, kij: tij + (xij / kij)

    V, C, quality = ita(edges, matod, cost)
    # print edges
    # print 'matod = ', matod
    # print_dict(V, 'Edges volume -------------')
    # print_dict(C, 'Edges cost ---------------')
    quality = {}
    for i in range(2,20):
        V, C, quality[i+1] = ita(edges, matod, cost, fracs=np.ones(i+1)/(i+1), verbose=False)

    plt.close('all')
    plt.plot(quality.keys(), quality.values())
    plt.xlabel('Number of packages')
    plt.ylabel('Accuracy')
    plt.show()


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
    __test_small__()