import numpy as np
from subprocess import check_output
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.stats import lognorm
from types import *
from traffic_assignment import dijkstra


def numberOfLines(filename):
    # Returns the number of lines in a file without open it
    return int(check_output(['wc', '-l', filename]).split()[0])


class City(object):
    def __init__(self, city_name):
        self.name = city_name
        self.nodes = self.read_nodes(city_name)
        self.edges = self.read_edges(city_name, self.nodes)

        # set sizes
        self.nnodes = self.nodes['lat'].size
        self.nedges = self.edges.source.size

        # create distance sparse matrix
        d = self.edges.dist_km
        s = self.edges.source
        t = self.edges.target
        self._D = {}
        for i in range(s.size):
            if (not self._D.has_key(s[i])):
                self._D[s[i]] = {}
            self._D[s[i]][t[i]] = d[i]

        self.show()

    @staticmethod
    def read_nodes(city_name):
        filename = '/home/michael/mit/instances/' + city_name + '_nodes_algbformat.txt'
        print('Reading nodes from ' + filename)
        nodes = np.genfromtxt(filename, delimiter=' ', names=True)
        nnodes = int(max(nodes['nid']))

        nid = (nodes['nid'] - 1).astype(np.int)  # converting to zero-based
        lat = np.zeros(nnodes, dtype=np.float)
        lon = np.zeros(nnodes, dtype=np.float)

        for i in range(nid.size):
            lat[nid[i]] = nodes['lat'][i]
            lon[nid[i]] = nodes['lon'][i]
        return dict(lat=lat, lon=lon)

    @staticmethod
    def read_edges(city_name, nodes):
        filename = '/home/michael/mit/instances/' + city_name + '_edges_algbformat.txt'
        print('Reading edges from ' + filename)
        edges = pd.read_csv(filename, sep=' ')
        edges = edges[edges.eid > -1]  # remove artificial edges
        edges.source = edges.source - 1  # convert to zero-based
        edges.target = edges.target - 1  # convert to zero-based
        edges['dist_km'] = City.__calc_dist_all(nodes, edges)
        return edges

    def dist(this, node_i, node_j):
        dij = this._D[node_i][node_j]
        return dij

    @staticmethod
    def __calc_dist_all(nodes, edges):
        s = edges.source
        t = edges.target
        d = np.zeros(s.size, dtype=np.float)
        for i in range(s.size):
            d[i] = City.__calc_dist(nodes, s[i], t[i])
        return d

    def show(self):
        print('City: ' + self.name)
        print('   #nodes: %d' % (self.nnodes))
        print('   #edges: %d' % (self.nedges))

    def show_node(this, nid, zero_based=True):
        print('Node[%d] %.7lf, %.7lf' % (nid, this.nodes['lat'][nid], this.nodes['lon'][nid]))

    @staticmethod
    def __calc_dist(nodes, node_i, node_j):
        # get nodes cartesian coordinates
        lat1 = nodes['lat'][node_i]
        lon1 = nodes['lon'][node_i]
        lat2 = nodes['lat'][node_j]
        lon2 = nodes['lon'][node_j]

        # Earth radius in kilometers
        R = 6371.009
        factor = np.pi / 180  # degrees to radians
        mlat = factor * (lat1 + lat2) / 2
        dlat = factor * (lat1 - lat2)
        dlon = factor * (lon1 - lon2)

        dij = R * np.sqrt(dlat ** 2 + (np.cos(mlat) * dlon) ** 2)
        return dij

    def show_edge(this, eid, zero_based=True):
        s = this.edges['s'][eid]
        t = this.edges['t'][eid]
        print('  s[%5d] %.7lf, %.7lf' % (s + (not zero_based), this.nodes['lat'][s], this.nodes['lon'][s]))
        print('  t[%5d] %.7lf, %.7lf' % (t + (not zero_based), this.nodes['lat'][t], this.nodes['lon'][t]))
        print('  dij: %lf km' % (this.calc_dist(s, t)))


