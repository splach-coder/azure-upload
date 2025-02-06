def compare_numbers_with_tolerance(num1, num2, tolerance=5):
    """
    Compares two numbers and checks if the absolute difference is within the given tolerance.

    :param num1: float, the first number
    :param num2: float, the second number
    :param tolerance: float, the allowed absolute difference (default is 5)
    :return: bool, True if the difference is within tolerance, False otherwise
    """
    # Calculate the absolute difference
    absolute_difference = abs(num1 - num2)

    # Check if the absolute difference is within the tolerance
    return absolute_difference <= tolerance


print(compare_numbers_with_tolerance(3647.86, 3648))




