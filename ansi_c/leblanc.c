/*
 * leblanc.c
 *
 *  Created on: Nov 9, 2016
 *      Author: michael
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

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

typedef struct {
	int eid;
	int source;
	int target;
	float capacity;
	float cost_time;
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


typedef struct{
	int *nid; // array of nodes' ids
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

void heap_insertion(Heap *heap, int nid, float cost){
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

int main(int argc, char **argv) {
	Node *nodes;
	Edge *edges;
	MatODRow *matod;
	int number_of_nodes, number_of_edges, number_of_travels;

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
	heap_insertion(&heap, 5, 8);
	heap_insertion(&heap, 2, 7);
	heap_insertion(&heap, 6, 4);
	heap_insertion(&heap, 1, 9);
	heap_insertion(&heap, 7, 3);
	heap_insertion(&heap, 3, 2);
	heap_insertion(&heap, 4, 1);
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