class MatOD(object):
    def __init__(this, filename, city=None):
        print('Reading MatOD from ' + filename)
        assert isinstance(filename, StringType)
        this.name = filename
        npaths = numberOfLines(filename) - 1  # number of paths
        this.o = np.zeros(npaths, dtype=np.int)
        this.d = np.zeros(npaths, dtype=np.int)
        this.vol = np.zeros(npaths, dtype=np.int)
        this.tt = np.zeros(npaths, dtype=np.float)
        this.path = []
        rmod = dict(o=[], d=[], tt=[], vol=[])
        with open(filename) as fid:
            # skip header
            fid.readline()
            # read remaining rows
            issues = dict(zero_len=dict(pth=0, vol=0), zero_vol=dict(pth=0, vol=0), too_slow=dict(pth=0, vol=0))
            npaths = 0
            totPth = 0
            totVol = 0
            for rawline in fid.xreadlines():
                rawdata = np.fromstring(rawline, dtype=np.float, sep=' ')
                this.o[npaths] = rawdata[0] - 1  # convert to zero-based
                this.d[npaths] = rawdata[1] - 1  # convert to zero-based
                this.vol[npaths] = rawdata[2]
                this.tt[npaths] = rawdata[3]

                remove = False
                totVol += 1.0 * this.vol[npaths]
                totPth += 1.0
                # skipping zero length paths and
                if (this.o[npaths] == this.d[npaths]):
                    issues['zero_len']['vol'] += this.vol[npaths]
                    issues['zero_len']['pth'] += 1
                    remove = True

                # skipping paths with travel time (tt) larger than 120 min
                if (this.tt[npaths] > 120):
                    issues['too_slow']['vol'] += this.vol[npaths]
                    issues['too_slow']['pth'] += 1
                    remove = True

                # paths without travelers
                if (this.vol[npaths] == 0):
                    issues['zero_vol']['pth'] += 1
                    remove = True

                if remove:
                    rmod['o'].append(this.o[npaths] + 1)
                    rmod['d'].append(this.d[npaths] + 1)
                    rmod['tt'].append(this.tt[npaths])
                    rmod['vol'].append(this.vol[npaths])
                    continue

                # read path (if there is one to be read)
                path = []
                if (rawdata.size > 4):
                    path = rawdata[4:].astype(int) - 1  # convert to int and zero-based
                    path = np.flipud(path)  # order inversion
                this.path.append(path)
                npaths += 1

        # saving removed od pairs
        if len(rmod['o']) > 0:
            filename = filename.replace('.txt', '_removed.txt')
            print '   Saving file %s' % filename
            rmod = pd.DataFrame(rmod)
            rmod.to_csv(filename, sep=' ', index=False)

        # reshaping paths
        this.npaths = npaths
        if npaths < this.o.size:
            dsize = this.o.size - npaths
            print '   Reshaping by eliminating %d paths' % dsize
            print '      zero_volume       = %5d (#path: %2.1f%% vol: %2.1f%%)  ' % (
            issues['zero_vol']['pth'], 100 * issues['zero_vol']['pth'] / totPth,
            (100 * issues['zero_vol']['vol']) / totVol)
            print '      zero_length       = %5d (#path: %2.1f%% vol: %2.1f%%)' % (
            issues['zero_len']['pth'], 100 * issues['zero_len']['pth'] / totPth,
            (100 * issues['zero_len']['vol']) / totVol)
            print '      too_slow(>120min) = %5d (#path: %2.1f%% vol: %2.1f%%)' % (
            issues['too_slow']['pth'], 100 * issues['too_slow']['pth'] / totPth,
            (100 * issues['too_slow']['vol']) / totVol)
            this.o = this.o[:npaths]
            this.d = this.d[:npaths]
            this.vol = this.vol[:npaths]
            this.tt = this.tt[:npaths]
            this.path = this.path[:npaths]

        # calc path length in km
        this.city = city
        if (city is not None):
            this.dij = np.zeros(this.npaths, dtype=np.float)
            for i in range(this.npaths):
                this.dij[i] = this.path_length(this.path[i], city)

        # calc path velocity in km/h
        this.vij = 60 * this.dij / this.tt

        this.show()

    def __check(this):
        for i in range(this.npaths):
            if (this.tt[i] == 0):
                print('Edge #%d (%d,%d) zeroed travel time' % (i, this.o[i], this.d[i]))

    @staticmethod
    def path_length(path, city):
        dij = 0
        for j in range(path.size - 1):
            dij += city.dist(path[j], path[j + 1])
        return dij

    def show_path(this, pid, zero_based=False, verbose=False):
        if (this.city is not None):
            s = this.o[pid]
            t = this.d[pid]
            print('Path[%d]' % (pid))
            for i in this.path[pid]:
                print('Node %5d: %.8lf, %.8lf' % (i, this.city.nodes['lat'][i], this.city.nodes['lon'][i]))
            print(
            '  o[%5d] %.7lf, %.7lf' % (s + (not zero_based), this.city.nodes['lat'][s], this.city.nodes['lon'][s]))
            print(
            '  d[%5d] %.7lf, %.7lf' % (t + (not zero_based), this.city.nodes['lat'][t], this.city.nodes['lon'][t]))
            print('  dij: %lf km' % (this.dij[pid]))

    def show(this):
        print('MatOD: %s' % this.name)
        print('  #paths: %d' % this.npaths)

    def write_wkt_paths(this, pids, filename):
        with open(filename, 'w') as fid:
            for pid in pids:
                print('Writing wkt path ')
                this.show_path(pid)
                path = this.path[pid]
                fid.write('%d;LINESTRING(' % (pid))
                for j in range(len(path)):
                    nid = path[j]
                    fid.write('%.8lf %.8lf' % (this.city.nodes['lon'][nid], this.city.nodes['lat'][nid]))
                    if j == (len(path) - 1):
                        fid.write(')\n')
                    else:
                        fid.write(',')

    def get_table(self):
        return pd.DataFrame({'dij': self.dij, 'vij': self.vij, 'tt': self.tt, 'vol': self.vol})


