from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DB_NAME = "golf_entries.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS entries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, phone TEXT, 
                  friday_attendance INTEGER, saturday_attendance INTEGER, lodging TEXT,
                  proam INTEGER, championship INTEGER, average_score TEXT,
                  friday_meal INTEGER, saturday_meal INTEGER, dietary TEXT, shirt_size TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
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
    conn = sqlite3.connect(DB_NAME)
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
    return templates.TemplateResponse("index.html", {"request": request, "message": "Thanks for registering! See you in Matlock."})

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM entries")
    entries = c.fetchall()
    conn.close()
    return templates.TemplateResponse("admin.html", {"request": request, "entries": entries})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
