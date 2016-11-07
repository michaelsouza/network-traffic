import numpy as np
import pandas as pd
import networkx as nx
import heapq
from scipy.optimize import minimize_scalar
import time
import multiprocessing
from contextlib import closing
import os
import os.path
import sys

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
        fid_xsol = 'sol_dial.csv'
    
    #ToDo: Code to split the porto_R and identify alpha(A), max_distance(D)
    
    if problem in ['porto', 'lisbon', 'rio', 'boston', 'sfbay']:
        wdir = "../instances/"
        fid_edges = wdir + '%s_edges_algbformat.txt' % problem
        fid_nodes = wdir + '%s_nodes_algbformat.txt' % problem
        fid_matod = wdir + '%s_interod_0_1.txt' % problem 
        fid_xsol = None
        # fid_edges = wdir + '%s_selfishflows_0_10.txt' % problem
        # fid_edges = 'sol_porto_0_btwall_01.csv'
        # fid_edges = wdir + 'results\\%s_selfishflows_0_btwall_01.txt' % problem
        # fid_edges = 'sol_porto_0_10.csv' % problem # already solved
        
    if 'porto_R' in problem:
        wdir = "../instances/"
        fid_nodes = wdir + 'porto_nodes_algbformat.txt'
        fid_matod = wdir + 'porto_interod_0_1.txt'
        fid_edges = wdir + '%s.csv' % problem
        # set initial solution file
        if '_D050' in problem:
            fid_xsol = 'sol_porto.csv'
        elif '_D100' in problem:
            fid_xsol = 'sol_' + problem.replace('_D100', '_D050') + '.csv'
        elif '_D250' in problem:
            fid_xsol = 'sol_' + problem.replace('_D250', '_D100') + '.csv'
        elif '_D500' in problem:
            fid_xsol = 'sol_' + problem.replace('_D500', '_D250') + '.csv'
    
    print('Reading nodes')
    print('   %s' % fid_nodes)
    nodes = pd.read_csv(fid_nodes, sep=' ')
    # print(nodes)

    print('Reading edges')
    print('   %s' % fid_edges)
    edges = pd.read_csv(fid_edges, sep=' ')
    
    print('Reading solution')
    x = None
    if fid_xsol is not None:
        print('   %s' % fid_xsol)
        print('Setting user-defined initial point')
        if fid_xsol is not fid_edges:
            print('   WARNING: Initial solution is given from different file')
        xsol = pd.read_csv(fid_xsol)
        x = xsol.vol

    print('Reading MatOD')
    print('   %s' % fid_matod)
    matod = pd.read_csv(fid_matod, sep=' ')
    
    # removing nodes without edges
    print('Cleaning MatOD matrix')
    print('    Creating edge map') 
    max_s = np.max(edges.source)
    max_t = np.max(edges.target)
    max_o = np.max(matod.o)
    max_d = np.max(matod.d)
    bmap  = np.zeros(1 + max(max_s,max_t,max_d,max_o), dtype=bool)
    bmap[edges.source] = True
    bmap[edges.target] = True
    print('    Setting keep array') 
    keep = bmap[matod.o] & bmap[matod.d]
    print('    Removing unkown edges') 
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

    return nodes, edges, matod, x


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
    nonreachable = []
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
            if dist[t] == np.inf:
                nonreachable.append((s,t))
            k = t
            while k != s :
                eij     = G[pred[k]][k]['eij']
                y[eij] += vol
                k       = pred[k]
    if len(nonreachable) > 0:
        for (s,t) in nonreachable:
            print('   NonreachablePair: (%d,%d)' % (s, t))
        raise Exception('NonreachablePairs');
        
    if verbose: 
        for e in G.edges_iter():
            eij = G.get_edge_data(*e)['eij']
            print('(%3d,%3d): %f'%(e[0],e[1],y[eij]))
    return y


def calculate_costs(G, D, edges, x, verbose=False):
    print('Optimality analysis: ')
    tic = time.time()
    # update cost
    f, g = bpr(edges.cost_time, edges.capacity, x, grad=True)
    for k in range(len(x)):
        G.add_edge(edges.source[k], edges.target[k], eij=k, weight=g[k])

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
    cost_time = g * x
    cost_per_edge = np.sum(cost_time)
    # optimality gap
    gap = 1 - cost_per_path / cost_per_edge
    print('   Cost per path: %E'% cost_per_path)
    print('   Cost per edge: %E'% cost_per_edge)
    print('   Gap .........: %E'% gap)
    print('   Elapsed time during check_optimality %.3f seconds' % (time.time() - tic))
    return cost_time


