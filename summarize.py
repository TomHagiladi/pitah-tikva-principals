"""
summarize.py — runs on the facilitator's laptop during the workshop.

מאזין לבקשות סיכום ב-/summaryRequest ב-Firebase RTDB. כשתום לוחץ על
"צור סיכום משובים" בדשבורד הבקרה (הפרטי), בקשה חדשה נכתבת ל-DB.
הסקריפט קורא את /feedback, שולח ל-Claude, וכותב את התוצאה ל-/summary.
הדשבורד (גם הפרטי וגם הציבורי) מאזין ל-/summary ומציג את הסיכום אוטומטית.

הפעלה:
    # וודא ש-ANTHROPIC_API_KEY מוגדר ב-env:
    #   PowerShell:  $env:ANTHROPIC_API_KEY = "sk-ant-..."
    #   bash:        export ANTHROPIC_API_KEY=sk-ant-...
    python summarize.py

השאר את הסקריפט רץ בטרמינל לאורך הסדנה. Ctrl+C לעצירה.
"""
import os
import sys
import time
import requests
from anthropic import Anthropic

DB_URL = "https://pitah-tikva-principals-default-rtdb.europe-west1.firebasedatabase.app"
MODEL = "claude-sonnet-4-6"
POLL_SECONDS = 3

SYSTEM_PROMPT = """אתה/את מסכם/ת משובי משתתפים בסדנת מנהלי בתי ספר בישראל, שעסקה בהתחדשות אחרי תקופה קשה, ובמציאת רגעי השראה בעבודה החינוכית.

סכם בעברית, בטון חם ואמפתי, אבל גם מקצועי ומדויק.

כללים:
- 3-5 משפטים בלבד (הסיכום יוצג על מסך בכיתה)
- שפה ברורה, לא פיוטית מדי
- זהה 2-3 מוטיבים מרכזיים שעלו
- כבד את הקול של המשתתפים — אם משהו עלה כקושי, אל תעטר אותו כהצלחה
- אל תציין שמות
- אל תוסיף כותרות או bullet-points, פסקה רציפה בלבד"""


def fetch(path):
    r = requests.get(f"{DB_URL}/{path}.json", timeout=10)
    r.raise_for_status()
    return r.json()


def put(path, data):
    r = requests.put(f"{DB_URL}/{path}.json", json=data, timeout=10)
    r.raise_for_status()
    return r.json()


def build_feedback_text(feedback_dict):
    items = []
    for _uid, item in feedback_dict.items():
        text = (item or {}).get("text", "").strip()
        if text:
            items.append(f"- {text}")
    return "\n".join(items)


def generate_summary(feedback_text):
    client = Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"להלן המשובים:\n\n{feedback_text}\n\nסכם/י בעברית.",
            }
        ],
    )
    return msg.content[0].text.strip()


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("חסר ANTHROPIC_API_KEY במשתני הסביבה. הגדר אותו ונסה שוב.")
        sys.exit(1)

    print(f"מחובר ל-{DB_URL}")
    print(f"מודל: {MODEL}")
    print(f"בודק כל {POLL_SECONDS} שניות. Ctrl+C לעצירה.\n")

    # בדוק מצב נוכחי כדי לא לסכם על בקשה ישנה ברגע ההפעלה
    last_seen = None
    try:
        current = fetch("summaryRequest")
        if current and isinstance(current, dict):
            last_seen = current.get("requestedAt")
            if last_seen:
                print(f"  (בקשה קיימת שנוצרה קודם timestamp={last_seen} — מתעלם ממנה)")
    except Exception as e:
        print(f"אזהרה: בעיה בקריאה ראשונית: {e}")

    while True:
        try:
            req = fetch("summaryRequest")
            if req and isinstance(req, dict):
                requested_at = req.get("requestedAt")
                if requested_at and requested_at != last_seen:
                    last_seen = requested_at
                    print(f"\nבקשה חדשה התקבלה (timestamp={requested_at})")
                    feedback = fetch("feedback") or {}
                    if not feedback:
                        print("  אין משובים — רושם שגיאה")
                        put("summary", {"status": "error", "error": "אין עדיין משובים"})
                    else:
                        text = build_feedback_text(feedback)
                        print(f"  נמצאו {len(feedback)} משובים, שולח ל-Claude...")
                        put("summary", {"status": "generating"})
                        try:
                            summary = generate_summary(text)
                            put(
                                "summary",
                                {
                                    "status": "ready",
                                    "text": summary,
                                    "generatedAt": int(time.time() * 1000),
                                    "feedbackCount": len(feedback),
                                },
                            )
                            print(f"  סיכום נכתב ({len(summary)} תווים):")
                            print(f"--- סיכום ---\n{summary}\n---")
                        except Exception as e:
                            print(f"  שגיאת Claude: {e}")
                            put("summary", {"status": "error", "error": str(e)[:200]})
            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            print("\nעצירה.")
            break
        except Exception as e:
            print(f"אזהרה: {e} — מנסה שוב בעוד {POLL_SECONDS} שניות")
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
