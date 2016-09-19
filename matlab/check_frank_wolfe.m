%% MAIN FUNCTION
function cost = check_frank_wolfe(options)
if(nargin < 1)
    problem = 'dial';
    options = struct(...
        'DerivativeCheck','off',...
        'StartPointMethod','ones',...
        'SolveMethod','frank_wolfe');
end

% load data
[nodes, edges, matod] = load_data(problem);

% set constraints and variables map
[Aeq,beq,xmap] = create_constraints(nodes,edges,matod);

% set initial solution
x = initial_solution(nodes, edges, matod, xmap, options.StartPointMethod);

% check bpr definition
if(strcmp(options.DerivativeCheck,'on'))
    check_bpr(edges, xmap, x);
end

% solve traffic assignment
[x,cost] = solve_nlp(edges, xmap, x, Aeq, beq, options.SolveMethod);

% check optimality
check_optimality(sprintf('fw_paths_%s.csv', problem),nodes, edges, matod, xmap, x);

% set vols (output)
save_solution(sprintf('fw_sol_%s.csv', problem), edges, xmap, x);
end

%% INITIAL SOLUTION
function x = initial_solution(nodes, edges, matod, xmap, method)
if(nargin < 5)
    method = 'shortestpath';
end

fprintf('Set initial solution using %s method\n', method);

nedges = length(edges.s);
nflows = length(matod.d);
nnodes = length(nodes.nid);
nvars  = xmap.nvars;

% emap(source,target) = eij (edge index)
emap = sparse(edges.s,edges.t,1:nedges);

switch method
    case 'ones'
        x = ones(nvars, 1);
    case 'random'
        x = rand(nvars, 1);
    case 'shortestpath'
        % creates graph G
        A = sparse(edges.s, edges.t, edges.ftt, nnodes, nnodes);
        % set initial solution
        x = zeros(nvars, 1);
        for k = 1:nflows
            i = matod.o(k);
            s = matod.d(k);
            v = matod.vol(k);
            [~,path,~] = graphshortestpath(A,i,s);
            for w = 2:length(path)
                i   = path(w - 1);
                j   = path(w);
                ij  = emap(i,j);
                xij = xmap.sij2xij(s,ij);
                x(xij) = x(xij) + v;
            end
        end
    otherwise
        error('UnsupportedMethod')
end
end

%% SOLVE NLP
function [x, cost] = solve_nlp(edges, xmap, x,Aeq,beq,method)
if(nargin < 5)
    method = 'fmincon';
end

fprintf('Solving nonlinear problem using %s\n', method);
switch method
    case 'fmincon'
        [x,cost] = solve_nlp_fmincon(edges, xmap, x, Aeq, beq);
    case 'frank_wolfe'
        [x,cost] = solve_nlp_frank_wolfe(edges, xmap, x, Aeq, beq);
    otherwise
        error('UnkownMethod')
end
end

%% SOLVE NLP USING FMINCON
function [x,cost] = solve_nlp_fmincon(edges, xmap, x, Aeq, beq)
options = optimoptions('fmincon',...
    'GradObj','on',...
    'Hessian','off',...
    'DerivativeCheck','off',...
    'Display','iter-detailed',...
    'PlotFcns',@optimplotfval,...
    'MaxIter',1000,...
    'Algorithm','interior-point');
A = [];
b = [];
lb = zeros(size(x));
ub = inf(size(x));
nonlcon = [];
fobj = @(x)bpr(edges,xmap,x);
% warning('off','MATLAB:nearlySingularMatrix');
[x, cost] = fmincon(fobj,x,A,b,Aeq,beq,lb,ub,nonlcon,options);
fprintf('   Final cost: %E\n', cost);
% warning('on','all');
end

%% SOLVER NLP USING FRANK WOLFE ALGORITHM
function [x,fx] = solve_nlp_frank_wolfe(edges, xmap, x, Aeq, beq)
% See LeBlanc1976

options = optimoptions('linprog','Display','none');

% set algorithm parameters
maxit = 10000;
xtol = 1E-3;
ftol = 1E-3;

% set linear programming parameters
A = [];
b = [];
lb = zeros(size(x));
ub = inf(size(x));

