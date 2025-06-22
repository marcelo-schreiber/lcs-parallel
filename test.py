import random
from os import system
from time import sleep

LENGTHS = [80000, 60000, 40000, 10000]
NUM_PROCESSES = [2, 4, 6, 8, 10]
BLOCKS = [256, 512, 1024]
REPS = 15

def generate_inputs(length):
    with open('fileA.in', 'w') as f:
        for _ in range(length):
            f.write(random.choice('abcdefghijklmnopqrstuvwxyz'))
        f.write('\n')
    with open('fileB.in', 'w') as f:
        for _ in range(length):
            f.write(random.choice('abcdefghijklmnopqrstuvwxyz'))
        f.write('\n')

def get_averages_and_deviations_from_file(file):
    # output file format:
    # Matrix size: 80000
    # Time elapsed: 16.852199 seconds
    # \n
    # Matrix size: 80000
    # Time elapsed: 16.852199 seconds
    # ... 

    with open(file, 'r') as f:
        lines = f.readlines()
        times = []
        for line in lines:
            if "Time elapsed" in line:
                time_str = line.split(":")[1].strip().split()[0]
                times.append(float(time_str))
        if not times:
            raise ValueError("No valid time data found in file.")
        user_avg = sum(times) / len(times)
        user_dev = (sum((x - user_avg) ** 2 for x in times) / len(times)) ** 0.5
        return user_avg, user_dev

def main():
    system("make")

    for length in LENGTHS:
        for _ in range(REPS):
            generate_inputs(length)
            sleep(0.1)

            # Sequential run (optional if not comparing)
            system(f"./sequential > ./txts/seq{length}.txt")
            sleep(0.1)

            # MPI runs
            for np in NUM_PROCESSES:
                for block in BLOCKS:
                    outfile = f"./txts/mpi{length}_{np}_{block}.txt"
                    cmd = f"mpirun -np {np} ./mpi {block} >> {outfile}"
                    system(cmd)
                    sleep(0.1)

    # Generate CSV reports
    with open("mpi.csv", "w") as f:
        f.write("length,np,block,user_avg,user_dev\n")
        for length in LENGTHS:
            for np in NUM_PROCESSES:
                for block in BLOCKS:
                    try:
                        file = f"./txts/mpi{length}_{np}_{block}.txt"
                        user_avg, user_dev = get_averages_and_deviations_from_file(file)
                        f.write(f"{length},{np},{block},{user_avg},{user_dev}\n")
                    except Exception:
                        f.write(f"{length},{np},{block},ERROR,ERROR\n")

    with open("sequential.csv", "w") as f:
        f.write("length,user_avg,user_dev,real_avg,real_dev\n")
        for length in LENGTHS:
            try:
                file = f"./txts/seq{length}.txt"
                user_avg, user_dev = get_averages_and_deviations_from_file(file)
                f.write(f"{length},{user_avg},{user_dev}\n")
            except Exception:
                f.write(f"{length},ERROR,ERROR\n")

if __name__ == "__main__":
    # main()
    generate_inputs(10)