class FlowTA(object):
    def __init__(self, filename, city=None):
        print 'Reading flow file', filename
        self.table = pd.read_csv(filename, sep=' ')
        self.tt = create_graph(self.table.s, self.table.t, self.table.tt)


def hist(x, weights=None, bins=10, distname='normal', color='b', label='pdf', filename=None):
    # create full data using weights
    z = x
    if (weights is not None):
        z = np.zeros(sum(weights))
        j = 0
        for i in range(weights.size):
            for k in range(j, j + weights[i]):
                z[j] = x[i]
                j += 1

    # histogram
    hist, bins = np.histogram(x, bins=bins, density=True, weights=weights)

    # fit distribution
    if (distname is 'normal'):
        (mu, sigma) = norm.fit(z)
        pdf = lambda x: norm.pdf(x, mu, sigma)
    elif (distname is 'lognormal'):
        sigma, loc, scale = lognorm.fit(z, floc=0)
        mu = np.log(scale)
        pdf = lambda x: lognorm.pdf(x, sigma, loc, scale=scale)
    elif (distname is not None):
        raise Exception('Unsupported distribution name ' + distname)

    # plot distribution
    if (distname is not None):
        x = np.linspace(bins[0], bins[-1], 100)
        y = pdf(x)
        label = 'm=%2.1f, s=%2.1f [%s]' % (mu, sigma, label)
        plt.plot(x, y, linewidth=3, label=label, alpha=0.7, color=color)

    # plot histogram
    c = (bins[:-1] + bins[1:]) / 2;  # bins centers
    plt.plot(c, hist, marker='s', alpha=0.7, markersize=8, linestyle='None', color=color)

    # format plot    
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.ylabel('PDF', fontsize=16)

    if (filename is not None):
        print('Saving figure ' + filename)
        plt.savefig(filename, bbos_inches='tight')


def create_graph(i, j, v):
    print 'Creating graph'
    G = {}
    for k in range(len(i)):
        if not G.has_key(i[k]):
            G[i[k]] = {}
        if not G[i[k]].has_key(j[k]):
            G[i[k]][j[k]] = v[k]
        else:
            raise Exception('Duplicated entry has been found')
    return G

def missing_nodes(N, G):
    # check matod nodes
    missing_nodes = []
    for i in G.keys():
        if not (i in missing_nodes or i in N):
            #print 'missing vertex %d' % i
            missing_nodes.append(i)
        for j in G[i].keys():
            if not (j in missing_nodes or j in N):
                #print 'missing vertex %d' % j
                missing_nodes.append(j)
    return missing_nodes

