import numpy as np
import heapq
import pandas as pd
from scipy.sparse import csr_matrix

def dijkstra(G, i):
    assert isinstance(G, dict)
    d = {}; p = {}; v = {}
    for j in G.keys():
        d[j] = np.inf # d[i] = distance to node i
        p[j] = 0      # p[i] = predecessor of node i
        v[j] = False  # v[i] is True if node is already visited False otherwise

    # init
    h = []
    heapq.heappush(h, (0, i))
    d[i] = 0
    p[i] = i
    while len(h) > 0:
        (dij, j) = heapq.heappop(h)
        print 'j = %2d, dij = %4.2lf' % (j, dij)
        if v[j] : continue
        for k in G[j]:
            dijk = dij + G[j][k]
            if dijk < d[k]:
                print '   k = %2d, dijk = %4.2lf' % (k, dijk)
                d[k] = dijk
                p[k] = j
                heapq.heappush(h, (dijk, k))
        v[j] = True
    return d, p

def dijkstra_path(i, j, p):
    print(p)
    s = [j]
    while(p[j] is not i):
        s.append(p[j])
        j = p[j]
    s.append(i)
    return s


def ita(edges, matod, cost, fracs=[.7,.1,.1,.1]):
    print('ITA')
    assert isinstance(edges, pd.DataFrame)
    print('   Creating dictionaries')
    T = {} # time
    K = {} # capacity
    V = {} # volumes
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

    fracs = np.array(fracs)

    for f in fracs:
        for index, row in matod.iterrows():
            print 'o: %d, d:%d' % (row.o, row.d)
            vol = row.vol * f

            # find shortest path
            c, p = dijkstra(C, row.o) # cost and predecessors
            raise Exception('NotImplemented')
            print dijkstra_path(row.o, row.d, p)
            # update volumes and costs
            j = row.d
            while p[j] is not row.o:
                i = p[j]
                print 'Updating edge (%2d,%2d)' % (i, j)
                V[i][j] += vol
                C[i][j] = cost(V[i][j], T[i][j], K[i][j])
                j = p[j]


def __test_dial():
    # load instance defined in Dial2006
    edges = pd.read_csv('../instances/dial_edges.txt', sep=' ')
    matod = pd.read_csv('../instances/dial_od.txt', sep=' ')

    # cost function from Dial2006
    cost = lambda xij, tij, kij: tij * (1 + 0.15 * (xij/kij)**4)

    ita(edges, matod, cost)

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