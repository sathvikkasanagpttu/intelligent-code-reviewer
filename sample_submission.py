def calculate_total(items):
    total = 0
    for i in items:
        total += i["price"]
    return total