def create_filtered_matod(city):    
    # read nodes
    print 'Reading nodes'
    fid = '/home/ascanio/Mit/ods_and_roads/%s/%s_nodes_algbformat.txt'%(city, city)
    nodes = pd.read_csv(fid, sep=' ')
    N = nodes.nid.as_matrix()

    print 'Reading MatOD'
    fid = '/home/ascanio/Mit/ods_and_roads/%s/%s_interod_0_1.txt' %(city, city)
    matod = pd.read_csv(fid, sep=' ')

    print 'Filtering'
    o = matod.o.as_matrix()
    d = matod.d.as_matrix()
    b = [False] * len(o)
    c = 0
    for k in range(len(o)):
        if o[k] in N and d[k] in N:
            b[k] = True
            c += 1
    print 'Number of excluded edges %d of %d' %(len(o) - c, len(o))
    matod = matod[b]

    print 'Saving file'
    fid = '/home/ascanio/Mit/instances/tables/%s_table_od.csv' % city
    matod.to_csv(fid, sep=' ', index=False)
    print 'Done'

def calculate_matod_travel_time(city):
    print 'Reading MatOD'
    fid = '/home/ascanio/Mit/instances/tables/%s_table_od.csv' % city
    matod = pd.read_csv(fid, sep=' ')
    
    print 'Creating MatOD graph'
    o = matod.o.as_matrix()
    d = matod.d.as_matrix()
    f = matod.flow.as_matrix()
    M = create_graph(o,d,f)

    def get_minimial_paths(M, fid):
        print 'Reading Flow %s' % fid        
        flow = pd.read_csv(fid, sep=' ')
    
        print 'Creating Flow Graph'
        s = flow.s.as_matrix()
        t = flow.t.as_matrix()
        c = flow.tt.as_matrix()
        F = create_graph(s,t,c)

        print 'Finding minimimal paths'    
        C = create_graph(o,d,np.zeros(len(o)))
        for i in M.keys():
            c, p = dijkstra(F, i)
            J = np.sort(M[i].keys())
            for j in J:
                C[i][j] = c[j]
        return C

    def get_path_cost_array(o,d,C):
        n = len(o)
        c = np.zeros(n)
        for i in range(n):
            c[i] = C[o[i]][d[i]]

    table = {'o':o,'d':d,'flow':f}

    C = get_minimial_paths(M, '/home/ascanio/Mit/instances/%s_selfishflows_0_10.txt' % city)
    table['tt'] = get_path_cost_array(o,d,C)

    ranks  = ['btwall', 'voc', 'cluster']    
    alphas = ['1', '5']
    for rank in ranks:
        for alpha in alphas:
            fid = '/home/ascanio/Mit/instances/results/%s_selfishflows_0_%s_0%s.txt' % (city, rank, alpha)
            C = get_minimial_paths(M, fid)
            table['tt_%s_%s' % (rank, alphas)] = get_path_cost_array(o,d,C)
    
    table = pd.DataFrame(table)
    fid = '/home/ascanio/Mit/instances/tables/%s_tt_od.csv' % city
    table.to_csv(fid, sep=' ', index=False)

