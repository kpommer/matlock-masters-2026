from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
import sqlite3
import os
from datetime import datetime

app = FastAPI()
DB_NAME = "golf_entries.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Existing Tables
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, phone TEXT, 
        handicap TEXT, shirt_size TEXT, dietary TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tournaments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, start_date TEXT, end_date TEXT, location TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS fee_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, price REAL, tournament_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER, tournament_id INTEGER, 
        lodging TEXT, golf_events TEXT, meals TEXT, total_price REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # New Scoring Tables
    c.execute('''CREATE TABLE IF NOT EXISTS foursomes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tournament_id INTEGER, team_name TEXT,
        round_type TEXT, tee_time TEXT, scorekeeper_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS foursome_players (
        foursome_id INTEGER, player_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT, foursome_id INTEGER, hole_number INTEGER, 
        strokes INTEGER, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS broadcast_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # Seed Data
    c.execute("SELECT COUNT(*) FROM tournaments")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO tournaments (name, start_date, end_date, location) VALUES ('Matlock Masters 2026', '2026-09-10', '2026-09-11', '8 Hazel, Matlock')")
        fees = [("Pro-Am", 50.0, 1), ("Masters Championship", 75.0, 1), ("Lodging (Fri Night)", 100.0, 1), ("Lodging (Sat Night)", 100.0, 1), ("Friday Dinner", 40.0, 1), ("Saturday Dinner", 60.0, 1), ("Saturday Breakfast", 20.0, 1), ("Sunday Breakfast", 20.0, 1)]
        c.executemany("INSERT INTO fee_schedule (item_name, price, tournament_id) VALUES (?,?,?)", fees)
        
        # Seed a sample foursome for testing
        c.execute("INSERT INTO foursomes (tournament_id, team_name, round_type, tee_time) VALUES (1, 'The Eagles', 'Championship', '10:00 AM')")
        c.execute("INSERT INTO broadcast_log (message) VALUES ('🎙️ **BROADCASTER:** Welcome to the Matlock Masters! The leaderboard is live.')")

    conn.commit()
    conn.close()

init_db()

# --- AI Broadcaster Logic ---
def generate_commentary(foursome_name, hole, score):
    par = 4 
    diff = score - par
    gifs = {
        "eagle": "https://media.giphy.com/media/l0MYt5jPR6uXN3QaI/giphy.gif", # Win/Success
        "birdie": "https://media.giphy.com/media/3o6fJdY47K6wU8Y88E/giphy.gif", # High Five
        "par": "https://media.giphy.com/media/l0HlHJGHe3yAMhdQY/giphy.gif", # Thumbs up
        "bogey": "https://media.giphy.com/media/3o7TKs600K0XN3QaI/giphy.gif", # Oh no
        "double": "https://media.giphy.com/media/3o7qDSOvfaIL9d3Msw/giphy.gif"  # Facepalm
    }
    
    if diff <= -2: return f"🦅 **UNBELIEVABLE!** {foursome_name} carded a {score} on Hole {hole}! <img src='{gifs['eagle']}' width='100'>"
    if diff == -1: return f"🔥 **BIRDIE!** {foursome_name} is heating up! <img src='{gifs['birdie']}' width='100'>"
    if diff == 0: return f"⛳ **PAR.** Steady as she goes. <img src='{gifs['par']}' width='100'>"
    if diff == 1: return f"⚠️ **BOGEY.** A little trouble on Hole {hole}. <img src='{gifs['bogey']}' width='100'>"
    return f"😱 **OUCH!** A {score} on Hole {hole}. <img src='{gifs['double']}' width='100'>"

@app.get("/")
async def home():
    return HTMLResponse(content="""<!DOCTYPE html><html><head><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-green-50 p-4"><div class="max-w-md mx-auto bg-white p-6 rounded-xl shadow-lg">
    <h1 class="text-2xl font-bold text-green-800 text-center">Matlock Masters 2026</h1>
    <div class="mt-6 space-y-2 text-center">
        <a href="/register" class="block w-full bg-green-700 text-white p-4 rounded font-bold">Register for Tournament</a>
        <a href="/leaderboard" class="block w-full bg-blue-600 text-white p-4 rounded font-bold">Live Leaderboard</a>
        <a href="/admin" class="block w-full bg-gray-700 text-white p-4 rounded font-bold">Admin Dashboard</a>
    </div></div></body></html>""")

@app.get("/register")
async def register_form():
    # (Using the previous registration form logic here for brevity)
    return HTMLResponse(content="<h1>Registration Form Placeholder</h1><p>See previous version for full form.</p>")

@app.get("/leaderboard")
async def leaderboard():
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT f.team_name, SUM(s.strokes) as total, COUNT(s.hole_number) as holes_played 
                 FROM foursomes f LEFT JOIN scores s ON f.id = s.foursome_id 
                 GROUP BY f.id ORDER BY total ASC""")
    teams = c.fetchall()
    
    c.execute("SELECT message, timestamp FROM broadcast_log ORDER BY id DESC LIMIT 5")
    broadcast = c.fetchall()
    conn.close()

    rows = ""
    for t in teams:
        status = f"Hole {t['holes_played']}" if t['holes_played'] > 0 else "Not Started"
        score = t['total'] if t['total'] else 0
        rows += f"<tr><td class='p-3 font-bold'>{t['team_name']}</td><td class='p-3 text-center'>{score}</td><td class='p-3 text-gray-500'>{status}</td></tr>"

    broadcast_html = "".join([f"<div class='p-2 border-b text-sm'>{b['message']} <span class='text-xs text-gray-400 float-right'>{b['timestamp'][11:16]}</span></div>" for b in broadcast])

    return HTMLResponse(content=f"""<!DOCTYPE html><html><head><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-100 p-4"><div class="max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold text-center mb-4">🏆 Live Leaderboard</h1>
    <div class="bg-white rounded-lg shadow overflow-hidden"><table class="w-full">{rows}</table></div>
    <h2 class="text-xl font-bold mt-6 mb-2">🎙️ Live Broadcast</h2>
    <div class="bg-white rounded-lg shadow p-4">{broadcast_html}</div>
    <div class="mt-4 text-center"><a href="/score-entry" class="text-blue-600 underline">Enter Scores (Scorekeepers Only)</a></div>
    </div></body></html>""")

@app.get("/score-entry")
async def score_entry_form():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, team_name FROM foursomes")
    teams = c.fetchall()
    conn.close()
    options = "".join([f"<option value='{t['id']}'>{t['team_name']}</option>" for t in teams])
    
    return HTMLResponse(content=f"""<!DOCTYPE html><html><head><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-green-50 p-4"><div class="max-w-md mx-auto bg-white p-6 rounded-xl shadow-lg">
    <h1 class="text-xl font-bold mb-4">Enter Score</h1>
    <form action="/submit-score" method="POST" class="space-y-4">
        <div><label class="block font-bold">Foursome</label><select name="foursome_id" class="w-full p-3 border rounded">{options}</select></div>
        <div><label class="block font-bold">Hole</label><input type="number" name="hole" min="1" max="18" class="w-full p-3 border rounded" required></div>
        <div><label class="block font-bold">Team Strokes</label><input type="number" name="strokes" class="w-full p-3 border rounded" required></div>
        <button type="submit" class="w-full bg-green-700 text-white p-4 rounded font-bold">Post Score</button>
    </form></div></body></html>""")

@app.post("/submit-score")
async def submit_score(foursome_id: int = Form(...), hole: int = Form(...), strokes: int = Form(...)):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO scores (foursome_id, hole_number, strokes) VALUES (?,?,?)", (foursome_id, hole, strokes))
    
    c.execute("SELECT team_name FROM foursomes WHERE id = ?", (foursome_id,))
    team = c.fetchone()
    
    commentary = generate_commentary(team['team_name'], hole, strokes)
    c.execute("INSERT INTO broadcast_log (message) VALUES (?)", (commentary,))
    
    conn.commit()
    conn.close()
    return HTMLResponse(content=f"<h1 style='text-align:center; padding-top:50px;'>Score Posted! <br><a href='/leaderboard' class='text-blue-600'>Back to Leaderboard</a></h1>")

@app.get("/admin")
async def admin():
    return HTMLResponse(content="<h1>Admin Dashboard</h1><p>Full admin features coming soon.</p>")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
