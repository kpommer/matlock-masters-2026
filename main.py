from fastapi import FastAPI, Request, Form
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

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/", response_class=HTMLResponse)
async def get_form():
    content = read_file("templates/index.html")
    return content

@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    friday_attendance: str = Form(None),
    saturday_attendance: str = Form(None),
    lodging: str = Form(...),
    proam: str = Form(None),
    championship: str = Form(None),
    average_score: str = Form(...),
    friday_meal: str = Form(None),
    saturday_meal: str = Form(None),
    dietary: str = Form(""),
    shirt_size: str = Form(...)
):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO entries 
                 (name, email, phone, friday_attendance, saturday_attendance, lodging,
                  proam, championship, average_score, friday_meal, saturday_meal, dietary, shirt_size)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (name, email, phone, 1 if friday_attendance else 0, 1 if saturday_attendance else 0,
               lodging, 1 if proam else 0, 1 if championship else 0, average_score,
               1 if friday_meal else 0, 1 if saturday_meal else 0, dietary, shirt_size))
    conn.commit()
    conn.close()
    
    content = read_file("templates/index.html")
    # Simple string replacement to show the success message
    content = content.replace('{% if message %}', '<div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">Thanks for registering! See you in Matlock.</div>')
    content = content.replace('{% endif %}', '')
    return content

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM entries")
    entries = c.fetchall()
    conn.close()
    
    rows = ""
    for entry in entries:
        events = []
        if entry['proam']: events.append("Pro-Am")
        if entry['championship']: events.append("Championship")
        rows += f"""
        <tr class="border-b">
            <td class="p-2">{entry['name']}</td>
            <td class="p-2">{", ".join(events)}</td>
            <td class="p-2">{entry['lodging']}</td>
            <td class="p-2">{entry['average_score']}</td>
        </tr>
        """
    
    content = read_file("templates/admin.html")
    content = content.replace('{% for entry in entries %}', rows)
    content = content.replace('{% endfor %}', '')
    # Replace the jinja variables in the row template with the actual values from the loop
    # (Since we are pre-rendering, we can just replace the whole loop block)
    return content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
