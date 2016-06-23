nodes = readtable('/home/ascanio/Mit/instances/porto_nodes_algbformat.txt', 'Delimiter', ' ');
n = max(nodes.nid);

matod = readtable('/home/ascanio/Mit/instances/tables/porto_table_od.csv', 'Delimiter',' ');
G = sparse(matod.o, matod.d, matod.flow, n, n);

flow = readtable('/home/ascanio/Mit/instances/porto_selfishflows_0_10.txt', 'Delimiter', ' ');
F = sparse(flow.s, flow.t, flow.tt, n, n);

i = 1;
[~,J,~] = find(G(1,:));
for j = 1:length(J)
    [dist, path, pred] = graphshortestpath(F,i,J(j));
    fprintf('(%d, %d) %f\n',i,J(j),dist);
end



