# מטעינים מחדש — אפליקציית סדנת מנהלים

אפליקציית Web חד-פעמית לסדנת מנהלי בתי ספר בפסגה פתח תקווה (26.4.2026).

## הפעלה מהירה

### במחשב (פיתוח)
```
לחיצה כפולה על index.html
```
או:
```bash
cd "C:\Users\tomha\claude code\workshops\pitah-tikva-principals"
start index.html
```

### מסך מנחה (Admin Dashboard)
```
index.html?dashboard=true&key=<המפתח-הסודי>
```
המפתח הסודי מוגדר בתוך `index.html` (חפש `ADMIN_KEY`).

### באונליין (ביום הסדנה)
```
https://tomhagiladi.github.io/pitah-tikva-principals
```
שלח את הלינק הזה במדבקת וואטסאפ למנהלים.

## צעד חד-פעמי: הקמת Firebase

1. היכנס ל-[console.firebase.google.com](https://console.firebase.google.com)
2. לחץ "Add project" → שם: `pitah-tikva-principals`
3. הפעל **Realtime Database** (Region: europe-west1, מצב Test)
4. הפעל **Storage** (מצב Test)
5. העתק את ה-Firebase Config מהגדרות הפרויקט → הדבק ב-`index.html` בסוף (שורה עם `FIREBASE_CONFIG = {...}`)

אחרי הסדנה אפשר למחוק את הפרויקט מ-Firebase (שומר על עלויות = 0).

## בדיקה לפני הסדנה

1. פתח 4 חלונות incognito → רשום 4 שמות שונים
2. פתח חלון חמישי עם `?dashboard=true&key=...` → לחץ "חלוקת קבוצות"
3. וידוא שכל 4 החלונות עוברים למסך 2 עם השמות הנכונים
4. עבור דרך 6 המסכים
5. העלה תמונה → וידוא שהיא מופיעה בקולאז' בדשבורד

## מבנה

- `index.html` — כל האפליקציה (HTML + CSS + JS)
- `assets/battery.png` — איור הסוללה
- `CLAUDE.md` — תיעוד לסוכני AI עתידיים

## מצב נוכחי של תכנים

- ✅ מבנה 6 המסכים
- ✅ אלגוריתם חלוקת קבוצות
- ✅ Firebase integration
- ⏳ טקסט השיר "לובשת שגרה" (בית פתיחה + קרדיט; טקסט מלא ממתין לירדנה/יעל)
- ✅ מד סוללה מקורי (Gemini)
