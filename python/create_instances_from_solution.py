import pandas as pd
import numpy as np

problem = 'porto'
MAX_DIST = {50, 100, 250, 500}
ALPHA = {0.1, 0.2, 0.5, 0.7, 1.0}
RANK = {'btw_id', 'voc_id'}

for alpha in ALPHA:
    for max_dist in MAX_DIST:
        for rank in RANK:
            fid_tab = '../matlab/rank_table_%s.csv' % problem
                
            # load table of ranks
            print('Reading table of ranks: %s' % fid_tab)
            table = pd.read_csv(fid_tab)

            table_gid = table['eid'].as_matrix()
            table_dij = table['dij_km'].as_matrix()
            table_rank_id = table[rank].as_matrix()

            rank_eid = dict()
            for eid in range(len(table_rank_id)):
                rank_eid[int(table_rank_id[eid])] = eid

            print('Selecting edges')
            selected_eids = []
            total_dist = 0
            for k in range(len(rank_eid)):
                eid = rank_eid[k]
                gid = table_gid[eid]
                selected_eids.append(eid)
                
                # consider only the length of non-artificial edges
                if gid >= 0:
                    total_dist += table_dij[eid]
                else:
                    print('The length of edge %d was not added' % gid)
                
                # stop criteria
                if total_dist >= max_dist:
                    break
            print('   Number of selected edges: %d' % len(selected_eids))
            print('   Total distance (km):      %f' % total_dist)

            # create selected column
            selected = np.zeros(len(rank_eid), dtype=int)
            for eid in selected_eids:
                selected[eid] = 1
            table['selected'] = pd.Series(selected, index=table.index)

            # incrementing the edge capacities
            cap = table['cap'].as_matrix()
            cap_old = cap.copy()
            for eid in selected_eids:
                cap[eid] *= (1 + alpha)
            table['cap'] = pd.Series(cap, index=table.index)
            table['cap_old'] = pd.Series(cap_old, index=table.index)

            print('Saving instance')
            table.to_csv('../instances/%s_R%s_A%3.2f_D%03d.csv' % (problem, rank, alpha, max_dist), index=False)