function create_rank_table(CITY)
if ~iscell(CITY)
    CITY = {CITY};
end

for j = 1:length(CITY)
    city = CITY{j};
    
    %% read original traffic assignment table
    fprintf('Reading original data: %s\n', upper(city));
    table = readtable(['../instances/' city '_edges.csv'], 'Delimiter', ' ');
    nedges = length(table.source);
    index = (1:nedges)';
    map_eid = sparse(table.source, table.target, index);
        
    %% VOC
    fprintf('Creating VOC rank\n');
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
    fprintf('Creating BTW rank\n');
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
    table.btw_id = index;
    table.btw_id(btw_id) = index;
    
    %% create rank table
    fprintf('Saving rank table\n');
    writetable(table, ['rank_table_' city '.csv']);
end
end