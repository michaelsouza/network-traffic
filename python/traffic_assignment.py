import numpy as np
import heapq
import pandas as pd
import matplotlib.pyplot as plt
import queue

def load_matod(filename):
    # read matod
    table = pd.read_csv(filename, sep=' ')
    matod = {}
    for index, row in table.iterrows():
        if (not matod.has_key(row.o)):
            matod[row.o] = {}
        if (not matod[row.o].has_key(row.d)):
            matod[row.o][row.d] = row.vol
        else:
            raise Exception('Duplicated entry')
    return matod


def dijkstra_multipath(G, i, dtol=0.0001, verbose=False):
    """

    :type dtol: float
    :type verbose: bool
    """
    assert isinstance(G, dict)
    di = {}
    pred = {}
    visited = {}
    for j in G.keys():
        di[j]      = 1E+20   # d[i] = distance to node i
        pred[j]    = {}      # p[i] = predecessors of node i
        visited[j] = False   # v[i] is True if node is already visited False otherwise

    # init
    h = []
    heapq.heappush(h, (0, i))
    di[i] = 0.0
    pred[i][i] = (i, 0)
    while len(h) > 0:
        # print 'h = ', h
        (dij, j) = heapq.heappop(h)
        if verbose: print('i = %2d, j = %2d, dij = %4.2lf' % (i, j, dij))
        # print 'visited[j] = ', visited[j]
        if visited[j]: continue
        # print 'G[j] = ', G[j]
        for k in G[j]:
            dijk = dij + G[j][k]
            # update shortest path
            if dijk < di[k]:
                if verbose: print('   update k = %2d, dijk = %4.2lf' % (k, dijk))
                di[k] = float(dijk)
                # remove not equivalent paths
                preds2remove = [];
                for z in pred[k].keys():
                    (z, dizk) = pred[k][z]
                    if (abs(dizk - dijk) / dijk) > dtol:
                        preds2remove.append(z)
                for z in preds2remove:
                    if verbose: print('      remove (%2d, %2d) = %4.2lf' %(z, k, dizk))
                    pred[k].pop(z)
                # update
                pred[k][j] = (j, dijk)
                heapq.heappush(h, (dijk, k))
            # add equivalent path
            elif (abs(dijk - di[k]) / max(di[k], 1.0)) < dtol:
                if verbose: print('   add   k = %2d, dik = %4.2lf, dijk = %4.2lf' % (k, di[k], dijk))
                pred[k][j] = (j, dijk)
                heapq.heappush(h, (dijk, k))

        visited[j] = True
    return di, pred


def dijkstra(G, i, verbose=False):
    assert isinstance(G, dict)
    di = {}
    pred = {}
    visited = {}

    # init di and pred
    for j in G.keys():
        if not di.has_key(j):
            di[j] = 1E+20  # d[i] = distance to node i
            pred[j] = 0  # p[i] = predecessor of node i
            visited[j] = False  # v[i] is True if node is already visited False otherwise
        for k in G[j].keys():
            if not di.has_key(k):
                di[k] = np.inf  # d[i] = distance to node i
                pred[k] = 0  # p[i] = predecessor of node i
                visited[k] = False  # v[i] is True if node is already visited False otherwise

    # init
    h = []
    heapq.heappush(h, (0, i))
    di[i] = 0
    pred[i] = i
    while len(h) > 0:
        (dij, j) = heapq.heappop(h)
        if verbose: print('j = %2d, dij = %4.2lf' % (j, dij))
        if visited[j]: continue
        for k in G[j]:
            dijk = dij + G[j][k]
            if dijk < di[k]:
                if verbose: print('   k = %2d, dijk = %4.2lf' % (k, dijk))
                di[k] = dijk
                pred[k] = j
                heapq.heappush(h, (dijk, k))
        visited[j] = True
    return di, pred


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
        fracs = [0.7, .1, .1, .1]

    if sum(fracs) < 0.99:
        raise Exception('The input sum(fracs) must be equal to one.')

    assert isinstance(edges, pd.DataFrame)

    if verbose: print('ITA')
    if verbose: print('   Creating data structures')
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
            C[i][j] = T[i][j]

    assert isinstance(matod, dict)
    if verbose: print('   Finding shortest paths')
    iter = 0
    for f in fracs:
        for i in matod.keys():
            if verbose: print('Find paths from node %d' % i)
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

    if verbose: traffic_assignment_quality(matod, V, C)

    return V, C


