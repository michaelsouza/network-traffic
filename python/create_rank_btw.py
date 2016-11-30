# -*- coding: utf-8 -*-
"""
Created on Tue Aug 16 16:43:04 2016

@author: souza.michael@gmail.com
"""

import networkx as nx
import numpy as np
from numpy import zeros
import pandas as pd
import os.path
import sys
import time
from time import sleep

def expected_remaining_time(start,iter,total): return ((total - iter) * (time.time() - start) / iter) / 60

def progressbar (iteration, total, prefix = '', suffix = '', decimals = 1, barLength = 100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    formatStr       = "{0:." + str(decimals) + "f}"
    percents        = formatStr.format(100 * (iteration / float(total)))
    filledLength    = int(round(barLength * iteration / float(total)))
    bar             = '█' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')
        sys.stdout.flush()

def calculate_edge_od_betweenness_centrality(OD, G):
	# add all edges
	rank = {edge:0 for edge in G.edges()}
	# set betweenness
	numberOfSkippedODPairs = 0
	ignoredVolume = 0

	count = 0
	tic = time.time()
	nedges = len(OD.flow)
	progressbar(count, nedges, prefix="Working:", suffix="Done", barLength=50)
	for k in range(nedges):

		count+=1
		if(count % 5 == 0): # update progress bar  
			progressbar(count,nedges,prefix='Working:', suffix = 'ETA %3.2f'%(expected_remaining_time(tic,count,nedges)),barLength=50)
	
		i = OD.o[k]
		j = OD.d[k]
		f = OD.flow[k]
		if((G.has_node(i)==False) or (G.has_node(j)==False)): 
			numberOfSkippedODPairs+=1
			ignoredVolume+=f
			continue
			
		# consider to use all_shortest_paths
		# for p in nx.all_shortest_paths(G, i, j, weight='weight'):
		# 	for q in range(len(p) - 1):
		# 		rank[(p[q],p[q+1])] += f
		p = nx.shortest_path(G, i, j, weight='weight')
		for k in range(len(p) - 1):
			rank[(p[k],p[k+1])] += f
				
	print('numberOfSkippedODPairs = ', numberOfSkippedODPairs)
	print('ignoredVolume          =  %f (%f of total volume)' % (ignoredVolume, ignoredVolume/np.sum(OD.flow)))
				
	return rank

def calculate_edge_cluster_index(G):
	
	def havlin_factor(G,eij): 
		eij = G[eij[0]][eij[1]]
		return eij['tt'] / eij['ftt']
	
	E = G.edges()
	V = G.nodes()
	M = G.copy()
	nedges = len(E)

	# havlin factor
	hfactor = [havlin_factor(G,eij) for eij in E]

	# remove first the empty edges
	order = np.argsort(hfactor)
	rank = zeros(nedges)
	nnodes = nx.number_of_nodes(max(nx.weakly_connected_component_subgraphs(M),key=len))

	count = 0
	tic = time.time()
	progressbar(count, nedges, prefix="Working:", suffix="Done", barLength=50)
	for i in order:
		M.remove_edge(E[i][0],E[i][1])
		if(hfactor[i]==1):continue
		nnodes_new = nx.number_of_nodes(max(nx.weakly_connected_component_subgraphs(M),key=len))
		rank[i] = nnodes - nnodes_new
		nnodes = nnodes_new
		count+=1
		if(count % 5 == 0): # update progress bar  
			progressbar(count,nedges,prefix='Working:', suffix = 'ETA %3.2f min (nnodes: %d)'%(expected_remaining_time(tic,count,nedges),nnodes),barLength=50)
		if(nnodes==1):break # the largest component is minimal

	print('hfactor[index]=',[rank[x] for x in order[0:5]])
	return rank

def load_data(wdir, city):
    # read graph files ##################################################
    print('Creating network')
    edges = pd.read_csv(wdir + city + '_edges_algbformat.txt', sep=' ')
    
    # creating graph
    G = nx.DiGraph()
    for i in range(len(edges.eid)):
        G.add_edge(edges.source[i], edges.target[i], eid=edges.eid[i], weight=edges.cost_time[i])
    print('   Number of nodes %d' % nx.number_of_nodes(G))
    print('   Number of edges %d' % nx.number_of_edges(G))
    
    # add edges info
    # print('Setting edge properties')
    # for k in range(len(rank.gid)):
        # i = edges.source[k]
        # j = edges.target[k]
        # if(G.has_edge(i,j)):
            # G.edge[i][j]['voc'] = rank.voc[k]
            # G.edge[i][j]['ftt'] = rank.ftt[k]
            # G.edge[i][j]['tt' ] = rank.tt[k]
            # G.edge[i][j]['cap'] = rank.cap[k]
        # else:
            # print('Properties of edge[%d][%d] could not be set' % (i,j))
        
    return edges, G
	
wdir = "../instances/"
for city in ['dial', 'porto', 'boston']:#['porto','lisbon','rio','sfbay','boston']:
    print('Working on ' + city.upper())
    edges, G = load_data(wdir, city)
    
    print('Calculating edge_betweenness_centrality')
    tic = time.time()
    btw = nx.edge_betweenness_centrality(G, k=None, normalized=False, weight='weight')
    print('   Total elapsed time %.3f hours' % ((time.time() - tic)/3600))
    btw = [btw[(edges.source[k], edges.target[k])] for k in range(len(edges.eid))]
    edges['btw'] = pd.Series(btw, index=edges.index)
    print('Saving btw rank table')
    edges.to_csv('rank_%s_edge_betweenness_centrality.csv' % city, index=False)