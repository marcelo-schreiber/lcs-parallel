#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#ifndef max
#define max(a, b) (((a) > (b)) ? (a) : (b))
#endif

#ifndef min
#define min(a, b) (((a) < (b)) ? (a) : (b))
#endif

typedef unsigned short mtype;

/* Read sequence from a file to a char vector.
 Filename is passed as parameter */

char *read_seq(char *fname)
{
	// file pointer
	FILE *fseq = NULL;
	// sequence size
	long size = 0;
	// sequence pointer
	char *seq = NULL;
	// sequence index
	int i = 0;

	// open file
	fseq = fopen(fname, "rt");
	if (fseq == NULL)
	{
		printf("Error reading file %s\n", fname);
		exit(1);
	}

	// find out sequence size to allocate memory afterwards
	fseek(fseq, 0L, SEEK_END);
	size = ftell(fseq);
	rewind(fseq);

	// allocate memory (sequence)
	seq = (char *)calloc(size + 1, sizeof(char));
	if (seq == NULL)
	{
		printf("Erro allocating memory for sequence %s.\n", fname);
		exit(1);
	}

	int ch;
	while ((ch = fgetc(fseq)) != EOF)
	{
		if (ch != '\n')
			seq[i++] = ch;
	}
	seq[i] = '\0';

	// close file
	fclose(fseq);

	// return sequence pointer
	return seq;
}

mtype **allocateScoreMatrix(int sizeA, int sizeB)
{
	int i;
	// Allocate memory for LCS score matrix
	mtype **scoreMatrix = (mtype **)malloc((sizeB + 1) * sizeof(mtype *));
	for (i = 0; i < (sizeB + 1); i++)
		scoreMatrix[i] = (mtype *)malloc((sizeA + 1) * sizeof(mtype));
	return scoreMatrix;
}

void initScoreMatrix(mtype **scoreMatrix, int sizeA, int sizeB)
{
	int i, j;
	// Fill first line of LCS score matrix with zeroes
	for (j = 0; j < (sizeA + 1); j++)
		scoreMatrix[0][j] = 0;

// Do the same for the first collumn
#pragma omp parallel for
	for (i = 1; i < (sizeB + 1); i++)
		scoreMatrix[i][0] = 0;
}

int LCS(mtype **scoreMatrix, int sizeA, int sizeB, char *seqA, char *seqB, int numThreads, int blockSize)
{
	int num_blocks_i = (sizeB + blockSize - 1) / blockSize;
	int num_blocks_j = (sizeA + blockSize - 1) / blockSize;

	for (int k = 0; k <= num_blocks_i + num_blocks_j - 2; ++k)
	{
#pragma omp parallel for num_threads(numThreads)
		for (int b = 0; b <= k; ++b)
		{
			int bi = b;
			int bj = k - b;

			if (bi >= num_blocks_i || bj >= num_blocks_j)
				continue;

			int i_start = bi * blockSize + 1;
			int j_start = bj * blockSize + 1;
			int i_end = (bi + 1) * blockSize;
			int j_end = (bj + 1) * blockSize;

			if (i_end > sizeB)
				i_end = sizeB;
			if (j_end > sizeA)
				j_end = sizeA;

			for (int i = i_start; i <= i_end; ++i)
			{
				for (int j = j_start; j <= j_end; ++j)
				{
					if (seqA[j - 1] == seqB[i - 1])
					{
						scoreMatrix[i][j] = scoreMatrix[i - 1][j - 1] + 1;
					}
					else
					{
						scoreMatrix[i][j] = max(scoreMatrix[i - 1][j], scoreMatrix[i][j - 1]);
					}
				}
			}
		}
	}

	return scoreMatrix[sizeB][sizeA];
}

void printMatrix(char *seqA, char *seqB, mtype **scoreMatrix, int sizeA,
								 int sizeB)
{
	int i, j;

	// print header
	printf("Score Matrix:\n");
	printf("========================================\n");

	// print LCS score matrix allong with sequences

	printf("    ");
	printf("%5c   ", ' ');

	for (j = 0; j < sizeA; j++)
		printf("%5c   ", seqA[j]);
	printf("\n");
	for (i = 0; i < sizeB + 1; i++)
	{
		if (i == 0)
			printf("    ");
		else
			printf("%c   ", seqB[i - 1]);
		for (j = 0; j < sizeA + 1; j++)
		{
			printf("%5d   ", scoreMatrix[i][j]);
		}
		printf("\n");
	}
	printf("========================================\n");
}

void freeScoreMatrix(mtype **scoreMatrix, int sizeB)
{
	int i;
	for (i = 0; i < (sizeB + 1); i++)
		free(scoreMatrix[i]);
	free(scoreMatrix);
}

unsigned int prev_pow2(unsigned int x)
{
	if (x == 0)
	{
		return 0;
	}
	return 1U << (31 - __builtin_clz(x));
}

int main(int argc, char **argv)
{
	// sequence pointers for both sequences
	char *seqA, *seqB;

	// sizes of both sequences
	int sizeA, sizeB, blockSize = 16;

	// read both sequences
	seqA = read_seq("fileA.in");
	seqB = read_seq("fileB.in");

	// find out sizes
	sizeA = strlen(seqA);
	sizeB = strlen(seqB);

	// allocate LCS score matrix
	mtype **scoreMatrix = allocateScoreMatrix(sizeA, sizeB);

	// initialize LCS score matrix
	initScoreMatrix(scoreMatrix, sizeA, sizeB);

	int threadCount = atoi(argv[1]);

	if (argc == 3)
	{
		blockSize = atoi(argv[2]);
	}

	// fill up the rest of the matrix and return final score (element locate at the last line and collumn)
	int res = LCS(scoreMatrix, sizeA, sizeB, seqA, seqB, threadCount, blockSize);

	printf("LCS length: %d\n", res);

	/* if you wish to see the entire score matrix,
	 for debug purposes, define DEBUGMATRIX. */
#ifdef DEBUGMATRIX
	printMatrix(seqA, seqB, scoreMatrix, sizeA, sizeB);
#endif

	// free score matrix
	freeScoreMatrix(scoreMatrix, sizeB);
	free(seqA);
	free(seqB);

	return EXIT_SUCCESS;
}