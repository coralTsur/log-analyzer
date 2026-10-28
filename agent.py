# ---------- 1. imports ----------
import json
import sys
from google import genai
from dotenv import load_dotenv
from analyzer import read_log, count_error, SEVERITY, most_common, logs_in_date
load_dotenv()

MAX_ROUNDS = 5
REPORT_INSTRUCTIONS = """אתה מנתח לוגים של שרת.
השתמש בכלים כדי לקבל נתונים. כל מספר בדוח חייב להגיע מתוצאה של כלי, אל תנחש.

כל תשובה שלך היא דוח בעברית, בנוי בדיוק כך:

## סיכום
משפט אחד: המצב הכללי והבעיה העיקרית.

## ממצאים
רשימה של השגיאות הרלוונטיות לשאלה. לכל שגיאה: שם, מספר הופעות, והסבר קצר של מה היא אומרת.

## המלצות
רשימה ממוספרת של עד 3 פעולות, מהדחופה ביותר.

אם השאלה לא קשורה לקובץ הלוג, כתוב זאת בסעיף הסיכום והשאר את שאר הסעיפים ריקים."""
# ---------- 2. הפונקציה (הכלי עצמו) ----------
def get_error_counts(log_path: str) -> dict:
    logs_list = read_log(log_path)
    return count_error(logs_list)

def get_most_common(log_path: str, num:int)->list:
    return most_common(get_error_counts(log_path),SEVERITY,num)

def get_logs_in_date(log_path: str, wanted_date:str)->list:
    return logs_in_date(read_log(log_path),wanted_date)

# ---------- 3. התיאור (מה שהמודל רואה) ----------
count_tool = {
    "type": "function",
    "name": "get_error_counts",
    "description": "מחזירה כמה פעמים הופיעה כל שגיאה בקובץ הלוג",
    "parameters": {
        "type": "object",
        "properties": {
            "log_path": {"type": "string", "description": "הנתיב לקובץ הלוג"}
        },
        "required": ["log_path"]
    }
}

most_common_tool = {
    "type": "function",
    "name": "get_most_common",
    "description": "מחזירה את השגיאות הנפוצות ביותר בקובץ הלוג, ממוינות לפי מספר ההופעות. "
    "כשיש שוויון, השגיאה החמורה יותר מופיעה קודם.",
    "parameters": {
        "type": "object",
        "properties": {
            "log_path": {"type": "string", "description": "הנתיב לקובץ הלוג"},
            "num": {"type": "integer", "description": "כמה שגיאות להחזיר. ברירת מחדל: 5"}
        },
        "required": ["log_path"]
    }
}

logs_in_date_tool = {
    "type": "function",
    "name": "get_logs_in_date",
    "description":"מחזירה את כל שורות הלוג (INFO, WARNING ו-ERROR) מתאריך מסוים, בפורמט המקורי שלהן.",
    "parameters": {
        "type": "object",
        "properties": {
            "log_path": {"type": "string", "description": "הנתיב לקובץ הלוג"},
            "wanted_date": {"type": "string", "description": "תאריך שממנו נרצה לראות לוגים בפורמט YYYY-MM-DD"}
        },
        "required": ["log_path","wanted_date"]
    }
}


# ---------- 4. השיחה ----------
def main():
    client = genai.Client()
    rounds = 0
    found_call = False
    TOOLS = [count_tool,most_common_tool,logs_in_date_tool]

    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <logfile> [date]")
        sys.exit(1)
    log_path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) == 3 else "נתח את הקובץ וכתוב אילו שגיאות הכי בעייתיות"

    # --- סבב 1: שולחים משימה + כלי ---
    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        system_instruction=REPORT_INSTRUCTIONS,
        input=f"קובץ הלוג: {log_path}\nשאלה: {question}",
        #input="נתח את הקובץ app.log וכתוב אילו שגיאות היו בתאריך 2026-10-21",
        #input = "מה השם של הצמח הכי נפוץ",
        tools=TOOLS
    )
    #print(dir(interaction)) #helped me understand how to get to call_id, call_name ect. 
    #print(interaction)

    while (rounds < MAX_ROUNDS):
        rounds += 1
        found_call = False
        for step in interaction.steps:
            if step.type == "function_call":
                found_call = True
                call_id = step.id
                call_name = step.name
                #print(f"המודל ביקש: {call_name} {step.arguments}")

                if (call_name =="get_error_counts"):
                    path = step.arguments['log_path']
                    result = get_error_counts(path)

                elif (call_name == "get_most_common"):
                    path = step.arguments['log_path']
                    num = step.arguments.get("num", 5)
                    result = get_most_common(path, num)

                elif call_name == "get_logs_in_date":                    
                    path = step.arguments['log_path']
                    wanted_date = step.arguments['wanted_date']
                    result = get_logs_in_date(path, wanted_date)
                else:
                    result= f"Unknown tool: {call_name}"
                #print(result)
        if not found_call:
            break
        if rounds == MAX_ROUNDS:
            break
        interaction = client.interactions.create(
                model="gemini-3.5-flash-lite",
                system_instruction=REPORT_INSTRUCTIONS,
                previous_interaction_id=interaction.id,
                input=[{
                    "type": "function_result",
                    "name": call_name,
                    "call_id": call_id,
                    "result": [{"type": "text", "text": json.dumps(result)}]
                }],
                tools=TOOLS
            )

    if found_call == False:
        print(interaction.output_text)
        with open("report.md", "w", encoding="utf-8") as f:
            f.write(interaction.output_text)
    else:
        print(f"After {MAX_ROUNDS} attempts, we haven't reached an answer. " \
        "Please try again—you might want to refine or be more specific with your requests.")


    #print(get_most_common("app.log", 3))
    #print(get_logs_in_date("app.log", "2026-10-21"))


if __name__ == "__main__":
    main()
