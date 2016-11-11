/*
 * leblanc.c
 *
 *  Created on: Nov 9, 2016
 *      Author: michael
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <limits.h>

// Node
typedef struct {
	int nid;
	float lon;
	float lat;
} Node;

void node_read_csv(char *csv_file_name, int *number_of_nodes, Node **nodes) {
	char * line = NULL;
	size_t len = 0, nlines = 0;
	ssize_t read;
	FILE *fid = fopen(csv_file_name, "r");
	float lon, lat;
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
		if (sscanf(line, "%d %f %f\n", &nid, &lat, &lon) != 3) {
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
	float capacity;
	float cost_time;
	float weight;
} Edge;

void edge_read_csv(char *csv_file_name, int *number_of_edges, Edge **edges) {
	char * line = NULL;
	size_t len = 0, nlines = 0;
	ssize_t read;
	FILE *fid = fopen(csv_file_name, "r");
	float capacity, cost_time;
	int eid, source, target;

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
		if (sscanf(line, "%d %d %d %f %f\n", &eid, &source, &target, &capacity,
				&cost_time) != 5) {
			printf("   Line[%zu] %s could not be read.\n", nlines + 1, line);
			exit(EXIT_FAILURE);
		}
		(*edges)[nlines].eid = eid;
		(*edges)[nlines].source = source;
		(*edges)[nlines].target = target;
		(*edges)[nlines].capacity = capacity;
		(*edges)[nlines].cost_time = cost_time;

		nlines++;
	}

	fclose(fid);
	if (line)
		free(line);

	printf("   #Edges : %d\n", *number_of_edges);
}

void edge_print_array(int number_of_edges, Edge *edges) {
	int i;
	printf("               eid   source   target capacity cost_time\n");
	for (i = 0; i < 5; i++) {
		printf("[Line %05d] % 5d % 6d % 8d %9.2f %7.2f\n", i + 2, edges[i].eid,
				edges[i].source, edges[i].target, edges[i].capacity,
				edges[i].cost_time);
	}
	printf("[..........]   ...  ....  ....\n");
	for (i = number_of_edges - 5; i < number_of_edges; i++) {
		printf("[Line %05d] % 5d % 6d % 8d %9.2f %7.2f\n", i + 2, edges[i].eid,
				edges[i].source, edges[i].target, edges[i].capacity,
				edges[i].cost_time);
	}
}

// Returns one if the x index is less than the y one, zero otherwise.
int edge_is_source_target_indices_less_than(Edge *x, Edge *y){
	if(x->source < y->source) 1;
	if(x->source > y->source) 0;
	return x->target < y->target;
}

void edge_sort_by_source_target_indices(Edge *edge, int number_of_edges){
	Edge swap; // swap
	int i, j;
	// using bubble sort
	for(i = 0; i < number_of_edges; i++){
		for(j = i - 1; j >= 0; j--){
			if(edge_is_index_less_than(edge[i], edge[j])){
				// swap
				swap = edge[i];
				edge[i] = edge[j];
				edge[j] = swap;
			}else{
				break;
			}
		}
	}
}

// MatODRow
typedef struct {
	int o;
	int d;
	float flow;
} MatODRow;

void matod_read_csv(char *csv_file_name, int *number_of_rows, MatODRow **rows) {
	char * line = NULL;
	size_t len = 0, nlines = 0;
	ssize_t read;
	FILE *fid = fopen(csv_file_name, "r");
	float flow;
	int o, d;

	if (fid == NULL) {
		printf("The file %s could not be opened.\n", csv_file_name);
		exit(EXIT_FAILURE);
	}

	// memory allocation (counting the file number of lines)
	while ((read = getline(&line, &len, fid)) != -1) {
		nlines++;
	}
	*number_of_rows = nlines - 1;
	*rows = (MatODRow*) malloc(sizeof(MatODRow) * (*number_of_rows));

	printf("\nReading MatOD file: %s\n", csv_file_name);
	rewind(fid);
	// skipping file header
	read = getline(&line, &len, fid);
	nlines = 0;
	while ((read = getline(&line, &len, fid)) != -1) {
		if (sscanf(line, "%d %d %f\n", &o, &d, &flow) != 3) {
			printf("   Line[%zu] %s could not be read.\n", nlines + 1, line);
			exit(EXIT_FAILURE);
		}
		(*rows)[nlines].o = o;
		(*rows)[nlines].d = d;
		(*rows)[nlines].flow = flow;

		nlines++;
	}

	fclose(fid);
	if (line)
		free(line);

	printf("   #Rows : %d\n", *number_of_rows);
}

void matod_print_array(int number_of_rows, MatODRow *matod) {
	int i;
	printf("                 o      d     flow\n");
	for (i = 0; i < 5; i++) {
		printf("[Line %05d] % 5d % 6d %8.2f\n", i + 2, matod[i].o, matod[i].d, matod[i].flow);
	}
	printf("[..........]   ...  ....  ....\n");
	for (i = number_of_rows - 5; i < number_of_rows; i++) {
		printf("[Line %05d] % 5d % 6d %8.2f\n", i + 2, matod[i].o, matod[i].d, matod[i].flow);
	}
}

// Heap
typedef struct{
	int   *nid; // array of nodes' ids
	float *cost;
	size_t len;
	size_t capacity;
} Heap;

void heap_init(size_t capacity, Heap *heap){
	heap->nid = (int*) malloc(sizeof(int) * capacity);
	heap->cost = (float*) malloc(sizeof(float) * capacity);
	heap->len = 0;
	heap->capacity = capacity;
}

void heap_push(Heap *heap, int nid, float cost){
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

void heap_pop(Heap *heap, int *nid, float *cost){
	// set output values
	*nid = heap->nid[0];
	*cost = heap->cost[0];

	// update heap - move the last node to the top
	heap->nid[0] = heap->nid[heap->len - 1];
	heap->cost[0] = heap->cost[heap->len - 1];
	heap->len--;

	int node = 0, child, node_nid;
	float node_cost;
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
} Graph;

void graph_init(Graph &G, Edge *edges, int number_of_edges){
	int i, j, nid, nelem, max_nid, min_nid, source;
	
	// memory allocation
	for(i = 0; i < number_of_edges; i++){
		nid = edges[i]->source > edges[i]->target ? source : target;
		if( nid > max_nid ) max_nid = nid;
		if( nid < min_nid ) min_nid = nid;
	}
	G->i = (int *) malloc(sizeof(int) * (max_nid + 2)); // accessed using one-based index
	G->j = (int *) malloc(sizeof(int) * number_of_edges);
	for(i = 0; i < (max_nid + 2); i++) G->i[i] = 0;     // cleanup memory 
	
	// setup using CSR
	edge_sort_by_source_target_indices(edges, number_of_edges);
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
}

void graph_free(Graph *G){
	free(G->i);
	free(G->j);
}

void graph_neighs(Graph *G, int i, int **neighs, int *nelems){
	*nelems = G->i[i + 1] - G->i[i]; 
	*neighs = &(G->j[G->i[i]]); 
}

void graph_vertex_edges(Graph *G, int v, Edge **edges, int *nedges){
	*nedges = G->i[v + 1] - G->i[v]; 
	*edges  = &(G->eij[G->i[v]]); 
}

// Dijkstra
typedef struct{
	int number_of_nodes;
	float *dist;
	int   *pred;
	char  *done;
	Heap  heap;
} Dijkstra;

void dijkstra_init(Dijkstra *dijkstra, Graph *G){
	int i;
	dijkstra->number_of_nodes = G->number_of_nodes;
	// memory allocation
	dijkstra->dist = (float*)malloc(sizeof(float) * G->number_of_nodes);
	dijkstra->pred = (float*)malloc(sizeof(float) * G->number_of_nodes);
	dijkstra->done = (float*)malloc(sizeof(float) * G->number_of_nodes);
	heap_init(G->number_of_nodes, &(dijkstra->heap));
}

void dijkstra_free(Dijkstra *dijkstra){
	free(&dijkstra->dist);
	free(&dijkstra->pred);
	free(&dijkstra->done);
	heap_free(&dijkstra->heap);
}

void dijkstra_reset(Dijkstra *dijkstra){
	int i;
	for(i=0; i < dijkstra->number_of_nodes; i++){
		dijkstra->dist[i] = INFINITY; // LARGE NUMBER
		dijkstra->pred[i] = -1;       // INVALID INDEX
		dijkstra->done[i] = 0;        // FALSE
	}
	dijkstra->heap.len = 0;
}

void dijkstra_apply(Dijkstra &dijkstra, Graph *G, int s){
	float *dist = dijkstra->dist;
	int   *pred = dijkstra->pred;
	char  *done = dijkstra->done;
	Heap  *heap = &(dijkstra->heap);
	Edge  *edges;
	
	float dist_sv, dist_svu;
	int   i, v, u, *neighs, nedges;
	
	dijkstra_reset(dijkstra);
	dist[s] = 0;
	pred[s] = s;
	heap_push(heap, s, 0);
	while(heap->len > 0){
		heap_pop(heap, &v, &dist_sv);
		graph_neighs_edges(G, v, &edges, &nedges);
		for(i = 0; i < nedges; i++){
			u = edges[i].target;
			dist_svu = edges[i].weight;
			if( dist_svu < dist_u ){
				dist[u] = dist_svu;
				pred[u] = v;
				if(!done[u]){
					heap_push(heap, u, dist_svu);
				}
			}
		}
		done[v] = 1;
	}
}

int main(int argc, char **argv) {
	Node *nodes;
	Edge *edges;
	MatODRow *matod;
	int number_of_nodes, 
	    number_of_edges, 
		number_of_travels;
	
	Dijkstra dijkstra;

	// read nodes
	node_read_csv("../instances/dial_nodes.txt", &number_of_nodes, &nodes);
	node_print_array(number_of_nodes, nodes);

	// read edges
	edge_read_csv("../instances/dial_edges.txt", &number_of_edges, &edges);
	edge_print_array(number_of_edges, edges);

	// read matod
	matod_read_csv("../instances/dial_od.txt", &number_of_travels, &matod);
	matod_print_array(number_of_travels, matod);

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
	float cost;
	heap_pop(&heap, &nid, &cost);
	printf("nid: %d cost: %g\n",nid, cost);
	heap_pop(&heap, &nid, &cost);
	printf("nid: %d cost: %g\n",nid, cost);
	heap_pop(&heap, &nid, &cost);
	printf("nid: %d cost: %g\n",nid, cost);
	heap_print(&heap);

	free(nodes);
	free(edges);
	free(matod);
	heap_free(&heap);
	return EXIT_SUCCESS;
}
