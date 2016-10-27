import pandas as pd
import numpy as np

problem = 'porto' 

# set instance file names #################################
if problem == 'porto':
    fid_sol = 'sol_porto_0_10.csv'
    fid_btw = '../mathematica/rank_porto_edge_betweenness_centrality.csv'
    fid_eid = '../instances/porto_edges_algbformat.txt'
    fid_nid = '../instances/porto_nodes_algbformat.txt'

def distance(x_lon, x_lat, y_lon, y_lat):
    # Reference: Wiki2012 - Geographical distances
            
    # Earth radius
    R = 6371.009    # kilometers
    # R = 3958.761; # statute miles
    # R = 3440.069; # nautical miles
            
            
    # conversion to radians
    factor = np.pi/180 # degrees to radians
    mean_latitude   = factor * (x_lat + y_lat) / 2
    delta_latitude  = factor * (x_lat - y_lat)
    delta_longitude = factor * (x_lon - y_lon)
            
    return R * np.sqrt(delta_latitude**2+(np.cos(mean_latitude)*delta_longitude)**2)
    
# reading nodes ###########################################
print('Reading nodes')
nodes = pd.read_csv(fid_nid, sep=' ')
lon = dict()
lat = dict()
for row in nodes.iterrows():
    nid = int(row[1].nid)
    lon[nid] = row[1].lon
    lat[nid] = row[1].lat
    
# reading edges ###########################################
print('Reading edges')
edges = pd.read_csv(fid_eid, sep=' ')
s = edges.source.as_matrix()
t = edges.target.as_matrix()
c = edges.cost_time.as_matrix()
v = edges.speed_mph.as_matrix()
    
# load traffic assignment solution ########################
print('Reading traffic assignment solution')
table = pd.read_csv(fid_sol, sep=',')
map_eid = dict();
dij = np.zeros(len(table.s))
for k in range(len(table.s)):
    sk = int(table.s[k])
    tk = int(table.t[k])
    map_eid[(sk, tk)] = k
    dij[k] = distance(lon[sk], lat[sk], lon[tk], lat[tk])
table['dij_km'] = pd.Series(dij, index = table.index)
    
# create VOC rank #########################################
print('Creating VOC rank')
voc = (table.vol / table.cap).as_matrix()
# sorting in ascending then reversing
index = np.argsort(voc)[::-1]
voc_id = np.zeros(len(index),dtype=int)
for k in range(len(index)):
    voc_id[index[k]] = k
table['voc'] = pd.Series(voc, index=table.index)
table['voc_id'] = pd.Series(voc_id, index=table.index)

# create BTW rank #########################################
print('Creating BTW rank')
table_btw = pd.read_csv(fid_btw, sep=',')
s = table_btw.source.as_matrix()
t = table_btw.target.as_matrix()
b = table_btw.EdgeBetweennessCentrality.as_matrix()
btw = np.zeros(len(table.s), dtype=int)
for k in range(len(b)):
    sk = int(s[k])
    tk = int(t[k])
    eid = map_eid[(sk,tk)]
    btw[eid] = b[k]
index = np.argsort(btw)[::-1]
btw_id = np.zeros(len(index),dtype=int)
for k in range(len(index)):
    btw_id[index[k]] = k
table['btw'] = pd.Series(btw, index=table.index)
table['btw_id'] = pd.Series(btw_id, index=table.index)
    
# save table
print('Saving table')
table.to_csv('table_porto_0_10.csv', index=False)