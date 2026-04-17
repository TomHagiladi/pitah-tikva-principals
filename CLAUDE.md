# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## מה זה

אפליקציית Web חד-פעמית לסדנת **Vibe Coding** עם מנהלי בתי ספר בפתח תקווה, **26.4.2026**, ~40 משתתפים (10 קבוצות של 4). נכנסת דרך לינק וואטסאפ, מנחה את הקבוצות בעבודה עצמאית, ובמקביל מהווה הדגמה (**Modeling**) של AI ככלי הנחיה בתוך מפגשי תום הגלעדי. חד-פעמית — אחרי 26.4 האפליקציה תושבת.

**Live URL:** https://tomhagiladi.github.io/pitah-tikva-principals/ (GitHub Pages, branch=main, path=/)
**Repo:** https://github.com/TomHagiladi/pitah-tikva-principals (public)

## Commands

```bash
# הפעלה מקומית
start index.html                                                     # משתתף רגיל
start "index.html?dashboard=true&key=pesga2026"                      # דשבורד מנחה — Control view
start "index.html?dashboard=true&key=pesga2026&view=display"         # דשבורד מנחה — Display view (למקרן)
start "index.html?fresh=1"                                           # משתתף עם זהות חדשה (לבדיקות רב-משתמש במחשב אחד)
start "index.html?screen=feedback"                                   # קפיצה למסך X — welcome/waiting/group/poem/battery/discussion/upload/feedback/done

# פתיחה מדויקת דרך Chrome (כשיש ?query params, start מתבלבל)
"C:/Program Files/Google/Chrome/Application/chrome.exe" "file:///C:/Users/tomha/claude%20code/workshops/pitah-tikva-principals/index.html?dashboard=true&key=pesga2026"

# ניקוי Firebase בזמן בדיקות (הדשבורד מספק כפתור "אתחול הסדנה" שעושה את אותו הדבר)
curl -X DELETE "https://pitah-tikva-principals-default-rtdb.europe-west1.firebasedatabase.app/.json"

# סקריפט סיכום — חייב לרוץ בטרמינל בזמן הסדנה (GEMINI_API_KEY נדרש בסביבה)
python summarize.py

# פריסה: כל push ל-main של GitHub repo `TomHagiladi/pitah-tikva-principals` מתעדכן אוטומטית ב-GitHub Pages תוך ~1-2 דק'
git push   # → https://tomhagiladi.github.io/pitah-tikva-principals/
```

אין build step, אין lint, אין tests. SPA קובץ יחיד.

## ארכיטקטורה

**קובץ אחד — [index.html](index.html)** מכיל את כל ה-HTML, CSS ו-JS inline. אין bundler, אין דפנדנסיות npm. הספריות היחידות: Firebase SDK 10.7.1 (app + database), Google Fonts (Rubik + Caveat), Font Awesome 6.

### שלוש תצוגות מאותו קובץ
- **משתתף** (default) — 8 מסכים לינאריים על המובייל: welcome → waiting → group → poem → battery → discussion → upload → **feedback** → done
- **מנחה Control** (`?dashboard=true&key=pesga2026`) — הפאנל הפרטי של תום: ניהול קבוצות, כפתורי פעולה, מד אנרגיה קבוצתי, קיר תמונות, סיכום
- **מנחה Display** (`?dashboard=true&key=pesga2026&view=display`) — נפרס על המקרן לכיתה. מסתיר את כל חלק הניהול; מציג רק מד אנרגיה קבוצתי, תובנות מהמשובים (סיכום Claude), וקיר תמונות

הבחירה נעשית ב-boot דרך `isDashboardMode()` + `getDashboardView()`. ה-display מופעל דרך class על body שמוסיף `body.dashboard-display` ומשנה את ה-grid-template-areas של הדשבורד.

**כפתור מעבר צף** (`#btn-view-toggle`) — בפינה עליונה של הדשבורד, מאפשר לתום להחליף בין Control ל-Display בלי לפתוח כרטיסייה חדשה. הכפתור גם מעדכן את ה-URL דרך `history.replaceState` כדי שאפשר יהיה לקבע את הכרטיסייה במצב מסוים. הכפתור מעומעם ל-opacity: 0.4 ב-Display mode כדי שלא יפריע על המקרן (חוזר ל-100% ב-hover).

### Firebase Realtime Database schema

```
/participants/{userId}  = { name, joinedAt, group: "1"|null, energy: 0-100, hasPhoto: bool, readyAt, currentScreen }
/groups/{groupId}       = { members: [uid, uid, ...], size: 3|4, createdAt, timer: {...}, currentScreen }
/groups/{id}/timer      = { state: 'idle'|'running'|'paused'|'ended', speakerIndex, speakerCount,
                            personalEndsAt, groupEndsAt, personalRemainingMs, groupRemainingMs }
/groups/{id}/currentScreen = 'screen-poem'|'screen-battery'|'screen-upload'|...  (Group-level sync — see below)
/photos/{userId}        = { data: "data:image/jpeg;base64,...", group, name, uploadedAt }
/feedback/{userId}      = { text, name, group, submittedAt }
/summaryRequest         = { requestedAt, requestedBy }  (written by control dashboard button)
/summary                = { status: 'generating'|'ready'|'error', text, generatedAt, feedbackCount, error }
```

