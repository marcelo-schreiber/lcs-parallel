#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mpi.h>

#ifndef max
#define max(a, b) (((a) > (b)) ? (a) : (b))
#endif

#ifndef min
#define min(a, b) (((a) < (b)) ? (a) : (b))
#endif

typedef unsigned short mtype;

char *read_seq(char *fname)
{
    FILE *fseq = fopen(fname, "rt");
    if (!fseq)
    {
        printf("Error reading file %s\n", fname);
        exit(1);
    }

    fseek(fseq, 0L, SEEK_END);
    long size = ftell(fseq);
    rewind(fseq);

    char *seq = (char *)calloc(size + 1, sizeof(char));
    if (!seq)
    {
        printf("Error allocating memory for sequence %s.\n", fname);
        exit(1);
    }

    int i = 0, ch;
    while ((ch = fgetc(fseq)) != EOF)
    {
        if (ch != '\n')
            seq[i++] = ch;
    }
    seq[i] = '\0';

    fclose(fseq);
    return seq;
}

mtype **allocateLocalBlock(int blockSize)
{
    mtype **block = (mtype **)malloc((blockSize + 1) * sizeof(mtype *));
    for (int i = 0; i <= blockSize; i++)
        block[i] = (mtype *)calloc(blockSize + 1, sizeof(mtype));
    return block;
}

void freeLocalBlock(mtype **block, int blockSize)
{
    for (int i = 0; i <= blockSize; i++)
        free(block[i]);
    free(block);
}

int LCS(int sizeA, int sizeB, char *seqA, char *seqB, int blockSize, int rank, int size)
{
    int blocks_i = (sizeB + blockSize - 1) / blockSize;
    int blocks_j = (sizeA + blockSize - 1) / blockSize;

    // Local block for computation
    mtype **localBlock = allocateLocalBlock(blockSize);
    
    // Communication buffers
    mtype *row_buffer = (mtype *)malloc((blockSize + 1) * sizeof(mtype));
    mtype *col_buffer = (mtype *)malloc((blockSize + 1) * sizeof(mtype));

    int final_result = 0;

    for (int k = 0; k <= blocks_i + blocks_j - 2; ++k)
    {
        for (int bi = 0; bi <= k; ++bi)
        {
            int bj = k - bi;
            if (bi >= blocks_i || bj >= blocks_j)
                continue;

            if ((bi + bj) % size != rank)
                continue;

            int i_start = bi * blockSize;
            int j_start = bj * blockSize;
            int i_end = min((bi + 1) * blockSize, sizeB);
            int j_end = min((bj + 1) * blockSize, sizeA);
            
            int block_height = i_end - i_start;
            int block_width = j_end - j_start;

            // Initialize boundaries
            for (int i = 0; i <= block_height; i++)
                localBlock[i][0] = 0;
            for (int j = 0; j <= block_width; j++)
                localBlock[0][j] = 0;

            // Receive top boundary (from above block)
            if (bi > 0)
            {
                int src = ((bi - 1) + bj) % size;
                if (src != rank) MPI_Recv(row_buffer, block_width + 1, MPI_UNSIGNED_SHORT, src, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                for (int j = 0; j <= block_width; j++)
                    localBlock[0][j] = row_buffer[j];
            }
            
            // Receive left boundary (from left block)
            if (bj > 0)
            {
                int src = (bi + (bj - 1)) % size;
                if (src != rank) MPI_Recv(col_buffer, block_height + 1, MPI_UNSIGNED_SHORT, src, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                for (int i = 0; i <= block_height; i++)
                    localBlock[i][0] = col_buffer[i];
            }

            // Compute the local block
            for (int i = 1; i <= block_height; i++)
            {
                for (int j = 1; j <= block_width; j++)
                {
                    int global_i = i_start + i - 1;
                    int global_j = j_start + j - 1;
                    
                    if (seqA[global_j] == seqB[global_i])
                        localBlock[i][j] = localBlock[i - 1][j - 1] + 1;
                    else
                        localBlock[i][j] = max(localBlock[i - 1][j], localBlock[i][j - 1]);
                }
            }

            // Send bottom boundary (to below block)
            if (bi < blocks_i - 1)
            {
                int dest = ((bi + 1) + bj) % size;
                for (int j = 0; j <= block_width; j++)
                    row_buffer[j] = localBlock[block_height][j];
                
                if (dest != rank) MPI_Send(row_buffer, block_width + 1, MPI_UNSIGNED_SHORT, dest, 0, MPI_COMM_WORLD);
            }
            
            // Send right boundary (to right block)
            if (bj < blocks_j - 1)
            {
                int dest = (bi + (bj + 1)) % size;
                for (int i = 0; i <= block_height; i++)
                    col_buffer[i] = localBlock[i][block_width];

                if (dest != rank) MPI_Send(col_buffer, block_height + 1, MPI_UNSIGNED_SHORT, dest, 1, MPI_COMM_WORLD);
            }

            // Store result if this is the last block
            if (bi == blocks_i - 1 && bj == blocks_j - 1)
            {
                final_result = localBlock[block_height][block_width];
            }
        }
    }

    freeLocalBlock(localBlock, blockSize);
    free(row_buffer);
    free(col_buffer);

    int global_result;
    MPI_Reduce(&final_result, &global_result, 1, MPI_INT, MPI_MAX, 0, MPI_COMM_WORLD);
    
    return global_result;
}

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc < 2)
    {
        if (rank == 0)
            printf("Usage: ./mpi <blockSize>\n");
        MPI_Finalize();
        return 1;
    }

    int blockSize = atoi(argv[1]);

    char *seqA = read_seq("fileA.in");
    char *seqB = read_seq("fileB.in");

    int sizeA = strlen(seqA);
    int sizeB = strlen(seqB);

    double start_time = MPI_Wtime();

    int result = LCS(sizeA, sizeB, seqA, seqB, blockSize, rank, size);

    double end_time = MPI_Wtime();
    double elapsed = end_time - start_time;

    if (rank == 0)
    {
        printf("Score: %d\n", result);
    }

    free(seqA);
    free(seqB);

    MPI_Finalize();
    return 0;
}
