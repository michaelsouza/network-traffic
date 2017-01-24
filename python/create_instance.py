import numpy as np
import pandas as pd


def distance_from_coordinates(x_lon, x_lat, y_lon, y_lat):
    # Reference: Wiki2012 - Geographical distances

    # Earth radius
    radii = 6371.009  # kilometers
    # radii = 3958.761; # statute miles
    # radii = 3440.069; # nautical miles

    # Conversion to radians
    factor = np.pi / 180  # degrees to radians
    mean_latitude = factor * (x_lat + y_lat) / 2
    delta_latitude = factor * (x_lat - y_lat)
    delta_longitude = factor * (x_lon - y_lon)

    return radii * np.sqrt(delta_latitude ** 2 + (np.cos(mean_latitude) * delta_longitude) ** 2)


def create_instance(city):
    print('Creating instance of %s' % city.upper())
    print('Reading Edges')
    edges = pd.read_csv('../instances/%s_edges_algbformat.txt' % city, sep=' ')
    print('Reading Nodes')
    nodes = pd.read_csv('../instances/%s_nodes_algbformat.txt' % city, sep=' ')

    print('Creating nodes mapping')
    nodes_lon = nodes.lon.as_matrix()
    nodes_lat = nodes.lat.as_matrix()
    nodes_nid = nodes.nid.as_matrix()
    lon = {}
    lat = {}
    for k in range(len(nodes.nid)):
        lon[int(nodes_nid[k])] = nodes_lon[k]
        lat[int(nodes_nid[k])] = nodes_lat[k]

    # nid = 11094
    # print('lat[%d] : (%f,%f) ' % (nid, lon[nid], lat[nid]))

    print('Creating edges mapping')
    print('   Converting from mph to kmh')
    print('   Calculating distances from lat-lon coords')
    print('   Calculating cost in hours')
    eid = edges.eid.as_matrix()
    source = edges.source.as_matrix()
    target = edges.target.as_matrix()
    dir = edges.dir.as_matrix()
    capacity = edges.capacity.as_matrix()
    speed_kmh = 1.60934 * edges.speed_mph
    length_km = np.zeros((len(eid),), dtype=np.float)
    for k in range(len(eid)):
        i = source[k]
        j = target[k]
        length_km[k] = distance_from_coordinates(lon[i], lat[i], lon[j], lat[j])
    cost_time_hour = length_km / speed_kmh

    print('Saving edges')
    edges = pd.DataFrame.from_dict(dict(eid=eid,source=source,target=target,dir=dir,capacity=capacity,speed_kmh=speed_kmh,length_km=length_km,cost_time_hour=cost_time_hour))
    edges.to_csv('../instances/%s_edges.csv' % city, index=False, header=True, columns=["eid", "source", "target", "dir", "capacity", "speed_kmh", "length_km", "cost_time_hour"], sep=' ')

if __name__ == '__main__':
        cities = {'porto','lisbon','rio','boston','sfbay'}
        for city in cities:
            create_instance(city)
