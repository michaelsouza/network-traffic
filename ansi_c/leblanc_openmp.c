/*
 * leblanc.c
 *
 *  Created on: Nov 9, 2016
 *      Author: Michael Souza
 *      E-mail: souza.michael@gmail.com
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <limits.h>
#include <time.h>
#include <omp.h>

#define toc(x) ((double)(clock() - (x))/CLOCKS_PER_SEC)

// Node
typedef struct {
	int nid;
	double lon;
	double lat;
} Node;

void node_read_csv(char *csv_file_name, int *number_of_nodes, Node **nodes) {
	char * line = NULL;
	size_t len = 0, nlines = 0;
	ssize_t read;
	FILE *fid = fopen(csv_file_name, "r");
	double lon, lat;
	int nid;

	if (fid == NULL) {
		printf("The file %s could not be opened.\n", csv_file_name);
		exit(EXIT_FAILURE);
	}

	// memory allocation (counting the file number of lines)
	while ((read = getline(&line, &len, fid)) != -1) {
		nlines++;
	}
	*number_of_nodes = nlines - 1;
	*nodes = (Node*) malloc(sizeof(Node) * (*number_of_nodes));

	printf("\nReading node file: %s\n", csv_file_name);
	rewind(fid);
	// skipping file header
	read = getline(&line, &len, fid);
	nlines = 0;
	while ((read = getline(&line, &len, fid)) != -1) {
		if (sscanf(line, "%d %lf %lf\n", &nid, &lat, &lon) != 3) {
			printf("   Line[%zu] %s could not be read.\n", nlines + 1, line);
			exit(EXIT_FAILURE);
		}
		(*nodes)[nlines].lon = lon;
		(*nodes)[nlines].lat = lat;
		(*nodes)[nlines].nid = nid;
		nlines++;
	}

	fclose(fid);
	if (line)
		free(line);

	printf("   #Nodes : %d\n", *number_of_nodes);
}

void node_print_array(int number_of_nodes, Node *nodes) {
	int i;
	printf("               nid   lon   lat\n");
	for (i = 0; i < 5; i++) {
		printf("[Line %05d] % 5d % 3.2f % 3.2f\n", i + 2, nodes[i].nid,
				nodes[i].lat, nodes[i].lon);
	}
	printf("[..........]   ...  ....  ....\n");
	for (i = number_of_nodes - 5; i < number_of_nodes; i++) {
		printf("[Line %05d] % 5d % 3.2f % 3.2f\n", i + 2, nodes[i].nid,
				nodes[i].lon, nodes[i].lat);
	}
}

// Edge
typedef struct {
	int eid;
	int source;
	int target;
	int dir;
	double capacity;
	double speed_mph;
	double cost_time;
	double weight;
	double vol;
	int xid;
} Edge;

void edge_read_csv(char *csv_file_name, size_t *number_of_edges, Edge **edges) {
	char * line = NULL;
	size_t len = 0, nlines = 0;
	ssize_t read;
	FILE *fid = fopen(csv_file_name, "r");
	double capacity, speed_mph, cost_time;
	int eid, source, target, dir;

	if (fid == NULL) {
		printf("The file %s could not be opened.\n", csv_file_name);
		exit(EXIT_FAILURE);
	}

	// memory allocation (counting the file number of lines)
	while ((read = getline(&line, &len, fid)) != -1) {
		nlines++;
	}
	*number_of_edges = nlines - 1;
	*edges = (Edge*) malloc(sizeof(Edge) * (*number_of_edges));

	printf("\nReading edge file: %s\n", csv_file_name);
	rewind(fid);
	// skipping file header
	read = getline(&line, &len, fid);
	nlines = 0;
	while ((read = getline(&line, &len, fid)) != -1) {
		if (sscanf(line, "%d %d %d %d %lf %lf %lf\n", &eid, &source, &target, &dir, 
			&capacity, &speed_mph, &cost_time) != 7) {
			printf("   Line[%zu] %s could not be read.\n", nlines + 1, line);
			exit(EXIT_FAILURE);
		}
		(*edges)[nlines].eid       = eid;
		(*edges)[nlines].source    = source;
		(*edges)[nlines].target    = target;
		(*edges)[nlines].dir       = dir;
		(*edges)[nlines].capacity  = capacity;
		(*edges)[nlines].speed_mph = speed_mph;
		(*edges)[nlines].cost_time = cost_time;
		(*edges)[nlines].vol       = 0.0;
		nlines++;
	}

	fclose(fid);
	if (line)
		free(line);

	printf("   #Edges : %zu\n", *number_of_edges);
}

void edge_print_array(Edge *edges, size_t number_of_edges) {
	int i;
	printf("Edges:\n");
	printf("                  eid   source   target  capacity cost_time\n");
	for (i = 0; i < 5; i++) {
		printf("[Line %05d] % 8d % 8d % 8d %9.2g %9.2g\n", i + 2, edges[i].eid,
				edges[i].source, edges[i].target, edges[i].capacity,
				edges[i].cost_time);
	}
	printf("[..........]   ...  ....  ....\n");
	for (i = number_of_edges - 5; i < number_of_edges; i++) {
		printf("[Line %05d] % 8d % 8d % 8d %9.2g %9.2g\n", i + 2, edges[i].eid,
				edges[i].source, edges[i].target, edges[i].capacity,
				edges[i].cost_time);
	}
}

void edge_sort_by_source_target_indices(Edge *edge, size_t number_of_edges){
	Edge swap; // swap
	int i, j, k;
	// using bubble sort
	for(i = 0; i < number_of_edges; i++){
		k = i;
		swap = edge[i];
		for(j = i - 1; j >= 0; j--){
			if(swap.source  > edge[j].source ||
			  (swap.source == edge[j].source && swap.target > edge[j].target)){
				break;
			}else{
				k = j;
				edge[j+1] = edge[j];
			}
		}
		edge[k] = swap;
	}
}

// Heap
typedef struct{
	int   *nid; // array of nodes' ids
	double *cost;
	size_t len;
	size_t capacity;
} Heap;

void heap_init(size_t capacity, Heap *heap){
	heap->nid  = (int*) malloc(sizeof(int) * capacity);
	heap->cost = (double*) malloc(sizeof(double) * capacity);
	heap->len  = 0;
	heap->capacity = capacity;
}

void heap_push(Heap *heap, int nid, double cost){
	if(heap->len == heap->capacity){
		printf("Heap maximum capacity has been reached.\n");
		exit(EXIT_FAILURE);
	}

	// bottom-up
	size_t node = heap->len, parent;
	heap->len++;
	while(node > 0){
		parent = (node - 1) / 2;
		if(cost > heap->cost[parent]){
			heap->nid[node]  = nid;
			heap->cost[node] = cost;
			return;
		}
		// swap with parent
		heap->nid[node] = heap->nid[parent];
		heap->cost[node] = heap->cost[parent];
		node = parent;
	}
	heap->nid[0] = nid;
	heap->cost[0] = cost;
}

void heap_pop(Heap *heap, int *nid, double *cost){
	// set output values
	*nid = heap->nid[0];
	*cost = heap->cost[0];

	// update heap - move the last node to the top
	heap->nid[0] = heap->nid[heap->len - 1];
	heap->cost[0] = heap->cost[heap->len - 1];
	heap->len--;

	int node = 0, child, node_nid;
	double node_cost;
	// node has one child at least
	while(2 * node + 1 < heap->len){
		child = 2 * node + 1;
		// find the child with smallest cost
		if(child + 1 < heap->len && heap->cost[child] >	heap->cost[child + 1]){
			child++;
		}
		// heap is ok!
		node_nid = heap->nid[node];
		node_cost = heap->cost[node];
		if(node_cost < heap->cost[child]){
			break;
		}
		// swap
		heap->nid[node] = heap->nid[child];
		heap->cost[node] = heap->cost[child];
		heap->nid[child] = node_nid;
		heap->cost[child] = node_cost;
		node = child;
	}
}

void heap_print(Heap *heap){
	int i;
	printf("Heap (capacity: %zu, len: %zu)\n", heap->capacity, heap->len);
	if(heap->len == 0){
		printf("The heap is empty\n");
		return;
	}
	printf("   nid   cost\n");
	for(i = 0; i < heap->len; i++){
		printf("%6d %8g\n", heap->nid[i], heap->cost[i]);
	}
}

void heap_free(Heap *heap){
	free(heap->cost);
	free(heap->nid);
}

// Graph (using CSR)
typedef struct{
	size_t number_of_nodes;
	size_t number_of_edges;
	int *i;    // accessed using one-based index scheme
	int *j;
	Edge *eij;
	int min_nid;
	int max_nid;
} Graph;

void graph_init(Graph *G, Edge *edges, size_t number_of_edges){
	printf("Creating network graph.\n");
	int i, j, nid, source;
	int max_nid = INT_MIN, min_nid = INT_MAX;
	
	edge_sort_by_source_target_indices(edges, number_of_edges);
	
	// memory allocation
	for(i = 0; i < number_of_edges; i++){
		nid = edges[i].source > edges[i].target ? edges[i].source : edges[i].target;
		if( nid > max_nid ) max_nid = nid;
		nid = edges[i].source < edges[i].target ? edges[i].source : edges[i].target;
		if( nid < min_nid ) min_nid = nid;
	}
	G->min_nid = min_nid;
	G->max_nid = max_nid;
	G->i = (int *) malloc(sizeof(int) * (max_nid + 2)); // accessed using one-based index
	G->j = (int *) malloc(sizeof(int) * number_of_edges);
	for(i = 0; i < (max_nid + 2); i++) G->i[i] = 0;     // cleanup memory 
	
	// setup using CSR
	nid = min_nid;
	for(i = 0; i < number_of_edges; i++){
		G->j[i] = edges[i].target;
		source = edges[i].source;
		if(source != nid){
			for(j = nid + 1; j <= source; j++){
				G->i[j] = i;
			}
			nid = source;
		}
		// update edge index
		edges[i].xid = i;
	}
	for(j = nid + 1; j <= (max_nid + 1); j++){
		G->i[j] = number_of_edges;
	}
	
	G->number_of_edges = number_of_edges;
	G->number_of_nodes = max_nid;
	G->eij = edges;
}

void graph_print(Graph *G){
	int i;
	Edge *edges = G->eij;
	printf("#Edges: %zu\n", G->number_of_edges);
	printf("#Nodes: %zu\n", G->number_of_nodes);
	printf("   eid   source   target capacity cost_time\n");
	for (i = 0; i < 5; i++) {
		printf("  % 5d % 6d % 8d %9.2f %7.2f\n", edges[i].eid,
				edges[i].source, edges[i].target, edges[i].capacity,
				edges[i].cost_time);
	}
	printf("     ...  ....  ....\n");
	for (i = G->number_of_edges - 5; i < G->number_of_edges; i++) {
		printf("  % 5d % 6d % 8d %9.2f %7.2f\n", edges[i].eid,
				edges[i].source, edges[i].target, edges[i].capacity,
				edges[i].cost_time);
	}
}

void graph_free(Graph *G){
	free(G->i);
	free(G->j);
}

void graph_neighs(Graph *G, int i, int **neighs, int *nelems){
	*nelems = G->i[i + 1] - G->i[i]; 
	*neighs = &(G->j[G->i[i]]); 
}

void graph_vertex_edges(Graph *G, int v, Edge **edges, size_t *nedges){
	*nedges = G->i[v + 1] - G->i[v]; 
	*edges  = &(G->eij[G->i[v]]); 
}

Edge* graph_edge(Graph *G, int i, int j){
	Edge *eij;
	size_t n;
	graph_vertex_edges(G, i, &eij, &n);
	int k;
	for(k=0;k<n;k++){
		if(eij[k].target == j){
			return &(eij[k]);
		}
	}
	return NULL;
}

// Dijkstra
typedef struct{
	int number_of_nodes;
	double *dist;
	int   *pred;
	char  *done;
	Heap  heap;
} Dijkstra;

void dijkstra_init(Dijkstra *dijkstra, Graph *G){
	dijkstra->number_of_nodes = G->number_of_nodes;
	
	// memory allocation
	dijkstra->dist = (double*)malloc(sizeof(double) * (G->number_of_nodes + 1));
	dijkstra->pred = (int*  )malloc(sizeof(int  ) * (G->number_of_nodes + 1));
	dijkstra->done = (char* )malloc(sizeof(char ) * (G->number_of_nodes + 1));
	heap_init(G->number_of_nodes, &(dijkstra->heap));
}

void dijkstra_free(Dijkstra *dijkstra){
	free(dijkstra->dist);
	free(dijkstra->pred);
	free(dijkstra->done);
	heap_free(&dijkstra->heap);
}

void dijkstra_reset(Dijkstra *dijkstra){
	int i;
	for(i=0; i < (dijkstra->number_of_nodes + 1); i++){
		dijkstra->dist[i] = INFINITY; // LARGE NUMBER
		dijkstra->pred[i] = -1;       // INVALID INDEX
		dijkstra->done[i] = 0;        // FALSE
	}
	dijkstra->heap.len = 0;
}

void dijkstra_print_status(Dijkstra *dijkstra){
	int i;
	printf("Dijkstra:\n");
	printf(" pred: ");
	for(i = 0; i <= dijkstra->number_of_nodes; i++){
		printf("(% d,% 4d) ", i, dijkstra->pred[i]);
	}
	printf("\n done: ");
	for(i = 0; i <= dijkstra->number_of_nodes; i++){
		printf("(% d,% 4d) ", i, dijkstra->done[i]);
	}
	printf("\n dist: ");
	for(i = 0; i <= dijkstra->number_of_nodes; i++){
		printf("(% d,% 4.3g) ", i, dijkstra->dist[i]);
	}
	printf("\n");
}

void dijkstra_apply(Dijkstra *dijkstra, Graph *G, int s){
	double *dist = dijkstra->dist;
	int   *pred = dijkstra->pred;
	char  *done = dijkstra->done;
	Heap  *heap = &(dijkstra->heap);
	Edge  *edges;
	
	double dist_sv, dist_svu;
	int   i, v, u;
	size_t nedges;
	
	// printf("\n** Starting dijkstra **\n");
	dijkstra_reset(dijkstra);
	// dijkstra_print_status(dijkstra);
	
	dist[s] = 0;
	pred[s] = s;
	heap_push(heap, s, 0);
	while(heap->len > 0){
		heap_pop(heap, &v, &dist_sv);
		// printf("Exploring node: %d, dist: %g\n", v, dist_sv);
		graph_vertex_edges(G, v, &edges, &nedges);
		for(i = 0; i < nedges; i++){
			u = edges[i].target;
			dist_svu = dist_sv + edges[i].weight;
			// printf(" node: %d, dist: %g\n", u, dist_svu);
			if( dist_svu < dist[u] ){
				dist[u] = dist_svu;
				pred[u] = v;
				// printf("Update dist and pred of node %d\n",u);
				if(!done[u]){
					heap_push(heap, u, dist_svu);
				}
			}
		}
		done[v] = 1;
		// dijkstra_print_status(dijkstra);
	}
}

// MatODEdge
typedef struct {
	int source;
	int target;
	double vol;
	char is_ok;
} MatODEdge;

void matodedge_read_csv(char *csv_file_name, size_t *number_of_edges, MatODEdge **edges) {
	char * line = NULL;
	size_t len = 0, nlines = 0;
	ssize_t read;
	FILE *fid = fopen(csv_file_name, "r");
	double vol;
	int source, target;

	if (fid == NULL) {
		printf("The file %s could not be opened.\n", csv_file_name);
		exit(EXIT_FAILURE);
	}

	// memory allocation (counting the file number of lines)
	while ((read = getline(&line, &len, fid)) != -1) {
		nlines++;
	}
	*number_of_edges = nlines - 1;
	*edges = (MatODEdge*) malloc(sizeof(MatODEdge) * (*number_of_edges));

	printf("\nReading MatOD file: %s\n", csv_file_name);
	rewind(fid);
	// skipping file header
	read = getline(&line, &len, fid);
	nlines = 0;
	while ((read = getline(&line, &len, fid)) != -1) {
		if (sscanf(line, "%d %d %lf\n", &source, &target, &vol) != 3) {
			printf("   Line[%zu] %s could not be read.\n", nlines + 1, line);
			exit(EXIT_FAILURE);
		}
		(*edges)[nlines].source = source;
		(*edges)[nlines].target = target;
		(*edges)[nlines].vol    = vol;

		nlines++;
	}

	fclose(fid);
	if (line){
		free(line);
	}
	printf("   #Edges : %zu\n", *number_of_edges);
}

void matodedge_write_csv(char *csv_file_name, MatODEdge *edges, size_t number_of_edges){
	FILE *fid = fopen(csv_file_name, "w");
	printf("Generating a new matod file: %s\n", csv_file_name);
	if(fid == NULL){
		printf("The file %s could not be created.\n", csv_file_name);
		exit(EXIT_FAILURE);
	}
	fprintf(fid, "o d flow\n");
	int k;
	for(k = 0; k < number_of_edges; k++){
		fprintf(fid, "%d %d %g\n", edges[k].source, edges[k].target, edges[k].vol);
	}
	fclose(fid);
	printf("   Exiting\n");
	exit(EXIT_SUCCESS);
}

void matodedge_print_array(MatODEdge *edges, size_t number_of_edges) {
	int i;
	printf("MatODEdges:\n");
	printf("                  source   target     vol\n");
	for (i = 0; i < 5; i++) {
		printf("[Line %08d] % 8d % 8d %8.2f\n", i + 2, edges[i].source, edges[i].target, edges[i].vol);
	}
	printf("[..........]   ...  ....  ....\n");
	for (i = number_of_edges - 5; i < number_of_edges; i++) {
		printf("[Line %08d] % 8d % 8d %8.2f\n", i + 2, edges[i].source, edges[i].target, edges[i].vol);
	}
}

void matodedge_sort_by_source_target_indices(MatODEdge *edge, size_t number_of_edges){
	printf("   Sorting MatODEdge\n");

	MatODEdge swap; // swap
	int i, j, k;
	char is_ok = 1;
	// using bubble sort
	for(i = 0; i < number_of_edges; i++){
		k = i;
		swap = edge[i];
		if(i % 100 == 0){
			printf("\r      Completed %5.2f%%", (100.0 * i) / number_of_edges);
			fflush(stdout);
		}
		for(j = i - 1; j >= 0; j--){
			if(swap.source  > edge[j].source ||
			  (swap.source == edge[j].source && swap.target > edge[j].target)){
				break;
			}else{
				is_ok = 0;
				k = j;
				edge[j+1] = edge[j];
			}
		}
		edge[k] = swap;
	}
	printf("\n");
	if(is_ok == 0){
		matodedge_write_csv("matod_sorted.txt", edge, number_of_edges);
	}
}

// MatOD (CSR)
typedef struct{
	size_t number_of_nodes;
	size_t number_of_edges;
	size_t number_of_sources;
	int *sources;
	int *i;
	int *j;
	MatODEdge *eij;
} MatOD;

void matod_init(MatOD *G, MatODEdge *edges, size_t number_of_edges){
	printf("Creating MatOD.\n");
	
	int i, j, nid, source;
	int max_nid = INT_MIN, min_nid = INT_MAX;
	
	matodedge_sort_by_source_target_indices(edges, number_of_edges);
	
	// memory allocation
	printf("  Memory allocation\n");
	for(i = 0; i < number_of_edges; i++){
		nid = edges[i].source > edges[i].target ? edges[i].source : edges[i].target;
		if( nid > max_nid ) max_nid = nid;
		if( nid < min_nid ) min_nid = nid;
	}
	G->i = (int *) malloc(sizeof(int) * (max_nid + 2)); // accessed using one-based index
	G->j = (int *) malloc(sizeof(int) * number_of_edges);
	for(i = 0; i < (max_nid + 2); i++) G->i[i] = 0;     // cleanup memory 
	
	// setup using CSR
	nid = min_nid;
	for(i = 0; i < number_of_edges; i++){
		G->j[i] = edges[i].target;
		source = edges[i].source;
		if(source != nid){
			for(j = nid + 1; j <= source; j++){
				G->i[j] = i;
			}
			nid = source;
		}
	}
	for(j = nid + 1; j <= (max_nid + 1); j++){
		G->i[j] = number_of_edges;
	}
	
	G->number_of_edges = number_of_edges;
	G->number_of_nodes = max_nid;
	G->eij = edges;
	
	G->sources = (int*) malloc(sizeof(int) * (G->number_of_nodes + 1));
	for(i = j = 0; j <= max_nid; j++){
		if(G->i[j+1] - G->i[j] > 0){
			G->sources[i++] = j;
		}
	}
	G->number_of_sources = i;
}

void matod_print(MatOD *G){
	int i, imin, imax;
	MatODEdge *edges = G->eij;
	printf("MatOD: \n");
	printf("  #Edges  : %zu\n", G->number_of_edges);
	printf("  #Nodes  : %zu\n", G->number_of_nodes);
	printf("  #Sources: %zu\n      ", G->number_of_sources);
	if(G->number_of_sources < 10){
		for (i = 0; i < G->number_of_sources; i++) {
			printf("%d ", G->sources[i]);
		}
	}else{
		imax = G->number_of_sources < 5 ? G->number_of_sources: 5;
		for (i = 0; i < imax; i++) {
			printf("%d ", G->sources[i]);
		}
		printf(" ... ");
		imin = G->number_of_sources < 5 ? 0: G->number_of_sources - 5;
		for (i = imin; i < G->number_of_sources; i++){
			printf("%d ", G->sources[i]);
		}
	}
	printf("\nsource   target     vol\n");
	for (i = 0; i < 5; i++) {
		printf("%6d % 8d %7.2f\n", edges[i].source, edges[i].target, edges[i].vol);
	}
	printf("     ...  ....  ....\n");
	for (i = G->number_of_edges - 5; i < G->number_of_edges; i++) {
		printf("%6d % 8d %7.2f\n", edges[i].source, edges[i].target, edges[i].vol);
	}
}

void matod_vertex_edges(MatOD *G, int v, MatODEdge **edges, size_t *nedges){
	*nedges = G->i[v + 1] - G->i[v]; 
	*edges  = &(G->eij[G->i[v]]); 
}

void matod_clean(MatOD *M, Graph *G){
	printf("Cleaning MatOD file\n");
	int j, k;
	MatODEdge *travels = M->eij;
	char is_ok = 1;
	
	printf("   Cleaning invalid nodes\n");
	for(k = 0; k < M->number_of_edges; k++){
		if(travels[k].source >= G->min_nid && travels[k].source <= G->max_nid &&
		   travels[k].target >= G->min_nid && travels[k].target <= G->max_nid
		){
			travels[k].is_ok = 1;
		}else{
			is_ok = 0;
			travels[k].is_ok = 0;
		}
	}
	
	printf("   Cleaning unreachable pairs\n");
	clock_t tic, toc;
	int source, target;
	Dijkstra dijkstra;
	dijkstra_init(&dijkstra, G);
	size_t ntravels;
	tic = clock();
	for(k = 0; k < M->number_of_sources; k++){
		source = M->sources[k];
		// printf("      source: %d\n", source);
		if(source >= G->min_nid && source <= G->max_nid){
			dijkstra_apply(&dijkstra, G, source);
		}
		matod_vertex_edges(M, source, &travels, &ntravels);
		// printf("      ntravels: %zu\n", ntravels);
		for(j = 0; j < ntravels; j++){
			target = travels[j].target;
			if(travels[j].is_ok && (dijkstra.dist[target] == INFINITY)){
				is_ok = 0;
				travels[j].is_ok = 0;
				// printf("      Removing pair: (%d, %d)\n", source, target);
			}
		}
		if(k % 100 == 0){
			printf("\r      Completed %5.2f%%", (100.0 * k) / M->number_of_sources);
			fflush(stdout);
		}
	}
	printf("\r      Completed   100%%\n");
	toc = clock();
	printf("      Elapsed time: %3.2g secs\n", ((double)(toc - tic))/CLOCKS_PER_SEC);
	
	// creating a new matod file
	if(is_ok == 0){
		travels = M->eij;
		for(j = k = 0; k < M->number_of_edges; k++){
			if(travels[k].is_ok){
				travels[j++] = travels[k];
			}
		}
		matodedge_write_csv("matod_sorted_cleaned.txt", travels, j);
	}else{
		printf("   No invalid MatODEdge has been found.\n");
	}
}

// BPR
void vecdot(double *dot, const double *u, const double *v, size_t n){
	int k;
	(*dot) = 0.0;
	for(k = 0; k < n; k++){
		(*dot) += u[k] * v[k];
	}
}

// x = y
void veccpy(double *x, const double *y, size_t n){
	int k;
	for(k = 0; k < n; k++){
		x[k] = y[k];
	}
}

// x = x + a * y
void vecadd(double *x, const double *y, double a, size_t n){
	int k;
	for(k=0;k<n;k++){
		x[k] += a * y[k];
	}
}

void bpr(const Graph *G, const double *x, double *f, double *g){
	Edge *edge = G->eij;
	int i;
	double y;
	*f = 0.0;
	for(i = 0; i < G->number_of_edges; i++){
		y   = pow(x[i] / edge[i].capacity, 4.0);
		*f += (edge[i].cost_time * x[i]) * (1.0 + 0.03 * y);
		g[i] = edge[i].cost_time * (1.0 + 0.15 * y);
	}
}

int bpr_linesearch(const Graph *G, const double *x, const double *d, double *y, double *f, double *g){
	int niter = 0, maxit = 100;
	size_t n = G->number_of_edges;
    double stp = 1.0;
    double finit, dginit = 0., dgtest;
    const double dec = 0.9, min_step = 1E-8, max_step = 1.0, ftol = 0.2;

	/* Compute the initial gradient in the search direction. */
	bpr(G, x, f, g);
    vecdot(&dginit, g, d, n);

    /* Make sure that y points to a descent direction. */
    if (dginit > 0) {
        printf("The vector d is not a descent direction.\n");
		exit(EXIT_FAILURE);
    }

    /* The initial value of the objective function. */
    finit  = *f;
    dgtest = ftol * dginit;

	// printf("\n       n     step   fobj\n");
	// printf("   %5d %5.3E %5.3E\n",niter,0.0,*f);
    for (;;) {
		veccpy(y, x, n);
        vecadd(y, d, stp, n);  // update x

        /* Evaluate the function and gradient values. */
        bpr(G, y, f, g);

        ++niter;

		// printf("   %5d %5.3E %5.3E\n",niter,stp,*f);
    	
        if (*f > finit + stp * dgtest) {
            stp *= dec;
        } else {
			return niter;
        }

        if (stp < min_step){
            return -1;
        }else if(stp > max_step){
			return -2;
		}else if(niter > maxit) {
			return -3;
		}
    }

    return 0;
}