% initialization (x is viable)
[~ , g] = bpr(edges, xmap, x);
x = linprog(g,A,b,Aeq,beq,lb,ub,x,options);
[fx, g] = bpr(edges, xmap, x);
niter = 0;
done  = false;
while(~done)
    niter = niter + 1;
    
    % bpr linear approx
    y = linprog(g,A,b,Aeq,beq,lb,ub,x,options);
    
    % line search
    d = y - x; % direction
    f = @(a)bpr(edges, xmap, x + a * d);
    a = fminbnd(f, 0, 1);
    y = x + a * d;
    [fy,g] = bpr(edges, xmap, y);
    
    % changes
    dx = norm(y - x)/max(1,norm(x));
    df = abs(fy - fx)/max(1,abs(fx));
    
    if(mod(niter,20) == 1)
        fprintf(' iter       fx           dx           df\n')
        fprintf('------------------------------------------------\n')
    end
    fprintf('%5d  %5E  %5E  %5E\n', niter, fy, dx, df);
    
    % stop criteria
    if(dx < xtol)
        fprintf('   Converged because xtol has been achieved\n');
        done = true;
    elseif(df < ftol)
        fprintf('   Converged because ftol has been achieved\n');
        done = true;
    elseif(niter == maxit)
        fprintf('   Converged because maxit has been achieved\n');
        done = true;
    end
    
    % update
    x = y;
    fx = fy;
end
end

%% CREATE CONSTRAINTS
function [A,b,xmap] = create_constraints(nodes,edges,matod)
% See LeBlanc1975
fprintf('Creating constraint matrix\n');
nnodes = length(nodes.nid); % number of nodes
nedges = length(edges.gid); % number of edges

% destinations
S = unique(matod.d);

% problem size
nvars = nedges * length(S);        % number of variables
neqs  = (nnodes - 1) * length(S);  % number of equations

% map variable index (all flows)
irow = zeros(length(S) * nedges, 1);
icol = irow;
xval = irow;
% (var index) -> (edge index)
xmap_xij2eij = irow;
k = 0;
for i = 1:length(S)
    s = S(i);
    for j = 1:nedges
        k = k + 1;
        irow(k) = s;
        icol(k) = j;
        xval(k) = k;
        xmap_xij2eij(k) = j;
    end
end
% (target, edge index) -> (var index)
xmap_sij2xij = sparse(irow,icol,xval);

% map equation index
irow = zeros(length(S) * (nnodes - 1), 1);
icol = irow;
xval = irow;
k = 0;
for i = 1:length(S)
    s = S(i);
    for j = 1:nnodes
        if(s == j)
            continue
        end
        k = k + 1;
        irow(k) = j;
        icol(k) = s;
        xval(k) = k;
    end
end
emap = sparse(irow, icol, xval, nnodes, nnodes);

D = sparse(matod.o, matod.d, matod.vol, nnodes, nnodes);
irow = zeros(neqs * nvars, 1);
jcol = irow;
xval = irow;
b = zeros(neqs, 1);
k = 0;
for ij = 1:nedges
    i = edges.s(ij);
    j = edges.t(ij);
    for w = 1:length(S)
        s = S(w);
        
        % index of variable xsij (col of A)
        xsij = xmap_sij2xij(s,ij);
        
        % set row associated to D(j,s)
        if(abs(s-j) > 0) % s <> j
            k = k + 1;
            DjsRow = emap(j,s); % index of equation (row) associated to D(j,s)
            irow(k) = DjsRow;
            jcol(k) = xsij;
            xval(k) = -1;
            
            % set b (rhs)
            b(DjsRow) = D(j,s);
        end
        
        % set row associated to D(j,s)
        if(abs(s-i) > 0) % s <> i
            k = k + 1;
            DisRow = emap(i,s); % index of equation (row) associated to D(i,s)
            irow(k) = DisRow;
            jcol(k) = xsij;
            xval(k) = 1;
            
            % set b (rhs)
            b(DisRow) = D(i,s);
        end
    end
end
irow = irow(1:k);
jcol = jcol(1:k);
xval = xval(1:k);
A = sparse(irow,jcol,xval);

xmap = struct('xij2eij',xmap_xij2eij,'sij2xij',xmap_sij2xij,'s',S,'nvars',nvars);
end

%% BPR
function [c,g,h,cij,vij] = bpr(edges,xmap,x)
% c   :: total cost
% g   :: gradient
% cij :: cost of each edge
% vij :: vol on each edge

nedges = length(edges.gid);

% vij(k) = sum flows on k-th edge
vij = zeros(nedges, 1);
for xij = 1:length(x)
    eij = xmap.xij2eij(xij);
    vij(eij) = vij(eij) + x(xij);
end

% cost per edge
yij = (vij ./ edges.cap).^4;
cij = edges.ftt .* (1 + 0.15 * yij);
% Cij = Integral[cij(v),v=0..vij]
Cij = (edges.ftt .* vij) .* (1 + 0.03 * yij);

% total cost
c = sum(Cij);

% gradient
G = cij;            % gradient in edge space
g = zeros(size(x)); % gradient in x (var) space
for k = 1:length(xmap.s)
    s = xmap.s(k);
    for ij = 1:nedges
        xij = xmap.sij2xij(s,ij);
        g(xij) = g(xij) + G(ij);
    end
