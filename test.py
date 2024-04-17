def calculate_pip_difference(current_price, base_price):
    return (current_price - base_price) * 10000


result = calculate_price_difference(1.07275, 1.06460)
print(result)

negative_result = calculate_price_difference(1.06479, 1.07275)
print(negative_result)