// shortestpaths
void shortestpaths(Graph *G, MatOD *M, Dijkstra *dijkstra, double *x){
    int i, j, source, target, pred;
	double vol;
	
	// set x = zeros
	for(i = 0; i < G->number_of_edges; i++){
		x[i] = 0.0;
	}
	Edge *edge;
	MatODEdge *travel;
	size_t ntravel;
	for(i = 0; i < M->number_of_sources; i++){
		source = M->sources[i];
		dijkstra_apply(dijkstra, G, source);
		matod_vertex_edges(M, source, &travel, &ntravel);
		for(j = 0; j < ntravel; j++){
			vol    = travel[j].vol;
			target = travel[j].target;
			while(target != source){
				pred = dijkstra->pred[target];
				edge = graph_edge(G, pred, target);
				x[edge->xid] += vol;
				target = pred;
			}
		}
	}
}

// xsol file
void xsol_write_csv(const char *filename, Graph *G, double *x, double *g){
	FILE *fid = fopen(filename, "w");
	if(fid == NULL){
		printf("The file %s could not be opened.\n", filename);
		exit(EXIT_FAILURE);
	}
	
	fprintf(fid, "eid source target cap ftt vol cost\n");
	int k;
	Edge eij;
	for(k = 0; k < G->number_of_edges; k++){
		eij = G->eij[k];
		fprintf(fid, "%d %d %d %g %g %g %g\n", eij.eid, eij.source, eij.target, eij.capacity, eij.cost_time, x[k], x[k] * g[k]);
	}
	fclose(fid);
}
char xsol_read_csv(const char *csv_file_name, double *x){
	FILE *fid = fopen(csv_file_name, "r");
	if(fid == NULL){
		printf("The file %s could not be opened.\n", csv_file_name);
		return 0;
	}

	char * line = NULL;
	size_t len = 0, nlines = 0;
	ssize_t read;
	double cap, ftt, cost, vol;
	int eid, source, target;
	if (fid == NULL) {
		printf("The file %s could not be opened.\n", csv_file_name);
		exit(EXIT_FAILURE);
	}

	// memory allocation (counting the file number of lines)
	printf("\nReading xsol file: %s\n", csv_file_name);
	// skipping file header
	read = getline(&line, &len, fid);
	nlines = 0;
	while ((read = getline(&line, &len, fid)) != -1) {
		if (sscanf(line, "%d %d %d %lf %lf %lf %lf\n", &eid, &source, &target, &cap, &ftt, &vol, &cost) != 7) {
			printf("   Line[%zu] %s could not be read.\n", nlines + 1, line);
			exit(EXIT_FAILURE);
		}
		x[nlines] = vol;
		
		nlines++;
	}

	fclose(fid);
	if (line){
		free(line);
	}
	
	return 1;
}

