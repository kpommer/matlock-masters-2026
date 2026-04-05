from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import sqlite3
import os

app = FastAPI()
DB_NAME = "golf_entries.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS entries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, phone TEXT, 
                  friday_attendance INTEGER, saturday_attendance INTEGER, lodging TEXT,
                  proam INTEGER, championship INTEGER, average_score TEXT,
                  friday_meal INTEGER, saturday_meal INTEGER, dietary TEXT, shirt_size TEXT)''')
    conn.commit()
    conn.close()

init_db()

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Matlock Masters 2026</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-green-50 p-4">
    <div class="max-w-md mx-auto bg-white p-6 rounded-xl shadow-lg">
        <h1 class="text-2xl font-bold text-green-800 text-center">Matlock Masters 2026</h1>
        <p class="text-center text-gray-600 mb-6">Sept 10-11 • 8 Hazel, Matlock</p>
        <form action="/submit" method="POST" class="mt-6 space-y-4">
            <div><label class="block font-bold">Name</label><input type="text" name="name" class="w-full p-3 border rounded" required></div>
            <div><label class="block font-bold">Email</label><input type="email" name="email" class="w-full p-3 border rounded" required></div>
            <div><label class="block font-bold">Phone</label><input type="tel" name="phone" class="w-full p-3 border rounded" required></div>
            <div><label class="block font-bold">Avg Score</label><input type="number" name="average_score" class="w-full p-3 border rounded" required></div>
            <button type="submit" class="w-full bg-green-700 text-white p-4 rounded font-bold text-lg">Register</button>
        </form>
    </div>
</body>
</html>
"""

@app.get("/")
async def home():
    return HTMLResponse(content=INDEX_HTML)

@app.post("/submit")
async def submit(
    name: str = Form(...), email: str = Form(...), phone: str = Form(...),
    average_score: str = Form(...), friday_attendance: str = Form(None),
    saturday_attendance: str = Form(None), lodging: str = Form("No"),
    proam: str = Form(None), championship: str = Form(None),
    friday_meal: str = Form(None), saturday_meal: str = Form(None),
    dietary: str = Form(""), shirt_size: str = Form("M")
):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO entries (name, email, phone, average_score, friday_attendance, 
                 saturday_attendance, lodging, proam, championship, friday_meal, saturday_meal, dietary, shirt_size)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (name, email, phone, average_score, 1 if friday_attendance else 0,
               1 if saturday_attendance else 0, lodging, 1 if proam else 0,
               1 if championship else 0, 1 if friday_meal else 0, 1 if saturday_meal else 0,
               dietary, shirt_size))
    conn.commit()
    conn.close()
    return HTMLResponse(content="<h1 style='text-align:center; padding-top:50px;'>Thanks for registering, " + name + "!</h1>")

@app.get("/admin")
async def admin():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM entries ORDER BY id DESC")
    entries = c.fetchall()
    conn.close()
    
    rows = ""
    for e in entries:
        events = []
        if e['proam']: events.append("Pro-Am")
        if e['championship']: events.append("Champ")
        
        rows += f"""
        <tr class="border-b hover:bg-gray-50">
            <td class="p-3 font-medium">{e['name']}</td>
            <td class="p-3">{e['email']}</td>
            <td class="p-3">{e['phone']}</td>
            <td class="p-3 text-center">
                {'✅' if e['friday_attendance'] else '❌'} / {'✅' if e['saturday_attendance'] else '❌'}
            </td>
            <td class="p-3 text-center">{e['lodging']}</td>
            <td class="p-3 text-sm">{', '.join(events) if events else 'None'}</td>
            <td class="p-3 text-center">{e['average_score']}</td>
            <td class="p-3 text-center">
                {'✅' if e['friday_meal'] else '❌'} / {'✅' if e['saturday_meal'] else '❌'}
            </td>
            <td class="p-3 text-sm text-gray-500">{e['dietary'] or '-'}</td>
            <td class="p-3 text-center font-bold">{e['shirt_size']}</td>
        </tr>"""

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin - Matlock Masters</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 p-4">
        <div class="max-w-6xl mx-auto bg-white p-6 rounded-xl shadow-lg">
            <h1 class="text-2xl font-bold text-green-800 mb-6">Tournament Entries ({len(entries)})</h1>
            <div class="overflow-x-auto">
                <table class="min-w-full text-sm">
                    <thead>
                        <tr class="bg-green-50 text-green-900">
                            <th class="p-3 text-left">Name</th>
                            <th class="p-3 text-left">Email</th>
                            <th class="p-3 text-left">Phone</th>
                            <th class="p-3 text-center">Fri/Sat</th>
                            <th class="p-3 text-left">Lodging</th>
                            <th class="p-3 text-left">Events</th>
                            <th class="p-3 text-center">Avg</th>
                            <th class="p-3 text-center">Meals (F/S)</th>
                            <th class="p-3 text-left">Dietary</th>
                            <th class="p-3 text-center">Shirt</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
