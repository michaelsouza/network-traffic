# REMEMBER TO SET 
leblanc_openmp: leblanc_openmp.c
	gcc -Wall -Werror -fopenmp leblanc_openmp.c -lm -o leblanc_openmp

leblanc_openmp_valgrind: leblanc_openmp.c
	gcc -pg -Wall -Werror leblanc.c -lm -o leblanc_openmp_valgrind
	valgrind --tool=memcheck --leak-check=yes  --show-reachable=yes ./leblanc_openmp_valgrind sample


leblanc: leblanc.c
	gcc -Wall -Werror leblanc.c -lm -o leblanc
	
leblanc_valgrind: leblanc.c
	gcc -pg -Wall -Werror leblanc.c -lm -o leblanc_valgrind
	valgrind --tool=memcheck --leak-check=yes  --show-reachable=yes ./leblanc_valgrind
   
run: leblanc
	./leblanc
