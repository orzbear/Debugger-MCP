def calculate_sum(limit):
    """Calculates the sum of numbers up to a limit."""
    total = 0
    for i in range(limit):
        total += i
        print(f"  (Calculating... current total is {total})")
    return total

print("Debugger test script started.")
final_result = calculate_sum(5)
print(f"Debugger test script finished. Final result: {final_result}")