def calculate_list_sum(numbers):
    """
    Calculates the sum of a list of numbers.
    ...or so it claims.
    """
    total = 0
    # Loop through the indices of the list to add each number.
    for i in range(len(numbers) - 1): # <- The bug is on this line!
        current_number = numbers[i]
        total += current_number
        print(f"  (Looping... adding {current_number}, new total is {total})")
    
    return total

# --- Main part of the script ---
my_numbers = [10, 20, 30, 40, 50]
expected_result = 150

print("Starting calculation...")
actual_result = calculate_list_sum(my_numbers)
print("Calculation finished!")

print(f"\nExpected result: {expected_result}")
print(f"Actual result:   {actual_result}")

if actual_result == expected_result:
    print("\n✅ The result is correct!")
else:
    print(f"\n❌ Something is wrong! The result is off by {expected_result - actual_result}.")