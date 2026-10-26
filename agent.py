# ---------- 1. imports ----------
import json
from google import genai
from dotenv import load_dotenv
from analyzer import read_log, count_error
load_dotenv()


# ---------- 2. הפונקציה (הכלי עצמו) ----------
def get_error_counts(log_path: str) -> dict:
    # TODO: לקרוא את הקובץ עם read_log
    # TODO: להעביר את התוצאה ל-count_error
    # TODO: להחזיר את המילון
    logs_list = read_log(log_path)
    return count_error(logs_list)

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


# ---------- 4. השיחה ----------
def main():
    client = genai.Client()

    # --- סבב 1: שולחים משימה + כלי ---
    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input="נתח את הקובץ app.log וכתוב אילו שגיאות הכי בעייתיות",
        tools=[count_tool]
    )
    # TODO: להדפיס את interaction.outputs ולהסתכל מה חזר
    #print(dir(interaction)) 
    #print(interaction)
    for step in interaction.steps:
        if step.type == "function_call":
            call_id = step.id
            call_name = step.name
            path = step.arguments['log_path']
            result = get_error_counts(path)
            print(result)
    # --- הרצת הכלי ---
    # TODO: לעבור על interaction.outputs בלולאה
    # TODO: למצוא פריט שה-type שלו "function_call"
    # TODO: לקחת ממנו את log_path מתוך arguments
    # TODO: לקרוא ל-get_error_counts עם הערך הזה, ולשמור את התוצאה

    # --- סבב 2: מחזירים תוצאה, מקבלים תשובה ---
    # TODO: קריאה נוספת ל-create עם previous_interaction_id
    #       וב-input מילון function_result (ראי בהודעה הקודמת)
    # TODO: להדפיס את output_text
    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        previous_interaction_id=interaction.id,
        input=[{
            "type": "function_result",
            "name": call_name,
            "call_id": call_id,
            "result": [{"type": "text", "text": json.dumps(result)}]
        }],
        tools=[count_tool]
    )
    print(interaction.output_text)


if __name__ == "__main__":
    main()
