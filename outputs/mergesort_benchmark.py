import random
import time

def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i, j = 0, 0
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result += left[i:]
    result += right[j:]
    return result

def benchmark_sorting_algorithms():
    # Generate a list of 10000 random numbers
    random_list = [random.randint(0, 10000) for _ in range(10000)]

    # Benchmark merge sort
    start_time = time.time()
    sorted_list = merge_sort(random_list.copy())
    end_time = time.time()
    merge_sort_time = end_time - start_time

    # Benchmark Python's built-in sort
    start_time = time.time()
    random_list.sort()
    end_time = time.time()
    built_in_sort_time = end_time - start_time

    print(f"Merge sort time: {merge_sort_time} seconds")
    print(f"Built-in sort time: {built_in_sort_time} seconds")

    return merge_sort_time, built_in_sort_time

def save_benchmark_results(merge_sort_time, built_in_sort_time):
    with open("mergesort_benchmark.py", "w") as file:
        file.write(f"merge_sort_time = {merge_sort_time}\n")
        file.write(f"built_in_sort_time = {built_in_sort_time}\n")

def main():
    merge_sort_time, built_in_sort_time = benchmark_sorting_algorithms()
    save_benchmark_results(merge_sort_time, built_in_sort_time)

if __name__ == "__main__":
    main()

# Execution output:
# Merge sort time: 0.03304457664489746 seconds
# Built-in sort time: 0.001020193099975586 seconds