def ita_multipath(edges, matod, cost, fracs=None, verbose=False):
    if fracs is None:
        fracs = [.4,.3,.2,.1]

    if sum(fracs) < 0.99:
        raise Exception('The input sum(fracs) must be equal to one.')

    assert isinstance(edges, pd.DataFrame)

    if verbose: print('ITA + MULTIPATH')
    if verbose: print('   Creating data structures')
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
            C[i][j] = T[i][j]

    assert isinstance(matod, dict)
    if verbose: print('   Finding shortest paths')
    iter = 0
    for f in fracs:
        for i in matod.keys():
            if verbose: print('Find paths from node %d' % i)
            # find shortest path from i to all nodes
            c, p = dijkstra_multipath(C, i, verbose=True) # cost and predecessors

            # update volumes
            q = []
            for j in matod[i].keys():
                #todo calculate the number of alternative paths for a specific od pair
                heapq.heappush(q, (matod[i][j] * f, j))
                while len(q) > 0:
                    (vj, ej) = heapq.heappop(q)
                    dv = vj / len(p[ej])
                    # volume divided by the number of alternative paths
                    for ei in p[ej].keys(): # predecessors
                        # update volume
                        V[ei][ej] += dv
                        if ei is not i:
                            heapq.heappush(q, (dv, ei))

        # update costs
        for i in V.keys():
            for j in V[i].keys():
                C[i][j] = cost(V[i][j], T[i][j], K[i][j])

        # view V and C
        if verbose: print_dict(V, 'Vols iter %d' % iter)
        if verbose: print_dict(C, 'Cost iter %d' % iter)
        iter += 1

    if verbose: traffic_assignment_quality(matod, V, C, verbose)
    return V, C


def traffic_assignment_quality(matod, V, C, verbose=False):
    assert isinstance(matod, dict)
    assert isinstance(V, dict)
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
    if verbose: print('Traffic assignment quality')
    if verbose: print('   Total path cost %g' % total_path_cost)
    if verbose: print('   Total edge cost %g' % total_edge_cost)
    if verbose: print('   Accuracy        %g' % quality)

    return quality


def print_dict(V, label):
    print(label)
    assert isinstance(V, dict)
    for i in V.keys():
        for j in V[i].keys():
            if V[i][j] > 0: print('   i = %2d, j = %2d value = %g' % (i, j, V[i][j]))


def __test_dial__():
    # load instance
    edges = pd.read_csv('../instances/dial_edges.txt', sep=' ')
    # load matod
    matod = load_matod('../instances/dial_od.txt')
    # cost function from Dial2006
    cost = lambda xij, tij, kij: tij * (1 + 0.15 * (xij / kij) ** 4)
    V, C = ita_multipath(edges, matod, cost)
    # V, C = ita(edges, matod, cost)
    traffic_assignment_quality(matod, V, C, verbose=True)


def __test_ita__():
    # load instance
    edges = pd.read_csv('../instances/smallA_edges.txt', sep=' ')
    # load matod
    matod = load_matod('../instances/smallA_od.txt')
    # cost function
    # cost = lambda xij, tij, kij: tij + (xij / kij)
    cost = lambda xij, tij, kij: tij * (1 + 0.15 * (xij / kij) ** 4)

    V, C = ita(edges, matod, cost, fracs=[0.1,.1,.8], verbose=True)
    traffic_assignment_quality(matod, V, C, verbose=True)

    V, C = ita_multipath(edges, matod, cost, fracs=[0.1,.1,.8], verbose=True)
    traffic_assignment_quality(matod, V, C, verbose=True)

    # print edges
    # print 'matod = ', matod
    # print_dict(V, 'Edges volume -------------')
    # print_dict(C, 'Edges cost ---------------')


def __test_ita_convergence__():
    # load instance
    edges = pd.read_csv('../instances/dial_edges.txt', sep=' ')
    # load matod
    matod = load_matod('../instances/dial_od.txt')
    # cost function
    # cost = lambda xij, tij, kij: tij + (xij / kij)
    cost = lambda xij, tij, kij: tij * (1 + 0.15 * (xij / kij) ** 4)
    # print edges
    # print 'matod = ', matod
    # print_dict(V, 'Edges volume -------------')
    # print_dict(C, 'Edges cost ---------------')
    quality = {}
    for i in range(2,20):
        # V, C = ita(edges, matod, cost, fracs=np.ones(i + 1)/(i + 1))
        V, C = ita_multipath(edges, matod, cost, fracs=np.ones(i + 1) / (i + 1), verbose=False)
        quality[i + 1] = traffic_assignment_quality(matod, V, C)

    plt.close('all')
    plt.plot(quality.keys(), quality.values())
    plt.xlabel('Number of packages')
    plt.ylabel('Accuracy')
    plt.title('ITA+MULTIPATH')
    plt.show()


def __test_dijkstra__():
    G = {0: {1: 2, 3: 1},
         1: {0: 2, 2: 1, 3: 1, 4: 2},
         2: {1: 1, 4: 2, 5: 5},
         3: {0: 1, 1: 1, 4: 3},
         4: {1: 2, 2: 2, 3: 3, 5: 2},
         5: {4: 2, 2: 5}}

    d, p = dijkstra(G, 0)
    print(d, p)


def __test_dijkstra_multipath__():
    # load instance
    # edges = pd.read_csv('../instances/smallA_edges.txt', sep=' ')
    edges = pd.read_csv('../instances/dial_edges.txt', sep=' ')

    # convert edges to graph
    G = {}
    for index, row in edges.iterrows():
        if row.o not in G.keys():
            G[row.o] = {}
        G[row.o][row.d] = row.ftt
    #print G

    d, p = dijkstra_multipath(G, 1, verbose=True)
    print('d = ', d)
    print('p = ', p)

    for i in p.keys():
        print('%i ' % i)
        for j in p[i]:
            print('   %i' % j)


if __name__ == '__main__':
    # __test_dial__()
    __test_dijkstra_multipath__()
    # __test_ita__()
    # __test_ita_convergence__()