// check routines
int check_heap(){
	Heap heap;
	heap_init(10, &heap);
	heap_push(&heap, 5, 8);
	heap_push(&heap, 2, 7);
	heap_push(&heap, 6, 4);
	heap_push(&heap, 1, 9);
	heap_push(&heap, 7, 3);
	heap_push(&heap, 3, 2);
	heap_push(&heap, 4, 1);
	heap_print(&heap);

	int nid;
	double cost;
	heap_pop(&heap, &nid, &cost);
	printf("nid: %d cost: %g\n",nid, cost);
	heap_pop(&heap, &nid, &cost);
	printf("nid: %d cost: %g\n",nid, cost);
	heap_pop(&heap, &nid, &cost);
	printf("nid: %d cost: %g\n",nid, cost);
	heap_print(&heap);
	
	heap_free(&heap);
	
	return EXIT_SUCCESS;
}

int check_dijkstra(){
	// read edges
	Edge *edges;
	size_t number_of_edges;
	edge_read_csv("../instances/smallA_edges.txt", &number_of_edges, &edges);
	edge_print_array(edges, number_of_edges);
	
	// create graph
	Graph G;
	int k;
	graph_init(&G, edges, number_of_edges);
	graph_print(&G);
	for(k = 0; k < G.number_of_edges; k++){
		G.eij[k].weight = G.eij[k].cost_time;
	}
	
	Dijkstra dijkstra;
	dijkstra_init(&dijkstra, &G);
	dijkstra_apply(&dijkstra, &G, 1);
	dijkstra_apply(&dijkstra, &G, 3);
	
	free(edges);
	graph_free(&G);
	dijkstra_free(&dijkstra);
	return EXIT_SUCCESS;
}