def leblanc(problem,xinit=None,verbose=False, check=False):
    nodes, edges, matod, x = load_data(problem)
    nedges = len(edges.source)

    # Network graph
    print('Creating network graph')
    G = nx.DiGraph(nedges=nedges)
    for k in range(nedges):
        G.add_edge(edges.source[k], edges.target[k], eij=k, weight=edges.cost_time[k])
    cap = edges.capacity
    ftt = edges.cost_time

    # Graph of demand
    print('Creating demand graph')
    D = nx.DiGraph(sources=np.unique(matod.o))
    for k in range(len(matod.o)):
        D.add_edge(matod.o[k], matod.d[k], vol=matod.flow[k])

    if verbose: 
        print('G (nedges = %d)'% nedges)
        for e in G.edges_iter(data=True):
            print('   ', e)

    if check:
        print('Just checking optimality')
        calculate_costs(G, D, edges, x)
        return
            
    # init x
    tic = time.time()
    if x is None:
        print('Setting all-in initial point')
        x = shortestpaths_parallel(G,D)
    print('Elapsed time during initialization %.3f seconds' % (time.time() - tic))

    tic = time.time()
    f, g = bpr(ftt, cap, x, grad=True)
    print('fobj(x_start) = %.8E calculated in %3.2f seconds' % (f, time.time() - tic))
    
    xtol  = 0.01
    niter = 0
    done  = False
    maxit = 100
    tstart = time.time()
    xsol = pd.DataFrame({'vol':x})
    while not done:
        tic = time.time()
        # update cost
        f, g = bpr(ftt, cap, x, grad=True)
        for k in range(len(x)):
            G.add_edge(edges.source[k], edges.target[k], eij=k, weight=g[k])

        # update y
        # y = shortestpaths(G,D)
        y = shortestpaths_parallel(G,D)
		
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
        
        # save step
        xsol['vol'] = x
        xsol.to_csv('xsol_it_%03d.csv' % niter, index=False)
        
        if niter % 20 == 1:
            print('\n  niter    step size     alpha        fobj         df     itime(sec)')
            print('---------------------------------------------------------------------')
        print(' %5d     %5.3E    %5.3E   %5.3E   %5.3E    %.3f' % (niter, dx, a, asol.fun, df, time.time()-tic))
    print('\nTotal elapsed time %.3f hours' % ((time.time() - tstart)/3600))

    # check optimality
    cost_time = calculate_costs(G, D, edges, x)

    # cleaning temporary solution files
    print('Cleaning temporay files')
    files =  os.listdir('.')
    for file in files:
        if file.startswith('xsol_it_'):
            os.remove(file)
        
    # save solution
    print('Saving solution')
    table = pd.DataFrame({'gid':edges.eid, 's':edges.source, 't':edges.target, 'cap':edges.capacity, 'ftt':edges.cost_time, 'vol':x, 'cost':cost_time})
    table.to_csv('sol_%s.csv'%problem,index=False)

    
class dijkstra_task:
    def __init__(self, G, D, sources):
        self.G = G
        self.D = D
        self.sources = sources
	
	
def dijkstra_worker(task):
    nonreachable = []
    y = np.zeros(task.G.graph['nedges'])
    for s in task.sources:
        dist, pred = dijkstra(task.G, s)
        for t in task.D.neighbors_iter(s):
            vol = task.D[s][t]['vol']
            if dist[t] == np.inf:
                nonreachable.append((s,t))
            k = t
            while k != s:
                eij = task.G[pred[k]][k]['eij']
                y[eij] += vol
                k = pred[k]
    if len(nonreachable) > 0:
        for (s,t) in nonreachable:
            print('NonreachablePair: (%d,%d)' % (s,t))
        raise Exception('NonreachablePairs');
    return y

    
def shortestpaths_parallel(G,D):
    # number of workers
    pool_size = multiprocessing.cpu_count() - 1 
    tasks = []
    sources = D.graph['sources']
    num_sources = len(sources) / pool_size
    for k in range(pool_size):
        if k < (pool_size - 1):
            s = sources[int(k * num_sources):int((k+1) * num_sources)]
        else:
            s = sources[int(k * num_sources):]
        tasks.append(dijkstra_task(G, D, s))
    with closing(multiprocessing.Pool()) as pool:
        sols = pool.map(dijkstra_worker, tasks)
    y = np.zeros(G.graph['nedges'])
    for k in range(len(sols)):
        y += sols[k]
    return y

    
if __name__ == '__main__':
    city = str(sys.argv[1])
    leblanc(city)
    #ToDo: Loop rank (R), alpha (A) and max_distance (D)
    #MAX_DIST = [50, 100, 250, 500]
    #ALPHA = [0.1, 0.2, 0.5, 0.7, 1.0]
    #RANK = ['voc_id', 'btw_id']
    # for alpha in ALPHA:
        # for max_dist in MAX_DIST:
            # for rank in RANK:
                # problem = '%s_R%s_A%3.2f_D%03d' % (city, rank, alpha, max_dist)
                # print('Problem: %s' % problem)
                # if not os.path.isfile('sol_%s.csv' % problem):
                    # leblanc(problem)
                # else:
                    # print('   Already solved')