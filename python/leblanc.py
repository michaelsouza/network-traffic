import numpy as np
import pandas as pd
import networkx as nx
import heapq
from scipy.optimize import minimize_scalar
import time
import multiprocessing


def dijkstra(G, s):
    dist = {} # dist to each node
    pred = {} # predecessors
    done = {} # already visited

    # initialization
    for v in G:
        dist[v] = np.inf
        pred[v] = 0
        done[v] = False

    h = []
    dist[s] = 0
    pred[s] = s
    heapq.heappush(h, (0,s))
    while(len(h) > 0):
        (dist_sv, v) = heapq.heappop(h)
        if done[v]: continue
        for u in G.neighbors_iter(v):
            dist_svu = dist_sv + G[v][u]['weight']
            if dist_svu < dist[u]:
                dist[u] = dist_svu
                pred[u] = v
                heapq.heappush(h, (dist_svu, u))
        done[v] = True

    return dist, pred


class MatOD:
    def __init__(self, o, d, flow):
        self.o = o
        self.d = d
        self.flow = flow


def load_data(problem):
    if problem in {'smallA','smallB','dial'}:
        fid_nodes = '../instances/' + problem + '_nodes.txt'
        fid_edges = '../instances/' + problem + '_edges.txt'
        fid_matod = '../instances/' + problem + '_od.txt'
    else:
        wdir = "C:\\Users\\Michael\\Dropbox\\work.network\\code\\matlab\\instances\\mit_data\\instances\\"
        fid_nodes = wdir + '%s_nodes_algbformat.txt' % problem
        fid_edges = wdir + '%s_selfishflows_0_10.txt' % problem
        fid_matod = wdir + '%s_interod_0_1.txt' % problem
    
    print('Reading nodes')
    nodes = pd.read_csv(fid_nodes, sep=' ')
    # print(nodes)

    print('Reading edges')
    edges = pd.read_csv(fid_edges, sep=' ')
    # print(edges)

    print('Reading MatOD')
    matod = pd.read_csv(fid_matod, sep=' ')
    
    # removing nodes without edges
    print('Cleaning MatOD matrix')
    print('    Creating edge map') 
    max_s = np.max(edges.s)
    max_t = np.max(edges.t)
    max_o = np.max(matod.o)
    max_d = np.max(matod.d)
    bmap  = np.zeros(1 + max(max_s,max_t,max_d,max_o), dtype=bool)
    bmap[edges.s] = True
    bmap[edges.t] = True
    print('    Setting keep array') 
    keep = bmap[matod.o] & bmap[matod.d]
    print('    Removing edges') 
    matod_o    = matod[keep].o.values
    matod_d    = matod[keep].d.values
    matod_flow = matod[keep].flow.values
    removed_edges = len(matod) - len(matod_o)
    removed_flows = sum(matod.flow) - sum(matod_flow)
    print('    Original number of edges ..: %3.2E' % len(matod))
    print('    Number of removed edges ...: %3.2E (%f)' % (removed_edges, removed_edges/len(matod)))
    print('    Total flow of removed edges: %3.2E (%f)' % (removed_flows, removed_flows/sum(matod.flow)))
    matod = MatOD(matod_o, matod_d, matod_flow)
    print('    Final number of edges .....: %3.2E' % len(matod.o))

    return nodes, edges, matod


def bpr(ftt, cap, x, grad=False):
    y = (x / cap)**4
    C = (ftt * x) * (1 + 0.03 * y)
    f = np.sum(C)
    if grad:
        g = ftt * (1 + 0.15 * y)
        return f, g
    else:
        return f


def shortestpaths(G, D, verbose=False):
    if verbose: 
        print('G =')
        for e in G.edges_iter(data=True):
            print('   ', e)
    y = np.zeros(G.graph['nedges'])
    for s in D.graph['sources']:
        dist, pred = dijkstra(G,s)
        if verbose: print('s=%3d : dist ='%s, dist)
        if verbose: print('        pred ='%s, pred)
        for t in D.neighbors_iter(s):
            vol = D[s][t]['vol']
            if dist[t] == np.inf: raise Exception('NonreachableNode: (%d,%d)' % (s,t));
            k = t
            while k != s :
                eij     = G[pred[k]][k]['eij']
                y[eij] += vol
                k       = pred[k]
    if verbose: 
        for e in G.edges_iter():
            eij = G.get_edge_data(*e)['eij']
            print('(%3d,%3d): %f'%(e[0],e[1],y[eij]))
    return y