void check_opt(Graph *G, MatOD *M, Dijkstra *dijkstra, double *x, double *f, double *g){
    int j, k, s;
	
	printf("\nOptimality analysis: \n");
    clock_t tic = clock();
	
    // update cost
    bpr(G, x, f, g);
    for(k = 0; k < G->number_of_edges; k++){
		G->eij[k].weight = g[k];
	}

    // cost per path
	MatODEdge *travels;
	size_t ntravels;
    double cost_per_path = 0.0;
    for(k = 0; k < M->number_of_sources; k++){
		s = M->sources[k];
        dijkstra_apply(dijkstra, G, s);
        matod_vertex_edges(M, s, &travels, &ntravels);
		for(j = 0; j < ntravels; j++){
            cost_per_path += dijkstra->dist[travels[j].target] * travels[j].vol;
		}
	}
	
    // cost per edge
    double cost_per_edge = 0.0;
	for(k = 0; k < G->number_of_edges; k++){
		cost_per_edge += g[k] * x[k];
	}
	
    // optimality gap
    double gap = 1 - cost_per_path / cost_per_edge;
    printf("   Cost per path: %E\n", cost_per_path);
    printf("   Cost per edge: %E\n", cost_per_edge);
    printf("   Gap .........: %E\n", gap);
    printf("   Elapsed time during check_optimality %.3f seconds\n", toc(tic));
}

