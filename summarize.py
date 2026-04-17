"""
summarize.py — runs on the facilitator's laptop during the workshop.

מאזין לבקשות סיכום ב-/summaryRequest ב-Firebase RTDB. כשתום לוחץ על
"צור סיכום משובים" בדשבורד הבקרה (הפרטי), בקשה חדשה נכתבת ל-DB.
הסקריפט קורא את /feedback, שולח ל-Gemini, וכותב את התוצאה ל-/summary.
הדשבורד (גם הפרטי וגם הציבורי) מאזין ל-/summary ומציג את הסיכום אוטומטית.

הפעלה:
    # וודא ש-GEMINI_API_KEY מוגדר ב-env (מותקן אצל תום כ-Windows env variable).
    python summarize.py

השאר את הסקריפט רץ בטרמינל לאורך הסדנה. Ctrl+C לעצירה.
"""
import os
import sys
import time
import requests
from google import genai
from google.genai import types

DB_URL = "https://pitah-tikva-principals-default-rtdb.europe-west1.firebasedatabase.app"
MODEL = "gemini-2.5-flash"
POLL_SECONDS = 3

SYSTEM_PROMPT = """אתה/את מסכם/ת משובים חופשיים ממשתתפים ומשתתפות בסדנת מנהלי בתי ספר בישראל. הסדנה עסקה בהתחדשות וברגעי השראה בעבודה החינוכית אחרי תקופה קשה.

המטרה: סיכום שישדר למשתתפים "נשמעתם" — לא סיכום כללי שאפשר היה לכתוב על כל סדנה. הסיכום יוקרן על המסך בכיתה בסוף המפגש.

כללים (קריטיים):

1. עיגון בתוכן קונקרטי — ציטט ביטויים, רעיונות או אנקדוטות ספציפיות מהמשובים. אסור לכתוב "עלה עניין של X" — צריך לומר "אחת המשתתפות סיפרה על..." או "חזר מוטיב של... למשל 'ציטוט'". אם משהו נאמר בפירוט — עגן בו.

2. שני-שלושה עוגנים תמטיים — זהה/י 2-3 מוטיבים שחזרו, ונסח/י עבור כל אחד משפט עם רמז לתוכן, לא רק שם הנושא.

3. אורך: 4-6 משפטים מלאים. פסקה אחת רציפה. בלי כותרות, בלי bullets, בלי "ראשית / שנית".

4. טון: חם אבל מדויק. לא פיוטי, לא מנופח, לא קלישאי. אמפתי ופרקטי.

5. בלי שמות משתתפים.

6. בלי משפטי פתיחה כלליים — אסור להתחיל ב-"המשובים משקפים", "עולה מהמשובים", "ניכר כי", "המפגש היה", "חוויה עשירה", "מסע עמוק". התחל/י ישירות בתוכן הקונקרטי.

7. אם יש מעט משובים (1-2) — עדיין לעגן בתוכן הקונקרטי שעלה. אל תחליש/י לסיכום כללי "בטוח".

---

דוגמה לסיכום פסול (מה שאסור לכתוב):
"המשובים מהסדנה משקפים חוויה עשירה ומגוונת, המעידה על מסע עמוק של התחדשות ומציאת השראה."
— כללי, ריק, אפשר לכתוב על כל סדנה ללא קשר למה שנאמר בפועל. אם אתה כותב משהו כזה — מחק ותתחיל שוב.

דוגמה לסיכום טוב:
"רבים התמקדו ברגעים בהם בית הספר הפך לעוגן בתוך הבלגן — תלמידה שחיכתה לשיחת בוקר, צוות שאימץ יוזמה חדשה דווקא בתקופה הכי קשה. החזרה לשגרה לא תוארה כהקלה אלא כעבודה אקטיבית — 'שגרה שלוחצת בצווארון', כפי שנאמר, שצריך לבנות אותה מחדש ולא לחכות שתחזור מעצמה. בצד הגאווה במה שהחזקנו מעמד, עלה גם כבוד כנה לקושי של מי שעוד לא שם. כמה משתתפות ציינו שהמרחב הקבוצתי פתח חשיבה חדשה — לא רק על בית הספר, אלא על מה זה להיות מנהלת נגישה בתוך משבר."
— יש ציטוטים, פרטים מוחשיים, ניואנס, דיוק."""


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
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    user_prompt = (
        "להלן המשובים שנאספו היום מהמשתתפות והמשתתפים:\n\n"
        f"{feedback_text}\n\n"
        "כתב/י סיכום עשיר ומעוגן בתוכן לפי ההנחיות שקיבלת. "
        "התחל/י ישירות בתוכן הקונקרטי — לא במשפט פתיחה כללי."
    )
    response = client.models.generate_content(
        model=MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=1024,
            temperature=0.85,
        ),
    )
    return (response.text or "").strip()


def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("חסר GEMINI_API_KEY במשתני הסביבה. הגדר אותו ונסה שוב.", flush=True)
        sys.exit(1)

    print(f"מחובר ל-{DB_URL}", flush=True)
    print(f"מודל: {MODEL}", flush=True)
    print(f"בודק כל {POLL_SECONDS} שניות. Ctrl+C לעצירה.\n", flush=True)

    # בדוק מצב נוכחי כדי לא לסכם על בקשה ישנה ברגע ההפעלה
    last_seen = None
    try:
        current = fetch("summaryRequest")
        if current and isinstance(current, dict):
            last_seen = current.get("requestedAt")
            if last_seen:
                print(f"  (בקשה קיימת שנוצרה קודם timestamp={last_seen} — מתעלם ממנה)", flush=True)
    except Exception as e:
        print(f"אזהרה: בעיה בקריאה ראשונית: {e}", flush=True)

    while True:
        try:
            req = fetch("summaryRequest")
            if req and isinstance(req, dict):
                requested_at = req.get("requestedAt")
                if requested_at and requested_at != last_seen:
                    last_seen = requested_at
                    print(f"\nבקשה חדשה התקבלה (timestamp={requested_at})", flush=True)
                    feedback = fetch("feedback") or {}
                    if not feedback:
                        print("  אין משובים — רושם שגיאה", flush=True)
                        put("summary", {"status": "error", "error": "אין עדיין משובים"})
                    else:
                        text = build_feedback_text(feedback)
                        print(f"  נמצאו {len(feedback)} משובים, שולח ל-Gemini...", flush=True)
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
                            print(f"  סיכום נכתב ({len(summary)} תווים):", flush=True)
                            print(f"--- סיכום ---\n{summary}\n---", flush=True)
                        except Exception as e:
                            print(f"  שגיאת Gemini: {e}", flush=True)
                            put("summary", {"status": "error", "error": str(e)[:200]})
            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            print("\nעצירה.", flush=True)
            break
        except Exception as e:
            print(f"אזהרה: {e} — מנסה שוב בעוד {POLL_SECONDS} שניות", flush=True)
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
