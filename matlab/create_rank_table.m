%% read original traffic assignment table
fprintf('Reading original data\n');
table = readtable('../python/sol_porto_0_10.csv');
% eid(s,t) :: index of edge (s,t)
map_eid = sparse(table.s, table.t, 1:length(table.s));
index   = (1:length(table.s))';

%% VOC
fprintf('Creating VOC rank\n');
table.voc = table.vol ./ table.cap;
[~,voc_id] = sort(table.voc, 'descend');
table.voc_id = index(voc_id);

%% BETWEENNESS CENTRALITY
fprintf('Creating BTW rank\n');
table_btw = readtable('../mathematica/rank_porto_edge_betweenness_centrality.csv');
s = table_btw.source;
t = table_btw.target;
B = sparse(s,t,table_btw.EdgeBetweennessCentrality);
btw = zeros(size(s));
for k = 1:length(btw)
    eid = map_eid(s(k), t(k));
    btw(eid) = B(s(k), t(k));
end
table.btw = btw;
[~,btw_id] = sort(table.btw,  'descend');
table.btw_id = index(btw_id);

%% create rank table
fprintf('Saving rank table\n');
writetable(table, 'table_porto_0_10.csv');