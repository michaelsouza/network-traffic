leblanc: leblanc.c
	gcc -Wall -Werror leblanc.c -lm -o leblanc
	
leblanc_valgrind: leblanc.c
	gcc -pg -Wall -Werror leblanc.c -lm -o leblanc_valgrind
	valgrind --tool=memcheck --leak-check=yes  --show-reachable=yes ./leblanc_valgrind
   
run: leblanc
	./leblanc
