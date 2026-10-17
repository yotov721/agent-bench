import csv


def total_revenue(path):
    total = 0.0
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        for row in reader:
            qty = (row["qty"] or "").strip()
            if not qty:
                continue
            total += float(row["price"]) * int(qty)
    return total


if __name__ == "__main__":
    print(f"Total revenue: {total_revenue('data.csv'):.2f}")
