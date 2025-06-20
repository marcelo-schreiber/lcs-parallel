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
    if (!fseq) {
        printf("Error reading file %s\n", fname);
        exit(1);
    }

    fseek(fseq, 0L, SEEK_END);
    long size = ftell(fseq);
    rewind(fseq);

    char *seq = (char *)calloc(size + 1, sizeof(char));
    if (!seq) {
        printf("Error allocating memory for sequence %s.\n", fname);
        exit(1);
    }

    int i = 0, ch;
    while ((ch = fgetc(fseq)) != EOF) {
        if (ch != '\n')
            seq[i++] = ch;
    }
    seq[i] = '\0';

    fclose(fseq);
    return seq;
}

mtype **allocateScoreMatrix(int sizeA, int sizeB)
{
    mtype **scoreMatrix = (mtype **)malloc((sizeB + 1) * sizeof(mtype *));
    for (int i = 0; i <= sizeB; i++)
        scoreMatrix[i] = (mtype *)calloc(sizeA + 1, sizeof(mtype));
    return scoreMatrix;
}

void initScoreMatrix(mtype **scoreMatrix, int sizeA, int sizeB)
{
    for (int j = 0; j <= sizeA; j++)
        scoreMatrix[0][j] = 0;
    for (int i = 1; i <= sizeB; i++)
        scoreMatrix[i][0] = 0;
}

int LCS(mtype **scoreMatrix, int sizeA, int sizeB, char *seqA, char *seqB, int blockSize, int rank, int size)
{
    int blocks_i = (sizeB + blockSize - 1) / blockSize;
    int blocks_j = (sizeA + blockSize - 1) / blockSize;

    for (int k = 0; k <= blocks_i + blocks_j - 2; ++k) {
        MPI_Barrier(MPI_COMM_WORLD);
        for (int bi = 0; bi <= k; ++bi) {
            int bj = k - bi;
            if (bi >= blocks_i || bj >= blocks_j)
                continue;

            int global_block_id = bi * blocks_j + bj;
            if (global_block_id % size != rank)
                continue;

            int i_start = bi * blockSize + 1;
            int j_start = bj * blockSize + 1;
            int i_end = min((bi + 1) * blockSize, sizeB);
            int j_end = min((bj + 1) * blockSize, sizeA);

            if (bi > 0) {
                int src = ((bi - 1) * blocks_j + bj) % size;
                MPI_Recv(&scoreMatrix[i_start - 1][j_start], j_end - j_start + 1, MPI_UNSIGNED_SHORT, src, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            }
            if (bj > 0) {
                int src = (bi * blocks_j + (bj - 1)) % size;
                for (int i = i_start; i <= i_end; ++i)
                    MPI_Recv(&scoreMatrix[i][j_start - 1], 1, MPI_UNSIGNED_SHORT, src, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            }
            if (bi > 0 && bj > 0) {
                int src = ((bi - 1) * blocks_j + (bj - 1)) % size;
                MPI_Recv(&scoreMatrix[i_start - 1][j_start - 1], 1, MPI_UNSIGNED_SHORT, src, 2, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            }

            for (int i = i_start; i <= i_end; ++i) {
                for (int j = j_start; j <= j_end; ++j) {
                    if (seqA[j - 1] == seqB[i - 1])
                        scoreMatrix[i][j] = scoreMatrix[i - 1][j - 1] + 1;
                    else
                        scoreMatrix[i][j] = max(scoreMatrix[i - 1][j], scoreMatrix[i][j - 1]);
                }
            }

            if (bi < blocks_i - 1) {
                int dest = ((bi + 1) * blocks_j + bj) % size;
                MPI_Send(&scoreMatrix[i_end][j_start], j_end - j_start + 1, MPI_UNSIGNED_SHORT, dest, 0, MPI_COMM_WORLD);
            }
            if (bj < blocks_j - 1) {
                int dest = (bi * blocks_j + (bj + 1)) % size;
                for (int i = i_start; i <= i_end; ++i)
                    MPI_Send(&scoreMatrix[i][j_end], 1, MPI_UNSIGNED_SHORT, dest, 1, MPI_COMM_WORLD);
            }
            if (bi < blocks_i - 1 && bj < blocks_j - 1) {
                int dest = ((bi + 1) * blocks_j + (bj + 1)) % size;
                MPI_Send(&scoreMatrix[i_end][j_end], 1, MPI_UNSIGNED_SHORT, dest, 2, MPI_COMM_WORLD);
            }
        }
    }

    int result = 0;
    int last_block_i = (sizeB - 1) / blockSize;
    int last_block_j = (sizeA - 1) / blockSize;
    int last_block_id = last_block_i * blocks_j + last_block_j;

    if ((last_block_id % size) == rank) {
        result = scoreMatrix[sizeB][sizeA];
    }

    int final_result;
    MPI_Reduce(&result, &final_result, 1, MPI_INT, MPI_MAX, 0, MPI_COMM_WORLD);

    return final_result;
}

void freeScoreMatrix(mtype **scoreMatrix, int sizeB)
{
    for (int i = 0; i <= sizeB; i++)
        free(scoreMatrix[i]);
    free(scoreMatrix);
}

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc < 2) {
        if (rank == 0) printf("Usage: ./mpi <blockSize>\n");
        MPI_Finalize();
        return 1;
    }

    int blockSize = atoi(argv[1]);

    char *seqA = read_seq("fileA.in");
    char *seqB = read_seq("fileB.in");

    int sizeA = strlen(seqA);
    int sizeB = strlen(seqB);

    mtype **scoreMatrix = allocateScoreMatrix(sizeA, sizeB);
    initScoreMatrix(scoreMatrix, sizeA, sizeB);

    int result = LCS(scoreMatrix, sizeA, sizeB, seqA, seqB, blockSize, rank, size);

    if (rank == 0)
        printf("LCS length: %d\n", result);

    freeScoreMatrix(scoreMatrix, sizeB);
    free(seqA);
    free(seqB);

    MPI_Finalize();
    return 0;
}
