import pandas as pd
import numpy as np

problem = 'boston'
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
            
            print('Converting table to arrays')
            eids   = table['eid'].as_matrix()
            source = table['source'].as_matrix()
            target = table['target'].as_matrix()
            dist   = table['length_km'].as_matrix()
            idrank = table[rank].as_matrix()
            nedges = len(source)
            
            # (rank_id) -> row
            map_rank_to_row = dict()
            for k in range(nedges):
                map_rank_to_row[idrank[k]] = k
                
            print('Selecting edges')
            selected_rows = []
            total_dist = 0
            for k in range(min(idrank), max(idrank) + 1):
                row = map_rank_to_row[k]
                selected_rows.append(row)
                
                # consider only the length of non-artificial edges
                eid = eids[row]
                if eid >= 0:
                    total_dist += dist[row]
                else:
                    print('The length of edge (%d,%d) was not added' % (source[row], target[row]))
                
                # stop criteria
                if total_dist >= max_dist:
                    break
            print('   Number of selected edges: %d' % len(selected_rows))
            print('   Total distance (km):      %f' % total_dist)

            # create selected column
            selected = np.zeros(nedges, dtype=int)
            for row in selected_rows:
                selected[row] = 1
            table['selected'] = pd.Series(selected, index=table.index)

            # incrementing the edge capacities
            cap = table['capacity'].as_matrix()
            cap_old = cap.copy()
            for row in selected_rows:
                cap[row] *= (1 + alpha)
            table['capacity'] = pd.Series(cap, index=table.index)
            table['capacity_old'] = pd.Series(cap_old, index=table.index)

            instance_name = '%s_R%s_A%3.2f_D%03d.csv' % (problem, rank, alpha, max_dist)
            print('Saving instance: %s' % instance_name)
            table.to_csv(instance_name, index=False)