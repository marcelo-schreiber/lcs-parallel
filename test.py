import random
from os import system
from time import sleep

LENGTHS = [80000, 60000, 40000, 10000]
NUM_PROCESSES = [2, 4, 6]
BLOCKS = [32, 256, 1024]
REPS = 5

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
    user_times = []
    real_times = []

    with open(file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if "user" in line:
                user_time = float(line.split()[0].replace(',', '.'))
                user_times.append(user_time)
            elif "elapsed" in line:
                real_time = float(line.split()[0].replace(',', '.'))
                real_times.append(real_time)

    average_user_time = sum(user_times) / len(user_times)
    average_real_time = sum(real_times) / len(real_times)
    user_deviation = (sum((x - average_user_time) ** 2 for x in user_times) / len(user_times)) ** 0.5
    real_deviation = (sum((x - average_real_time) ** 2 for x in real_times) / len(real_times)) ** 0.5

    return average_user_time, user_deviation, average_real_time, real_deviation

def main():
    system("make")

    for length in LENGTHS:
        for _ in range(REPS):
            generate_inputs(length)
            sleep(0.1)

            # Sequential run (optional if not comparing)
            system(f"perf stat -o ./txts/seq{length}.txt --append -- ./sequential")
            sleep(0.1)

            # MPI runs
            for np in NUM_PROCESSES:
                for block in BLOCKS:
                    outfile = f"./txts/mpi{length}_{np}_{block}.txt"
                    cmd = f"perf stat -o {outfile} --append -- mpirun -np {np} ./mpi {block}"
                    system(cmd)
                    sleep(0.1)

    # Generate CSV reports
    with open("mpi.csv", "w") as f:
        f.write("length,np,block,user_avg,user_dev,real_avg,real_dev\n")
        for length in LENGTHS:
            for np in NUM_PROCESSES:
                for block in BLOCKS:
                    try:
                        file = f"./txts/mpi{length}_{np}_{block}.txt"
                        user_avg, user_dev, real_avg, real_dev = get_averages_and_deviations_from_file(file)
                        f.write(f"{length},{np},{block},{user_avg},{user_dev},{real_avg},{real_dev}\n")
                    except Exception:
                        f.write(f"{length},{np},{block},ERROR,ERROR,ERROR,ERROR\n")

    with open("sequential.csv", "w") as f:
        f.write("length,user_avg,user_dev,real_avg,real_dev\n")
        for length in LENGTHS:
            try:
                file = f"./txts/seq{length}.txt"
                user_avg, user_dev, real_avg, real_dev = get_averages_and_deviations_from_file(file)
                f.write(f"{length},{user_avg},{user_dev},{real_avg},{real_dev}\n")
            except Exception:
                f.write(f"{length},ERROR,ERROR,ERROR,ERROR\n")

if __name__ == "__main__":
    main()
