from graph_tool.all import *
import pandas as pd
import numpy as np

city = 'porto'

# read data
print('Reading nodes')
fid = '/home/michael/mit/ods_and_roads/%s/%s_nodes_algbformat.txt'%(city, city)
nodes = pd.read_csv(fid, sep=' ')
N = nodes.nid.as_matrix()

print('Reading edges')
fid = '/home/michael/mit/ods_and_roads/%s/%s_edges_algbformat.txt'%(city, city)
edges = pd.read_csv(fid, sep=' ')
s = edges.source.as_matrix()
t = edges.target.as_matrix()
c = edges.cost_time.as_matrix()

print('Reading MatOD')
fid = '/home/michael/mit/ods_and_roads/%s/%s_interod_0_1.txt' %(city, city)
matod = pd.read_csv(fid, sep=' ')

# create graph 
G = graph()
v_name = G.new_vertex_property("int")
v_lat  = G.new_vertex_property("float")
v_lon  = G.new_vertex_property("float")
for index, node in nodes.iterrows():
	v = G.add_vertex()
	v_name[v] = node.nid
	v_lat[v]  = node.lat
	v_lon[v]  = node.lon
	V[node.nid] = v

e_cap = G.new_edge_property("float")
e_ftt = G.new_edge_property("float")
e_vol = G.new_edge_property("float")
e_wgt = G.new_edge_property("float")
for index, edge in edges.iterrows():
	i = edge.o
	j = edge.d
	e = G.add_new_edge(V[i], V[j])
	e_cap[e] = edge.capacity
	e_ftt[e] = edge.ftt
	e_wgt[e] = edge.ftt
	e_vol[e] = 0.0
	E[(i,j)] = e


# define delay function and its derivative
def bpr(e_vol, e_cap, e_ftt):
	c = 0.0
	for e in E.values():
		cij = e_ftt[e]
		xij = e_vol[e]
		kij = e_cap[e]
		c += cij * (1 + 0.15 * (xij / kij)^4)
		g[e] = (0.6 * cij * xij^3) / (kij^4)
	return (c,g)

def FW(G, matod, e_vol, e_cap, e_ftt, e_wgt):
	# set initial solution
	for e in G.edges(): e_vol[e] = 0.0
	for index, row in matod.iterrows():
		vlist, elist = shortest_path(row.o, row.d, weights=e_wgt)
		for e in elist: e_vol[e] += row.vol

	done = False
	while(not done):
		# update linearized cost function
		(c,g) = bpr(e_vol, e_cap, e_ftt)
		for e in g.keys():
			e_wgt[e] = g[e]

		# get shortest paths
		for index, row in matod.iterrows():
			vlist, elist = shortest_path(row.o, row.d, weights=e_wgt)
			

	# write solution