### Group-level screen sync (Pattern)
"מצאנו ואנחנו מוכנים", "קראנו ממשיכים", "סיימנו ממשיכים" — בכל אחד מהכפתורים האלה לחיצה אחת של חבר/ת קבוצה מקדמת את כל הקבוצה. המנגנון:
- כפתור כותב ל-`/groups/{id}/currentScreen` את המסך הבא
- כל לקוח בקבוצה מאזין ל-node הזה ומקפיץ `goToScreen(target)` — עם הגנה שהולכת רק קדימה (לפי `SCREEN_ORDER`)
- **אל תדחוף סנכרון על מסכים אישיים** (battery, upload, feedback, done) — שם כל משתתף ממשיך עצמאית
- אם תוסיף מסך מסונכרן נוסף — הוסף אותו ל-`SCREEN_ORDER` והפעל `syncGroupScreen('screen-x')` אחרי `goToScreen` בכפתור

**הפרדת `/photos/` מ-`/participants/`** קריטית: תמונות base64 (~200KB כל אחת) יוצרות רעש ברוחב פס אם הן ב-`/participants`, כי הדשבורד מאזין ל-`participants` כל הזמן. ב-`/photos/` הן נטענות רק בדשבורד דרך `child_added` (כל תמונה כ-delta נפרד, לא טעינה מחדש של כל האוסף).

### למה base64 ב-RTDB ולא Firebase Storage
Firebase עדכנה מדיניות (2024): Storage דורש שדרוג ל-**Blaze plan** (עם כרטיס אשראי), גם אם בפועל השימוש בטווח החינמי. פתרון: תמונות נשמרות כ-base64 dataURL ב-RTDB (שנשאר ב-Spark חינמי). client-side resize ל-800px + JPEG quality 0.7 נותן ~200-250KB לתמונה. 40 משתתפים × 250KB = ~10MB, בנוחות בתוך ה-1GB של RTDB free tier. הפיתרון הזה **חייב להישאר** כל עוד Firebase לא מחזירה את Storage החינמי.

### Synchronized Group Timer — החלק המורכב ביותר

במסך הדיון, **כל חברי הקבוצה רואים את אותו הטיימר** למרות שכל אחד בטלפון שלו. Source of truth: `/groups/{id}/timer`. כל לקוח:

1. נרשם ל-`.info/serverTimeOffset` (פעם אחת ב-boot) כדי לסנכרן את השעון המקומי עם שרת Firebase
2. נרשם ל-`groups/{id}/timer` עם `.on('value')` כשנכנסים למסך הדיון
3. מחשב תצוגה מקומית מ-state + serverNow() ב-setInterval של 500ms

State transitions נעשות **בתוך transaction** כדי למנוע race conditions כשמספר לקוחות לוחצים יחד:
- `running` ↔ `paused` (אוטומטי כש-`personalEndsAt <= serverNow()` — הלקוח הראשון שמגלה זאת עושה transaction שמעביר ל-paused; שאר הלקוחות transaction יחזיר abort)
- "הדובר/ת הבא/ה" — `speakerCount++`, reset של `personalEndsAt`, שמירת `groupRemainingMs` (שלא מתאפס בין דוברים)
- `speakerCount >= size` → הכפתור נסגר (כולם דיברו)

כשמוסיפים פיצ'ר חדש שמערב סנכרון בין חברי קבוצה — השתמש באותה תבנית (shared state + server time + transactions).

### מצב Fresh (debug)
`?fresh=1` מחליף `localStorage` ב-`sessionStorage` דרך המשתנה `identityStorage`. קריטי לבדיקות רב-משתמש במחשב אחד — Chrome incognito **משתף localStorage בין חלונות**. בטלפונים אמיתיים לא רלוונטי, כל משתמש על המכשיר שלו.

## Gotchas מהבנייה

