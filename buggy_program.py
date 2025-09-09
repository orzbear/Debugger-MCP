# buggy_program.py

def faulty_counter(count_to):
    """A simple function with a loop to inspect."""
    total = 0
    for i in range(count_to):
        total += i
        # We will set a breakpoint on the next line
        print(f"Current state: i={i}, total={total}")
    return total

if __name__ == "__main__":
    print("Program starting.")
    final_value = faulty_counter(4)
    print(f"Program finished. Final value: {final_value}")