CITY = {'lisbon','porto','sfbay','boston'};

RANK  = {'btw_id', 'voc_id', 'clus_id'};
ALPHA = [0.0, 0.1, 0.2, 0.5, 0.7, 1.0];
cost_bpr = @(ftt,cap,vol) vol .* (ftt .* (1 + 0.15 * (vol ./ cap).^4));

%% plot total costs
close all
for icity = 1:length(CITY)
    city = CITY{icity};
     for i = 1:length(RANK)
        rank = RANK{i};
        fig = figure;
        AXES = axes('Parent', fig);
        hold on
        box on
        for dist = [50, 100, 250, 500]
            total_cost = zeros(length(ALPHA), 1);
            for k = 1:length(ALPHA)
                alpha = ALPHA(k);
                problem = sprintf('../python/%s_R%s_D%03d_A%3.2f_xsol.csv', city, rank, dist, alpha);
                if alpha == 0
                    problem = sprintf('../instances/%s_xsol.txt', city);
                end
                fprintf('Reading problem %s\n', problem)
                table = readtable(problem, 'Delimiter', ' ');
                total_cost(k) = sum(cost_bpr(table.ftt, table.cap, table.vol));
            end
            plot(ALPHA, total_cost/total_cost(1), 'DisplayName', sprintf('L=%d', dist), 'LineWidth', 2, 'Marker', 'o');
        end
        xlabel('\alpha', 'FontSize', 20);
        ylabel('Total Cost', 'FontSize', 20);
        stitle = sprintf('%s - %s',upper(city), upper(rank));
        stitle = strrep(stitle,'_ID','');
        title(stitle, 'FontSize', 16);
        LEG = legend(AXES, 'show');
        set(LEG, 'FontSize', 16, 'Location','southwest')
        drawnow
        figname = sprintf('fig_total_cost_%s_%s', city, rank);
        print(figname, '-dpng');
     end
end

%% create table of direct contribution
fid = fopen('direct_cost.csv', 'w');
fprintf(fid,'city,rank,dist,alpha,total_cost,direct_cost\n');
for icity = 1:length(CITY)
    city = CITY{icity};
    % read original capacities
    table = readtable(sprintf('../instances/%s_xsol.txt', city), 'Delimiter', ' ');
    CAPo  = sparse(table.source, table.target, table.cap);
    for i = 1:length(RANK)
        rank = RANK{i};
        for dist = [50, 100, 250, 500]
            problem = sprintf('../python/%s_R%s_D%03d_A0.10_xsol.csv', city, rank, dist);
            table = readtable(problem, 'Delimiter', ' ');
            % identifying edges whose capacities were modified
            CAPk  = sparse(table.source, table.target, table.cap);
            [ui,uj,ux] = find(CAPk - CAPo);
            index = abs(ux) > 1E-8;
            ui = ui(index);
            uj = uj(index);
            for k = 1:length(ALPHA)
                alpha = ALPHA(k);
                problem = sprintf('../python/%s_R%s_D%03d_A%3.2f_xsol.csv', city, rank, dist, alpha);
                if alpha == 0
                    problem = sprintf('../instances/%s_xsol.txt', city);
                end
                fprintf('Reading problem %s\n', problem)
                table = readtable(problem, 'Delimiter', ' ');
                cost  = cost_bpr(table.ftt, table.cap, table.vol);
                COST = sparse(table.source, table.target, cost);
                total_cost = sum(cost);
                direct_cost = 0;
                for j = 1:length(ui)
                    direct_cost = direct_cost + COST(ui(j), uj(j));
                end
                fprintf(fid,'%s,%s,%d,%g,%g,%g\n',city,rank,dist,alpha,total_cost,direct_cost);
            end
        end
    end
end
fclose(fid);
%% plot cluster sizes
for k = 1:length(CITY)
    city = CITY{k};
    data = readtable(['cluster_data_' city '.csv']);
    fig = figure;
    AXES = axes('Parent',fig);
    box(AXES,'on');
    hold(AXES,'on');
    plt = plot([data.voc,data.voc],[data.sz_1st_comp,data.sz_2nd_comp],'LineWidth',1);
    set(plt(1),'DisplayName','LC','Marker','o');
    set(plt(2),'DisplayName','SC','Marker','diamond');
    xlabel('Threshold q');
    ylabel('Cluster Size');
    title(sprintf('Cluster - %s', upper(city)));
    LEG = legend(AXES,'show');
    set(LEG,'Location','northwest');
    print(['fig_cluster_size_' city ], '-dpng');
end