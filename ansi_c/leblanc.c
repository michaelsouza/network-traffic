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

	printf("Reading node file: %s\n", csv_file_name);
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

	printf("Reading edge file: %s\n", csv_file_name);
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

	printf("Reading MatOD file: %s\n", csv_file_name);
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


int main(int argc, char *argv) {
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

	free(nodes);
	return EXIT_SUCCESS;
}
