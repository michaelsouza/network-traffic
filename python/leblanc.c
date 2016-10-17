#include <stdlib.h>
#include <stdio.h>
#include <float.h>

typedef struct {
	unsigned int nid; // unique identification
	float lon;        // longitude
	float lat;        // latitude
	void *next;
} Node;

typedef struct {
	size_t length;
	unsigned int max_node_id;
	Node *root;
} Nodes;


typedef struct {
	unsigned int eid;
	unsigned int s;
	unsigned int t;
	float ftt;
	float cap;
	void *next;
} Edge;

typedef struct {
	size_t length;
	Edge *root;
} Edges;


// CSR format
typedef struct {
	size_t number_of_nodes;
	size_t number_of_edges;
	// array of nodes unique identification
	Node *nodes; // pointer to root node
	// array of array of nodes neighbors
	unsigned int **neighs;
	// dist between nodes
	float **dist;
	// number of neighs
	size_t *neighs_length;
	size_t length;
} Graph;

float graph_get_dist(Graph *G, unsigned int u, unsigned int v){
	int i;
	for(i = 0; i < G->neighs_length[u]; i++){
		if(G->neighs[u][i] == v){
			return G->dist[u][i];
		}
	}
	printf("Edge (%u, %u) not found.\n", u, v);
	abort();
}

void graph_set_dist(Graph *G, unsigned int u, unsigned int v,float dist){
	int i;
	for(i = 0; i < G->neighs_length[u]; i++){
		if(G->neighs[u][i] == v){
			G->dist[u][i] = dist;
			return;
		}
	}
	printf("Edge (%u, %u) not found.\n", u, v);
	abort();
}

void create_graph(Graph *G, Nodes nodes, Edges edges){
	Edge *edge;
	int k;
	
	// +1 because the nodes index (nid) might be one-based
	G->length = nodes.max_node_id + 1;
	// memory allocation
	G->dist = malloc(sizeof(float*) * G->length);
	G->neighs = malloc(sizeof(unsigned int*) * G->length);
	G->neighs_length = malloc(sizeof(size_t) * G->length);

	// init
	for(k=0; k < G->length; k++){
		G->neighs_length[k] = 0;
	}

	// creating edges
	for(edge = (Edge*) edges.root; edge != NULL; edge = (Edge*) edge->next){
		G->neighs_length[edge->s]++;
	}

	// memory allocation
	for(k=0; k < G->length; k++){
		// malloc
		G->neighs[k] = malloc(sizeof(unsigned int) * G->neighs_length[k]);
		// reset to use as pointers
		G->neighs_length[k] = 0;
	}
	for(edge = (Edge*) edges.root; edge != NULL; edge = (Edge*) edge->next){
		G->neighs[edge->s][G->neighs_length[edge->s]] = edge->t;
		G->neighs_length[edge->s]++;
	}
}

typedef struct {
	size_t length;
} Heap;

void heap_push(Heap *heap, float value, unsigned int node){

}

void heap_pop(Heap *heap, float *value, unsigned int *node){

}

int read_nodes(char *fn, Nodes *nodes){
	FILE *fid = fopen(fn, "r");
	int i;
	double fl_nid, fl_lon, fl_lat;
	size_t buffer_size = 1024, n;
	char *buffer;
	Node *node, *node_prev;

	if(fid != NULL){
		nodes->length = 0;
		nodes->root = NULL;
		node_prev = NULL;
		// read file entries
		while(getline(&buffer, &buffer_size, fid) > 0){
			sscanf(buffer, "%lf %lf %lf\n", &fl_nid, &fl_lon, &fl_lat);
			// malloc and set current node
			node = malloc(sizeof(Node));
			node->nid = (unsigned int) fl_nid;
			node->lon = fl_lon;
			node->lat = fl_lat;
			node->next = NULL;
			nodes->length++;
			// init
			if(nodes->root == NULL){
				nodes->root = node;
				node_prev = node;
			}
			// update
			node_prev->next = node;
			node_prev = node;
		}
		fclose(fid);
		return EXIT_SUCCESS;
	}else{
		printf("The file %s could not be opened.\n", fn);
		abort();
	}
	return EXIT_FAILURE;
}


typedef struct {
	unsigned int o;  // origin node
	unsigned int d;  // destination node
	float flow;      // expected o->d flow 
} MatODRow;

// Origin-Destination Matrix
typedef struct {
	size_t length;  // total number of OD pairs
	MatODRow *row;
} MatOD;

void dijkstra(Graph *G, unsigned int s, float *dist, unsigned int *pred){
	Heap h;
	char *done;
	unsigned int i, j, k, u, v, *neighs_s;
	size_t neighs_s_length;
	float dist_sv, dist_svu;
	
	// memory allocation
	done = (char*) malloc(sizeof(char) * G->length);
	
	// initializations
	for(i = 0; i < G->length; i++){
		dist[v] = FLT_MAX; // maximum value of float
		pred[v] = 0;
		done[v] = 0;
	}
	
	dist[s] = 0;
	pred[s] = s;
	heap_push(&h, 0, s);
	while(h.length > 0){
		heap_pop(&h, &dist_sv, &v);
		if( done[v] ) continue;
		neighs_s = G->neighs[s];
		neighs_s_length = G->neighs_length[s];
		for(k = 0; k < neighs_s_length; k++){
			u = neighs_s[k];
			dist_svu = dist_sv + graph_get_dist(G,v,u);
			if(dist_svu < dist[u]){
				dist[u] = dist_svu;
				pred[u] = v;
				heap_push(&h, dist_svu, u);
			}
		}
		done[v] = 1;
	}
}

int main(){
	Nodes nodes;
	Edges edges;
	MatOD matod;

	// load problem
	read_nodes("porto_nodes_algbformat.txt", &nodes);

	return EXIT_SUCCESS;
}