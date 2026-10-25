import csv
import sys

counts = {}
severity = {
    "Payment failed": 4,
    "File not found": 2,
    "Database connection timeout": 4,
    "Out of memory": 5,
    "Invalid user token": 2,
    "Permission denied": 3,
}

if len(sys.argv) < 2:
    print("Usage: python analyzer.py <logfile> [date]")
    sys.exit(1)

log_path = sys.argv[1]
date_filter = sys.argv[2] if len(sys.argv) == 3 else None
date_rows = []

with open(log_path) as file:
    for line in file:
        line = line.strip()
        if "ERROR" in line:
            error = line.split("ERROR ")[1]
            if error in counts:
                counts[error] += 1
            else:
                counts[error] = 1
        if date_filter:
            parts = line.split(maxsplit=3)
            if parts[0] == date_filter:
                print(line)
                date_rows.append(parts)

if date_filter:
    with open("date_lines.csv", "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["date", "time", "level", "message"])
        writer.writerows(date_rows)

sorted_counts = sorted(
    counts.items(), key=lambda item: (item[1], severity[item[0]]), reverse=True
)
sorted_counts = sorted_counts[0:5]

with open("error_summary.csv", "w", newline="") as out:
    writer = csv.writer(out)
    writer.writerow(["error", "count"])
    for error, count in sorted_counts:
        print(f"{error}: {count}")
        writer.writerow([error, count])