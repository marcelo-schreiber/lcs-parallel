parallel_name = parallel
sequential_name = sequential

CC=gcc
CFLAGS=-Wall -W -Wextra -pedantic -std=c99 -O3 -march=native -mavx -fopenmp

all: $(parallel_name) $(sequential_name)
$(parallel_name): lcs-parallel.c
	$(CC) $(CFLAGS) -o $(parallel_name) lcs-parallel.c
$(sequential_name): lcs.c
	$(CC) $(CFLAGS) -o $(sequential_name) lcs.c
clean:
	rm -f $(parallel_name) $(sequential_name)
	rm -f *.o
	rm -f *.txt