int leblanc_apply(int argc, char **argv) {
	// read nodes
	// Node *nodes;
	// int number_of_nodes;
	// node_read_csv("../instances/dial_nodes.txt", &number_of_nodes, &nodes);
	// node_print_array(number_of_nodes, nodes);
	
	char filename[256];
	
	// read edges
	sprintf(filename, "../instances/%s_edges_algbformat.txt", argv[1]);
	Edge *edges;
	size_t number_of_edges;
	edge_read_csv(filename, &number_of_edges, &edges);
	edge_print_array(edges, number_of_edges);
	
	// create network graph
	Graph G;
	graph_init(&G, edges, number_of_edges);
	size_t n = G.number_of_edges;
	
	// set init edge weight
	int k;
	for(k = 0; k < n; k++){
		G.eij[k].weight = G.eij[k].cost_time;
	}

	// read matod edges (travels)
	sprintf(filename, "../instances/%s_matod.txt", argv[1]);
	MatODEdge *travels;
	size_t	number_of_travels;
	matodedge_read_csv(filename, &number_of_travels, &travels);
	// matodedge_read_csv("matod_sorted.txt", &number_of_travels, &travels);
	matodedge_print_array(travels, number_of_travels);
	
	// create matod 
	MatOD M;
	matod_init(&M, travels, number_of_travels);
	matod_print(&M);
	matod_clean(&M, &G);
	
	// create Dijkstra
	Dijkstra dijkstra;
	dijkstra_init(&dijkstra, &G);
	
	// set initial x
	printf("Set initial x\n");
	clock_t tic;
	double *x = (double*) malloc(sizeof(double) * n);
	tic = clock();
	sprintf(filename, "../instances/%s_xsol.txt", argv[1]);
	if(!xsol_read_csv(filename, x)) shortestpaths(&G, &M, &dijkstra, x);	
	printf("   Elapsed time: %3.2g secs\n", toc(tic));
	
	// initial fobj value
	double *g = (double *) malloc(sizeof(double*) * n);
	double f;
	tic = clock();
	bpr(&G, x, &f, g);
	printf("fobj(x_start) = %.8E calculated in %3.2f seconds", f, toc(tic));
	
	double xtol  = 0.01, fx, fy, dx, dy, df;
    int niter = 0, niter_linesearch;
    char done    = 0;
    size_t maxit = 1000;
    clock_t tstart = clock();
	double *y = (double*) malloc(sizeof(double) * n);
	double *d = (double*) malloc(sizeof(double) * n);
    while(!done){
        tic = clock();
		
        // update cost
        bpr(&G, x, &fx, g);
        for(k=0;k<n;k++){
            G.eij[k].weight=g[k];
		}
		
        // update direction
        shortestpaths(&G,&M,&dijkstra,d);
        vecadd(d,x,-1.0,n);
		
        // solve line search problem bpr(ftt, cap, x + a * d)
		niter_linesearch = bpr_linesearch(&G, x, d, y, &fy, g);
		
        // stop criterion
        // dx = np.max(np.abs(x-y)/(np.abs(x)+1))
		dx = 0.0;
		for(k=0;k<n;k++){
			dy = fabs(x[k]-y[k]) / (fabs(x[k]) + 1);
			if(dx < dy) dx = dy;
		}
        df = (fx - fy) / fx;
        niter++;
        done = dx < xtol || niter > maxit || df < 1E-4;

        // update x
        veccpy(x,y,n);
       
        if(niter % 20 == 1){
            printf("\n  niter_out     dx            fobj           df        niter_in   itime(sec)\n");
            printf("---------------------------------------------------------------------\n");
		}
		printf(" %5d       %5.3E     %5.3E   %5.3E    %5d         %.3f\n", niter, dx, fy, df, niter_linesearch, toc(tic));
	}	
    printf("\nTotal elapsed time %.3f hours", toc(tstart) / 3600);
	
	sprintf(filename, "../instances/%s_xsol.txt", argv[1]);
	xsol_write_csv(filename, &G, x, g);
	
	check_opt(&G, &M, &dijkstra, x, &fx, g);
	
	// free(nodes);
	// free(edges);
	// free(matod);
	
	// check_dijkstra();
	// matod_clean();
	
	return EXIT_SUCCESS;
}

