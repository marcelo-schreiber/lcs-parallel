import random
from os import system
from time import sleep

LENGTHS = [80000, 60000, 40000, 10000]
NUM_THREADS = [1, 2, 4, 8, 16]
BLOCKS = [32, 256, 1024, 4096]
REPS = 20

def generate_inputs(length):
    with open('fileA.in', 'w') as f:
        for _ in range(length):
            f.write(random.choice('abcdefghijklmnopqrstuvwxyz'))
        f.write('\n')
    with open('fileB.in', 'w') as f:
        for _ in range(length):
            f.write(random.choice('abcdefghijklmnopqrstuvwxyz'))
        f.write('\n')

def main():
    system("make")

    for length in LENGTHS:
        for _ in range(REPS):
            # sequential
            generate_inputs(length)

            sleep(.1)

            system(f"perf stat -o ./txts/seq{length}.txt --append -- ./sequential")

            sleep(.1)
            
            # parallel
            for threads in NUM_THREADS:
                for block in BLOCKS:
                    system(f"perf stat -o ./txts/para{length}_{threads}_{block}.txt --append -- ./parallel {threads} {block}")
                    sleep(.1)
    
    # get averages and deviations and put it in csv
    with open("parallel.csv", "w") as f:
        f.write("length,threads,blocks,user_avg,user_dev,real_avg,real_dev\n")
        for length in LENGTHS:
            for threads in NUM_THREADS:
                for block in BLOCKS:
                    user_avg, user_dev, real_avg, real_dev = get_averages_and_deviations_from_file(f"./txts/para{length}_{threads}_{block}.txt")
                    f.write(f"{length},{threads},{block},{user_avg},{user_dev},{real_avg},{real_dev}\n")

    with open("sequential.csv", "w") as f:
        f.write("length,user_avg,user_dev,real_avg,real_dev,\n")
        for length in LENGTHS:
            user_avg, user_dev, real_avg, real_dev = get_averages_and_deviations_from_file(f"./txts/seq{length}.txt")
            f.write(f"{length},{user_avg},{user_dev},{real_avg},{real_dev}\n")

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
    # Calculate average and standard deviation

    average_user_time = sum(user_times) / len(user_times)
    average_real_time = sum(real_times) / len(real_times)
    user_deviation = (sum((x - average_user_time) ** 2 for x in user_times) / len(user_times)) ** 0.5
    real_deviation = (sum((x - average_real_time) ** 2 for x in real_times) / len(real_times)) ** 0.5

    return average_user_time, user_deviation, average_real_time, real_deviation



if __name__ == "__main__":
    # generate_inputs(100000)
    # get_averages_and_deviations_from_file("algo.txt")
    main()