def check_optimality(G, D, edges, x, verbose=False):
    # update cost
    f, g = bpr(edges.ftt, edges.cap, x, grad=True)
    for k in range(len(x)):
        G.add_edge(edges.s[k], edges.t[k], eij=k, weight=g[k])

    # cost per path
    cost_per_path = 0.0
    for s in D.graph['sources']:
        dist,pred = dijkstra(G,s)
        if verbose: print('s=%3d : dist ='%s, dist)
        if verbose: print('        pred ='%s, pred)
        for t in D.neighbors_iter(s):
            vol = D[s][t]['vol']
            cost_per_path += dist[t] * vol
    # cost per edge
    cost_per_edge = np.sum(g * x)
    # optimality gap
    gap = 1 - cost_per_path / cost_per_edge
    print('Optimality analysis: ')
    print('   Cost per path: %E'% cost_per_path)
    print('   Cost per edge: %E'% cost_per_edge)
    print('   Gap .........: %E'% gap)


def leblanc(problem,verbose=False):
    nodes, edges, matod = load_data(problem)
    nedges = len(edges.s)

    # Network graph
    print('Creating network graph')
    G = nx.DiGraph(nedges=nedges)
    for k in range(nedges):
        G.add_edge(edges.s[k], edges.t[k], eij=k, weight=edges.ftt[k])
    cap = edges.cap
    ftt = edges.ftt

    # Graph of demand
    print('Creating demand graph')
    D = nx.DiGraph(sources=np.unique(matod.o))
    for k in range(len(matod.o)):
        D.add_edge(matod.o[k], matod.d[k], vol=matod.flow[k])

    if verbose: 
        print('G (nedges = %d)'% nedges)
        for e in G.edges_iter(data=True):
            print('   ', e)

    # init x
    tic = time.time()
    # x = shortestpaths(G,D)
    x = shortestpath_parallel(G,D)
    print('Elapsed time during initialization %.3f seconds' % (time.time() - tic))


    tic = time.time()
    f, g = bpr(ftt, cap, x, grad=True)
    print('fobj(x_start) = %.8E calculated in %3.2f seconds' % (f, time.time() - tic))

    if len(x) > 0: 
	    return
    
    xtol  = 0.01
    niter = 0
    done  = False
    maxit = 100
    tstart = time.time()
    while not done:
        tic = time.time()
        # update cost
        f, g = bpr(ftt, cap, x, grad=True)
        for k in range(len(x)):
            G.add_edge(edges.s[k], edges.t[k], eij=k, weight=g[k])

        # update y
        # y = shortestpaths(G,D)
        y = shortestpath_parallel(G,D)
		
        # solve line search problem
        d = y - x
        fobj = lambda a: bpr(ftt, cap, x + a * d)
        if verbose: print('fobj(0) = %E, fobj(1) = %E' % (fobj(0),fobj(1)))
        asol = minimize_scalar(fobj,bracket=(0,1),bounds=(0,1),method='Bounded')
        a = asol.x
        if a < 0 or a > 1: raise Exception('InviableSolution: a=%f' % a)
        y = x + a * d

        # stop criterion
        dx     = np.max(np.abs(x-y)/(np.abs(x)+1))
        df     = (f - asol.fun)/f
        niter += 1
        done = dx < xtol or niter == maxit or df < 1E-4

        # update x
        x = y

        if niter % 20 == 1:
            print('\n  niter    step size     alpha        fobj         df     itime(sec)')
            print('---------------------------------------------------------------------')
        print(' %5d     %5.3E    %5.3E   %5.3E   %5.3E    %.3f' % (niter, dx, a, asol.fun, df, time.time()-tic))
    print('\nTotal elapsed time %.3f hours' % ((time.time() - tstart)/3600))

    # check optimality
    check_optimality(G, D, edges, x)

    # save solution
    print('Saving solution')
    table = pd.DataFrame({'eij':edges.gid, 's':edges.s, 't':edges.t, 'cap':edges.cap, 'ftt':edges.ftt, 'vols':x})
    table.to_csv('sol_%s.csv'%problem,index=False)

class dijkstra_task:
    def __init__(self, G, D, sources):
        self.G = G
        self.D = D
        self.sources = sources

		
def dijkstra_worker(task):
    y = np.zeros(task.G.graph['nedges'])
    for s in task.sources:
        dist, pred = dijkstra(task.G, s)
        for t in task.D.neighbors_iter(s):
            vol = task.D[s][t]['vol']
            if dist[t] == np.inf: raise Exception('NonreachableNode: (%d,%d)' % (s, t));
            k = t
            while k != s:
                eij = task.G[pred[k]][k]['eij']
                y[eij] += vol
                k = pred[k]
    return y


def shortestpath_parallel(G,D):
    pool_size = 4 # number of workers
    tasks = []
    sources = D.graph['sources']
    num_sources = len(sources) / pool_size
    for k in range(pool_size):
        if k < (pool_size - 1):
            s = sources[int(k * num_sources):int((k+1) * num_sources)]
        else:
            s = sources[int(k * num_sources):]
        tasks.append(dijkstra_task(G, D, s))
    pool = multiprocessing.Pool()
    sols = pool.map(dijkstra_worker, tasks)
    y = np.zeros(G.graph['nedges'])
    for k in range(len(sols)):
        y += sols[k]
    return y

if __name__ == '__main__':
    leblanc("porto")