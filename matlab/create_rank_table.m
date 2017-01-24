function create_rank_table(CITY)
if ~iscell(CITY)
    CITY = {CITY};
end

for j = 1:length(CITY)
    city = CITY{j};
    tic
    fprintf('Create rank table: %s\n', upper(city));
    %% read original traffic assignment table
    fprintf('   Reading original data\n');
    table = readtable(['../instances/' city '_edges.csv'], 'Delimiter', ' ');
    nedges = length(table.source);
    nnodes = max(max(table.source), max(table.target));
    index = (1:nedges)';
    map_eid = sparse(table.source, table.target, index);
        
    %% VOC
    fprintf('   Creating VOC rank\n');
    table_voc = readtable(['../instances/' city '_xsol.txt'], 'Delimiter', ' ');
    VOC = sparse(table_voc.source, table_voc.target, table_voc.vol ./ table_voc.cap);
    VOL = sparse(table_voc.source, table_voc.target, table_voc.vol);
    voc = zeros(nedges, 1);
    vol = voc;
    for k = 1:nedges
        s = table_voc.source(k);
        t = table_voc.target(k);
        eid = map_eid(s, t);
        voc(eid) = VOC(s, t);
        vol(eid) = VOL(s, t);
    end
    table.vol = vol;
    table.voc = voc;
    [~,voc_id] = sort(table.voc, 'descend');
    table.voc_id = zeros(size(index));
    table.voc_id(voc_id) = index;
    
    %% BETWEENNESS CENTRALITY
    fprintf('   Creating BTW rank\n');
    table_btw = readtable(['../python/rank_' city '_edge_betweenness_centrality.csv']);
    BTW = sparse(table_btw.source,table_btw.target,table_btw.btw);
    btw = zeros(size(index));
    for k = 1:length(btw)
        s = table_btw.source(k);
        t = table_btw.target(k);
        eid = map_eid(s, t);
        btw(eid) = BTW(s, t);
    end
    table.btw = btw;
    [~,btw_id] = sort(table.btw,  'descend');
    table.btw_id = zeros(size(index));
    table.btw_id(btw_id) = index;

    %% CLUSTER
    fprintf('   Creating CLUS rank\n')
    table_clus = readtable(['cluster_data_' city '.csv']);
    CLUS = sparse(table_clus.source, table_clus.target, table_clus.var_sz_1st_comp, nnodes, nnodes);
    clus = zeros(size(index));
    for k = 1:length(table_clus.source)
        s = table_clus.source(k);
        t = table_clus.target(k);
        eid = map_eid(s, t);
        clus(eid) = CLUS(s,t);
    end
    table.clus = clus;
    [~,clus_id] = sort(table.clus, 'descend');
    table.clus_id = zeros(size(index));
    table.clus_id(clus_id) = index;
    
    %% create rank table
    fprintf('   Saving rank table\n');
    writetable(table, ['rank_table_' city '.csv']);
    fprintf('   TElapsed %3.2f seconds\n', toc);
end
end