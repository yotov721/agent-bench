import csv


def total_revenue(path):
    total = 0.0
    with open(path) as f:
        for row in csv.DictReader(f):
            total += float(row["price"]) * int(row["qty"])
    return total


if __name__ == "__main__":
    print(f"Total revenue: {total_revenue('data.csv'):.2f}")