// openmp course task01
void task01_hello(){
	#pragma omp parallel
	{
		int ID = omp_get_thread_num();
		printf("hello(%d)", ID);
		printf(" world(%d)\n", ID);
	}
}

// openmp course task02
void task02_integral_seq(){
	// integrates
	// int_0^1 4.0 / (1+x^2) dx = \pi
	static long num_steps =  1000000000;
	double step = 1.0 / (double) num_steps;
	double tic = omp_get_wtime();
	int i; double x, pi, sum = 0.0;
	step = 1.0 / (double) num_steps;
	for(i = 0; i < num_steps; i++){
		x = (i+0.5)*step;
		sum += 4.0 /(1.0+x*x);
	}
	double telapsed = omp_get_wtime() - tic;
	pi = step * sum;
	printf("pi = %f\n", pi);
	printf("TElapsed %g secs\n", telapsed);
}
void task02_integral_parallel(int num_threads){
	// integrates
	// int_0^1 4.0 / (1+x^2) dx = \pi
	static long num_steps = 1000000000;
	double step = 1.0 / (double) num_steps;
	
	omp_set_dynamic(0);
	omp_set_num_threads(num_threads);
	int work = num_steps / num_threads;
	double pi=0.0;
	int j;
	double *sum_local = (double*) malloc(num_threads * sizeof(double));
	// printf("num_threads: %d\n", num_threads);
	// printf("work: %d\n", work);
	double tic = omp_get_wtime();
	#pragma omp parallel
	{
		int ID   = omp_get_thread_num();
		double sum = 0.0;
		// printf("Thread(%d)\n", ID);
		int imin = ID * work;
		int imax = imin + work;
		// printf("imin: %d, imax: %d\n", imin, imax);
		int i; 
		double x;
		for(i = imin; i < imax; i++){
			x = (i+0.5) * step;
			sum += 4.0 /(1.0+x*x);
		}
		sum_local[ID] = sum;
	}
	for(j = 0; j < num_threads; j++){
		pi += step * sum_local[j];
	}
	double telapsed = omp_get_wtime() - tic;
	
	printf("pi: %f NumProc: %d TElapsed: %3.2gs\n", pi, num_threads, telapsed);
}

void task03_integrap_parallel_optimized(int num_threads){
	// integrates
	// int_0^1 4.0 / (1+x^2) dx = \pi
	static long num_steps = 1000000000;
	double step = 1.0 / (double) num_steps;

	omp_set_num_threads(num_threads);
	double pi=0.0;
	double tic = omp_get_wtime();
	#pragma omp parallel
	{
		int i, id = omp_get_thread_num(), slice = omp_get_num_threads();
		double x, sum_local = 0.0;
		if(id == 0){
			num_threads = slice;
		}
		for(i = id; i < num_steps; i+=slice){
			x = (i+0.5) * step;
			sum_local += 4.0 /(1.0+x*x);
		}
		#pragma omp atomic
		pi += step * sum_local;
	}

	double telapsed = omp_get_wtime() - tic;

	printf("pi: %f NumProc: %d TElapsed: %3.2gs\n", pi, num_threads, telapsed);
}

int main(int argc, char **argv){
	task02_integral_seq();
	int num_threads;
	for(num_threads=1;num_threads<8;num_threads++){
		task03_integrap_parallel_optimized(num_threads);
	}
	
	return EXIT_SUCCESS;
}
