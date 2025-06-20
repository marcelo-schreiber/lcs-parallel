parallel_name = parallel
sequential_name = sequential
mpi_name = mpi

CC=gcc
MPICC=mpicc
CFLAGS=-Wall -W -Wextra -pedantic -std=c99 -O3

all: $(parallel_name) $(sequential_name) $(mpi_name)
$(parallel_name): lcs-openmp.c
	$(CC) $(CFLAGS) -o $(parallel_name) lcs-openmp.c -fopenmp
$(sequential_name): lcs.c
	$(CC) $(CFLAGS) -o $(sequential_name) lcs.c
$(mpi_name): lcs-mpi.c
	$(MPICC) $(CFLAGS) -o $(mpi_name) lcs-mpi.c
clean:
	rm -f $(parallel_name) $(sequential_name) $(mpi_name)
	rm -f *.o
	rm -f *.txt