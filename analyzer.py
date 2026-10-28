import csv
import sys
from google import genai
from dotenv import load_dotenv
load_dotenv()

SEVERITY = {
        "Payment failed": 4,
        "File not found": 2,
        "Database connection timeout": 4,
        "Out of memory": 5,
        "Invalid user token": 2,
        "Permission denied": 3,
    }


def read_log(log_path:str):
    lines_list = []
    with open(log_path) as file:
        for line in file:
                lines_list.append(line.strip())
    return lines_list

def error_summary_file(error_counts:list):
    with open("error_summary.csv", "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["error", "count"])
        for error, count in error_counts:
            writer.writerow([error, count])

def date_lines_file(logs_list:list):
    with open("date_lines.csv", "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["date", "time", "level", "message"])
        writer.writerows(logs_list)


def count_error(logs_list:list)->dict:
    counts = {}
    for line in logs_list:
            if "ERROR" in line:
                error = line.split("ERROR ")[1]
                if error in counts:
                    counts[error] += 1
                else:
                    counts[error] = 1
    return counts

def most_common(error_dict:dict, severity_dict:dict,num:int = 5)->list:
    sorted_counts = sorted(
    error_dict.items(), key=lambda item: (item[1], severity_dict[item[0]]), reverse=True
    )
    return sorted_counts[0:num]


def logs_in_date(logs_list:list, wanted_date:str)->list:
    date_rows = []
    for line in logs_list:
        parts = line.split(maxsplit=3)
        if parts[0] == wanted_date:
            date_rows.append(parts)
    return date_rows

def explain_errors(common_errors:list)->str:
    errors_text = ""
    for error, count in common_errors:
        errors_text += f"{error}: {count}\n"   
    prompt = (
        "הנה השגיאות הנפוצות ביותר בלוג של שרת, עם מספר ההופעות של כל אחת. " \
            "לכל שגיאה, הסבר מה יכולה להיות הסיבה ומה כדאי לבדוק כדי לתקן. ענה בקצרה." 
    )
    client = genai.Client()
    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input = prompt +"\n"+ errors_text
    )
    return interaction.output_text



def main():
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <logfile> [date]")
        sys.exit(1)
    log_path = sys.argv[1]
    date_filter = sys.argv[2] if len(sys.argv) == 3 else None

    log_list = read_log(log_path)
    if date_filter:
        logs_in_date_list = logs_in_date(log_list,date_filter)
        date_lines_file(logs_in_date_list)
    counts = count_error(log_list)
    common_errors = most_common(counts,SEVERITY)
    error_summary_file(common_errors)
    print(explain_errors(common_errors))
    


if __name__=="__main__":
    main()




