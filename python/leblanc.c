#include <float.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct Graph {
	unsigned int number_of_nodes;
	// array of nodes unique identification
	unsigned int *nodes; 
	// array of array of nodes neighbors
	unsigned int **neighbors; 
}

typedef struct Node {
	unsigned int nid; // unique identification
	float lon;        // longitude
	float lat;        // latitude
}

typedef struct Nodes{
	unsigned long int length;
	Node *node;
}


void read_nodes(char *fn, Nodes *nodes){
	FILE *fid = fopen(fn, "r");
	int i;
	float fl_nid, fl_lon, fl_lat;
	if(fid != NULL){
		nodes->length = 0;
		// skipping the file header
		fgetline(fid);
		// counting the number of lines
		while(fgetline(fid)){
			nodes->length++;
		}
		// allocating memory
		nodes->node = malloc(sizeof(Node) * nodes->length;
		// rewind to read from the file begining
		rewind(fid);
		// skipping the file header
		fgetline(fid);
		// read file entries
		for(i = 0; i < nodes->length; i++){
			fscanf(fid, "%lf %lf %lf\n", &fl_nid, &fl_lon, &fl_lat);
			nodes->node[i].nid = (unsigned int) fl_nid;
			nodes->node[i].lon = fl_lon;
			nodes->node[i].lat = fl_lat;
		}
		fclose(fid);
	}else{
		printf("The file %s could not be found.\n", fn_nodes);
		return EXIT_FAILURE;
	}
}


typedef struct MatODRow{
	unsigned int o;      // origin node
	unsigned int d;      // destination node
	unsigned float flow; // expected o->d flow 
}

// Origin-Destination Matrix
typedef struct MatOD{
	unsigned int length;  // total number of OD pairs
	MatODRow *row;
}

typedef struct Edge {
	unsigned int eid;
	unsigned int s;
	unsigned int t;
	unsigned float ftt;
	unsigned float cap;
}

typedef struct Edges{
	unsigned long int length;
	Edge *edge;
}

void load_problem(char *fn_nodes, char *fn_edges, char *fn_matod, Nodes *nodes, Edges *edges, MatOD *matod){
	FILE *fid;
	
	printf("Reading nodes\n");
	printf("Reading edges\n");
	fid = fopen(fn_nodes, "r");
	if(fid != NULL){
		
		fclose(fid);
	}else{
		printf("The file %s could not be found.\n", fn_edges);
		return EXIT_FAILURE;
	}
	printf("Reading MatOD\n");
	fid = fopen(fn_nodes, "r");
	if(fid != NULL){
		fclose(fid);
	}else{
		printf("The file %s could not be found.\n", fn_nodes);
		return EXIT_FAILURE;
	}
}

void dijkstra(Graph G, int s, float *dist, int *pred){
	char *done;
	int i, j, k, v;
	Heap h;
	
	// memory allocation
	done = (char*) malloc(sizeof(char) * (G.max_vertex_index + 1));
	
	// initializations
	for(i = 0; i < G.number_of_nodes; i++){
		v = G.nodes[i];
		dist[v] = FLT_MAX; // maximum value of float
		pred[v] = 0;
		done[v] = 0;
	}
	
	dist[s] = 0;
	pred[s] = s;
	heap_push(h, 0, s);
	while(h.length > 0){
		heap_pop(h, &dist_sv, &v);
		if( done[v] ) continue;
		neighbors_of_s = G.neighbors[s];
		for(k = 0; k < neighbors_of_s.length; k++){
			u = neighbors_of_s[k];
			dist_svu = dist_sv + G.edges(v,u).weight;
			if(dist_svu < dist[u]){
				dist[u] = dist_svu;
				pred[u] = v;
				heap_push(h, dist_svu, u);
			}
		}
		done[v] = 1;
	}
}