if __name__ == '__main__':
    calculate_matod_travel_time('porto')
    # # convert matod to a graph M
    # o = matod.o.as_matrix()
    # d = matod.d.as_matrix()
    # f = matod.flow.as_matrix()
    # C = create_graph(o, d, f)
    # nrows = len(o)

    # create_filtered_matod(N, matod)

    # print 'Reading edges'
    # edges = pd.read_csv('/home/ascanio/Mit/ods_and_roads/porto/porto_edges_algbformat.txt', sep=' ')
    # s = edges.source.as_matrix()
    # t = edges.target.as_matrix()
    # c = edges.cost_time.as_matrix()
    # E = create_graph(s, t, c)

    # # check edges
    # issues = missing_nodes(N, E)
    # print 'There are %d edge vertices that have no (lat,lon) info.' % len(issues)

    # # get travel time graph
    # G = FlowTA('/home/ascanio/Mit/instances/porto_selfishflows_0_10.txt').tt

    # # check flow node
    # issues = missing_nodes(N, G)
    # print 'There are %d nodes in FlowTA that have no (lat,lon) info.' % len(issues)

   

    # # check matod nodes
    # issues = missing_nodes(N, C)        
    # print 'There are %d nodes in MatOD that have no (lat,lon) info.' % len(issues)
    # count = 0
    # for i in G.keys():
    #     for j in G[i].keys():
    #         if (i in N or j in N):
    #             count+=1
    # print 'There are %d edges in MatOD that have no (lat,lon) info.' % count


    # # get original travel times
    # for i in C.keys(): # origins
    #     print 'i = ', i
    #     c, p = dijkstra(G, i)
    #     for j in C[i].keys():
    #         C[i][j] = c[j]
    #     break

    # # add new column
    # T = np.array(nrows, dtype=float)
    # for k in range(nrows):
    #     T[k] = C[o[k]][d[k]]

    # matod['T'] = pd.Series(T, index=matod.index)

    # load city
    # city = City('porto')
    # # read traffic assignments
    # F1 = FlowTA('/home/michael/mit/instances/results/porto_selfishflows_0_btwall_01.txt')
    # F5 = FlowTA('/home/michael/mit/instances/results/porto_selfishflows_0_btwall_05.txt')
    #
    # # get travel time graphs
    # G1 = F1.tt
    # G5 = F5.tt
    #
    # # get shortest paths cost
    # T1 = np.array(matod.count(), dtype=float)
    # T5 = np.array(matod.count(), dtype=float)

    # save result
    # print 'Saving result'
    # matod.to_csv('/home/michael/mit/instances/tables/porto_table_od.csv', sep=' ', index=False)

# # load matod
#     matod = {'10':[], 'voc_05':[], 'btwall_05':[], 'clus_05':[]}
#     for key in matod.keys():
#         matod[key] = MatOD('instances/Results_ita/' + city.name + '_' + key + '_od_a.txt', city)
#
#     #%% Analysis
#     ranks = ['10', 'voc_05', 'btwall_05', 'clus_05']
#     color = {'10':'b', 'voc_05':'r' , 'btwall_05':'g', 'clus_05':'m'}
#
#     #%% histogram velocity - normal
#     plt.figure(figsize=(12,3))
#     for rank in ranks:
#         table = matod[rank].get_table()
#         hist(table.vij,table.vol,bins=140,color=color[rank],label=rank)
#     plt.legend(loc='best')
#     plt.xlabel('Velocity (km/h)', fontsize=16)
#     plt.title('Porto - Velocity (Normal Distribution)', fontsize=16)
#
#     #%% histogram distance - lognormal
#     plt.figure(figsize=(12,3))
#     for rank in ranks:
#         table = matod[rank].get_table()
#         hist(table.dij,table.vol,bins=140,distname='lognormal',color=color[rank],label=rank)
#     plt.legend(loc='best')
#     plt.xlabel('Distance (km)', fontsize=16)
#     plt.title('Porto - Distance (Lognormal Distribution)')
#
#     #%% histogram travel times - lognormal
#     plt.figure(figsize=(12,3))
#     for rank in ranks:
#         table = matod[rank].get_table()
#         hist(table.tt,table.vol,bins=140,distname='lognormal',color=color[rank],label=rank)
#     plt.legend(loc='best')
#     plt.xlabel('Travel Time (min)', fontsize=16)
#     plt.title('Porto - Travel Time')
#
#     #%% Distance vs Travel Time
#     table = matod['10'].get_table()
#
#     plt.figure()
#     plt.subplot(1, 2, 1)
#     plt.hist2d(table.tt, table.vij, bins=50)
#     plt.colorbar()
#     plt.xlabel('Travel Time (min)',fontsize=12)
#     plt.ylabel('Distance (km)',fontsize=12)
#     plt.title('Histogram')
#     axis = plt.axis()
#
#     plt.subplot(1, 2, 2)
#     plt.scatter(table.tt, table.vij, s=10, alpha=.1)
#     plt.xlabel('Travel Time (min)',fontsize=12)
#     plt.ylabel('Distance (km)',fontsize=12)
#     plt.axis(axis)
#     plt.show()