- **גודל קבוצה 5 בלתי אפשרי** — אלגוריתם החלוקה תומך רק ב-3/4. `computeGroupsPreview()` מחזיר `{impossible: true}` עבור 1, 2, 5. הדשבורד מציג אזהרה במקום ללחוץ.
- **השיר "לובשת שגרה" בזכויות יוצרים** — המחברת **טלי ורסנו-אייסמן**. הטקסט המלא משובץ inline ב-`#poem-text` (לא לינק חיצוני) — תום אישר. אם יהיו התלבטויות משפטיות, חזור למודל של בית-פתיחה בלבד + קרדיט.
- **סולי הסוללה דמות מסחרית** של סיגל אלבז ([souly.co.il](https://www.souly.co.il)) — **אסור להשתמש**. מה שיש באפליקציה: (א) מד סוללה ב-CSS טהור (battery-visual) שמשקף את ה-slider; (ב) **שלוש דמויות סוללה מקוריות** ב-`assets/`, שנוצרו דרך Imagen 4 (Gemini):
  - `battery-drained.png` — מותשת, משמאל ל-slider במסך המשתתף (ליד "אני גמור/ה")
  - `battery-energetic.png` — נמרצת, מימין ל-slider (ליד "אני מלא/ת אנרגיה")
  - `battery-pondering.png` — מהרהרת, מוצגת רק בדשבורד Display (class `.battery-pondering-img` שמוסתר עד ש-body מקבל `.dashboard-display`)
- **שני כפתורי העלאה**: `#btn-take-photo` מפעיל `<input capture="environment">` (פותח מצלמה בטלפון), `#btn-choose-photo` מפעיל `<input>` בלי capture (פותח גלריה). שני הקלטים מחוברים ל-`handlePhotoSelection`. התנהגות שונה ב-iOS vs Android — בדיקה במכשירים אמיתיים נדרשת לפני 26.4.
- **Skip-upload button** (`#btn-skip-upload`) — מופיע אצל חברי קבוצה ברגע ש-`listenForGroupPhoto()` מזהה שמישהו אחר באותה קבוצה כבר העלה תמונה. מקדם אותם ל-`screen-feedback` בלי שיצטרכו להעלות בעצמם (תמיכה במצב "תמונה קבוצתית אחת"). הלחיצה **לא** מסנכרנת את הקבוצה (upload/feedback/done אישיים).
- **Persistent group header** (`#group-header`) מוסתר במסכי welcome/waiting/dashboard/group ומוצג בכל השאר. הלוגיקה ב-`showScreen()`.
- **Chrome ב-Windows ו-`start`** — query strings (`?dashboard=true&key=...`) מתבלבלים. חייב לפתוח דרך chrome.exe ישירות, ראה commands למעלה.

## תלויות חיצוניות

- **Firebase config** מוטמע ישירות ב-`index.html` (FIREBASE_CONFIG). הפרויקט: `pitah-tikva-principals` (region: europe-west1, Spark plan חינמי, test mode — rules פתוחות ל-30 יום).
- **ADMIN_KEY** קבוע ב-`index.html` = `'pesga2026'`. כל שינוי דורש עדכון של הלינק שתום שומר.
- **Gemini API** — הסיכום של המשובים דורש `summarize.py` לרוץ על הלפטופ של תום בזמן הסדנה. `GEMINI_API_KEY` חייב להיות ב-env (מוגדר אצל תום כ-Windows env var). המפתח **לא** מוטמע ב-index.html (client-side → יחשוף את המפתח).
  - **הגבלת IP של המפתח** — תום הסיר זמנית בגלל שה-IP הציבורי שלו דינמי. החשיפה נמוכה: Free tier (50 תמונות/יום, quota גבוה לטקסט), המפתח ב-env בלבד. אם תחזור להגביל — זכור שכל פעם שה-ISP מחליף IP תתקע שוב.
- **למה Gemini ולא Claude** — הוחלפנו מ-Claude sonnet-4-6 ל-Gemini 2.5-flash אחרי שהקרדיט ב-Anthropic אזל באמצע ההכנה. אם חוזרים לקלוד, זכור להחזיר את `ANTHROPIC_API_KEY` ולעדכן את `MODEL` + ה-API call ב-`summarize.py`.
- אחרי 26.4.2026 אפשר למחוק את פרויקט Firebase לגמרי + ארכב את הריפו.

## Summary pipeline (חשוב לארכיטקטורה)

המסך feedback שומר טקסט חופשי אנונימי ב-`/feedback/{uid}`. הסיכום נוצר בזרימה הבאה:

1. תום לוחץ "צור סיכום משובים" בדשבורד הפרטי (control view)
2. הדשבורד כותב ל-`/summary = {status: "pending"}` (פידבק מיידי שנראה ב-UI) ואז ל-`/summaryRequest = {requestedAt: <timestamp>}`
3. `summarize.py` (רץ בטרמינל על הלפטופ של תום) בודק את `/summaryRequest` כל 3 שניות, משווה ל-`last_seen`
4. ברגע שהוא רואה timestamp חדש — כותב `/summary = {status: "generating"}`, קורא את `/feedback`, שולח ל-**Gemini 2.5-flash**, וכותב את התוצאה ל-`/summary = {status: "ready", text, generatedAt}`
5. הדשבורד (פרטי וציבורי) מאזין ל-`/summary` ומציג את הסטטוסים (`pending` → `generating` → `ready`/`error`) אוטומטית דרך `renderSummary()`

**חייבים:**
- הסקריפט חייב לרוץ לפני שתום לוחץ על הכפתור. אם לא רץ — הסטטוס נתקע ב-`pending`.
- **Gemini thinking mode חייב להיות כבוי** (`thinking_budget=0`). אחרת thinking tokens אוכלים את תקציב הפלט ו-סיכומים בעברית נחתכים באמצע משפט.
- ה-prompt ב-`summarize.py` כולל דוגמאות מפורשות של פלט **פסול** (קלישאות כמו "חוויה עשירה ומגוונת") ו**טוב** (ציטוטים, פרטים מוחשיים, ניואנס). אל תחליש/י את הדוגמאות — Gemini נוטה לכללי בלעדיהן.