end

% hessiana
% H = 3 * edges.ftt .* (vij.^3) ./ (edges.cap.^4);
h = zeros(length(x));
% for ij = 1:nedges
%     hij = H(ij);
%     xij = xmap.sij2xij(xmap.s,ij);
%     for i = 1:length(xij)
%         for j = 1:length(xij)
%             h(xij(i),xij(j)) = hij;
%         end
%     end
% end
end

function check_bpr(edges, xmap, x)
fprintf('Checking BPR derivatives\n');
addpath DERIVESTsuite\
[~,g,h] = bpr(edges, xmap, x);
[G,err] = gradest(@(x)bpr(edges,xmap,x),x);
fprintf('   MaxGradError = %f, MaxNumGradError=%f\n',norm(G'-g,Inf),norm(err));
[H,err] = hessian(@(x)bpr(edges,xmap,x),x);
fprintf('   MaxHessError = %f, MaxNumHessError=%f\n',norm(H'-h,Inf),norm(err));
end

%% LOAD DATA
function [nodes, edges, matod] = load_data(problem)
fprintf('Reading nodes\n')
% fid = '/home/michael/mit/ods_and_roads/%s/%s_nodes_algbformat.txt'%(city, city)
fid = ['../instances/' problem '_nodes.txt'];

fprintf('   %s\n',fid);
nodes = readtable(fid, 'Delimiter',' ');

fprintf('Reading edges\n')
% fid = '/home/michael/mit/ods_and_roads/%s/%s_edges_algbformat.txt'%(city, city)
fid = ['../instances/' problem '_edges.txt'];
fprintf('   %s\n',fid);
edges = readtable(fid, 'Delimiter', ' ');

fprintf('Reading MatOD\n')
% fid = '/home/michael/mit/ods_and_roads/%s/%s_interod_0_1.txt' %(city, city)
fid = ['../instances/' problem '_od.txt'];
fprintf('   %s\n',fid);
matod = readtable(fid, 'Delimiter', ' ');
end

%% CHECK OPTIMALITY
function check_optimality(filename,nodes,edges,matod,xmap,x,options)
if(nargin < 7)
    options = struct('ShowPaths','on');
end

nflows = length(matod.vol);
nnodes = length(nodes.nid);

% fid to save shortest paths
if(strcmp(options.ShowPaths,'on'))
    fid = fopen(filename,'w');
end

[~,~,~,cij] = bpr(edges, xmap, x);
G = sparse(edges.s, edges.t, cij, nnodes, nnodes);
cost_per_path = 0.0;
for k = 1:nflows
    s = matod.o(k);
    t = matod.d(k);
    vol = matod.vol(k);
    [cost, path] = graphshortestpath(G,s,t);
    
    % save path
    if(strcmp(options.ShowPaths,'on'))
        fprintf(fid,'(%3d,%3d): ',s,t);
        for i = 1:length(path)
            fprintf(fid,'%d ', path(i));
        end
        fprintf(fid,'\n');
    end
    
    cost_per_path = cost_per_path + cost * vol;
end

cost_per_edge = 0.0;
for k = 1:length(x)
    eij = xmap.xij2eij(k);
    cost_per_edge = cost_per_edge + cij(eij) * x(k);
end

% close shortest path file
if(strcmp(options.ShowPaths,'on'))
    fclose(fid);
end

gap = 1 - cost_per_path / cost_per_edge;
fprintf('Optimality Analysis\n');
fprintf('   Cost per path: %5.3E\n', cost_per_path);
fprintf('   Cost per edge: %5.3E\n', cost_per_edge);
fprintf('   Gap .........: %3.2f%%\n', 100 * gap);
end

%% SAVE SOLUTION
function save_solution(filename, edges, xmap, x)
nedges = length(edges.gid); % number of edges
[~,~,~,cij,vij] = bpr(edges, xmap, x);
vols.flows = zeros(nedges, length(xmap.s));
for k = 1:length(xmap.s)
    s = xmap.s(k);
    for ij = 1:nedges
        xij = xmap.sij2xij(s,ij);
        vols.flows(ij,k) = x(xij);
    end
end
vols.total = vij;

% saving solution
edges = struct('gid',edges.gid,'s',edges.s,'t',edges.t,'cap',edges.cap,'ftt',edges.ftt,'vols',vols.total,'cij',cij);
for k = 1:length(xmap.s)
    edges.(sprintf('V%d',xmap.s(k))) = vols.flows(:,k);
end
edges = struct2table(edges);
writetable(edges, filename)
end