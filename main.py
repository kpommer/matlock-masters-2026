from fastapi import FastAPI, Form, Request
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
    # Players Table
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT, email TEXT UNIQUE, phone TEXT, 
        handicap TEXT, shirt_size TEXT, dietary TEXT
    )''')
    # Tournaments Table
    c.execute('''CREATE TABLE IF NOT EXISTS tournaments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT, start_date TEXT, end_date TEXT, location TEXT
    )''')
    # Fee Schedule Table
    c.execute('''CREATE TABLE IF NOT EXISTS fee_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        item_name TEXT, price REAL, tournament_id INTEGER
    )''')
    # Entries Table
    c.execute('''CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        player_id INTEGER, tournament_id INTEGER, 
        lodging TEXT, golf_events TEXT, meals TEXT, 
        total_price REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Seed default tournament and fees if empty
    c.execute("SELECT COUNT(*) FROM tournaments")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO tournaments (name, start_date, end_date, location) VALUES ('Matlock Masters 2026', '2026-09-10', '2026-09-11', '8 Hazel, Matlock')")
        fees = [
            ("Pro-Am", 50.0, 1), ("Masters Championship", 75.0, 1),
            ("Lodging (Fri Night)", 100.0, 1), ("Lodging (Sat Night)", 100.0, 1),
            ("Friday Dinner", 40.0, 1), ("Saturday Dinner", 60.0, 1),
            ("Saturday Breakfast", 20.0, 1), ("Sunday Breakfast", 20.0, 1)
        ]
        c.executemany("INSERT INTO fee_schedule (item_name, price, tournament_id) VALUES (?,?,?)", fees)
    
    conn.commit()
    conn.close()

init_db()

@app.get("/")
async def home():
    return HTMLResponse(content="""
    <!DOCTYPE html><html><head><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-green-50 p-4"><div class="max-w-md mx-auto bg-white p-6 rounded-xl shadow-lg">
    <h1 class="text-2xl font-bold text-green-800 text-center">Matlock Masters 2026</h1>
    <form action="/submit" method="POST" class="mt-6 space-y-4">
        <div><label class="block font-bold">Name</label><input type="text" name="name" class="w-full p-3 border rounded" required></div>
        <div><label class="block font-bold">Email</label><input type="email" name="email" class="w-full p-3 border rounded" required></div>
        <div><label class="block font-bold">Phone</label><input type="tel" name="phone" class="w-full p-3 border rounded" required></div>
        <div><label class="block font-bold">Handicap</label><input type="text" name="handicap" class="w-full p-3 border rounded"></div>
        <div><label class="block font-bold">Shirt Size</label><select name="shirt_size" class="w-full p-3 border rounded"><option>M</option><option>L</option><option>XL</option></select></div>
        <div class="border-t pt-4"><label class="block font-bold">Golf Events</label>
            <label class="flex items-center"><input type="checkbox" name="golf" value="Pro-Am" class="m-2"> Pro-Am ($50)</label>
            <label class="flex items-center"><input type="checkbox" name="golf" value="Masters Championship" class="m-2"> Championship ($75)</label>
        </div>
        <div class="border-t pt-4"><label class="block font-bold">Lodging at 8 Hazel</label>
            <label class="flex items-center"><input type="checkbox" name="lodging" value="Fri Night" class="m-2"> Friday ($100)</label>
            <label class="flex items-center"><input type="checkbox" name="lodging" value="Sat Night" class="m-2"> Saturday ($100)</label>
        </div>
        <div class="border-t pt-4"><label class="block font-bold">Meals</label>
            <label class="flex items-center"><input type="checkbox" name="meals" value="Fri Dinner" class="m-2"> Fri Dinner ($40)</label>
            <label class="flex items-center"><input type="checkbox" name="meals" value="Sat Dinner" class="m-2"> Sat Dinner ($60)</label>
            <label class="flex items-center"><input type="checkbox" name="meals" value="Sat Breakfast" class="m-2"> Sat Breakfast ($20)</label>
            <label class="flex items-center"><input type="checkbox" name="meals" value="Sun Breakfast" class="m-2"> Sun Breakfast ($20)</label>
        </div>
        <button type="submit" class="w-full bg-green-700 text-white p-4 rounded font-bold text-lg">Register</button>
    </form></div></body></html>
    """)

@app.post("/submit")
async def submit(
    request: Request, name: str = Form(...), email: str = Form(...), 
    phone: str = Form(...), handicap: str = Form(""), shirt_size: str = Form("M"),
    golf: list = Form(None), lodging: list = Form(None), meals: list = Form(None)
):
    conn = get_db()
    c = conn.cursor()
    
    # Get or Create Player
    c.execute("SELECT id FROM players WHERE email = ?", (email,))
    player = c.fetchone()
    if not player:
        c.execute("INSERT INTO players (name, email, phone, handicap, shirt_size) VALUES (?,?,?,?,?)", 
                  (name, email, phone, handicap, shirt_size))
        player_id = c.lastrowid
    else:
        player_id = player[0]
        c.execute("UPDATE players SET name=?, phone=?, handicap=?, shirt_size=? WHERE id=?", 
                  (name, phone, handicap, shirt_size, player_id))

    # Calculate Price
    total = 0
    items = (golf or []) + (lodging or []) + (meals or [])
    for item in items:
        c.execute("SELECT price FROM fee_schedule WHERE item_name = ? AND tournament_id = 1", (item,))
        fee = c.fetchone()
        if fee: total += fee[0]

    # Create Entry
    c.execute("INSERT INTO entries (player_id, tournament_id, lodging, golf_events, meals, total_price) VALUES (?,?,?,?,?,?)",
              (player_id, 1, ", ".join(lodging or []), ", ".join(golf or []), ", ".join(meals or []), total))
    
    conn.commit()
    conn.close()
    return HTMLResponse(content=f"<h1 style='text-align:center; padding-top:50px;'>Thanks {name}! Total: ${total:.2f}</h1>")

@app.get("/admin")
async def admin():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT e.id, p.name, e.golf_events, e.lodging, e.meals, e.total_price FROM entries e JOIN players p ON e.player_id = p.id ORDER BY e.id DESC")
    rows = c.fetchall()
    conn.close()
    
    html_rows = ""
    for r in rows:
        html_rows += f"<tr><td class='p-2'>{r['name']}</td><td class='p-2'>{r['golf_events']}</td><td class='p-2'>{r['lodging']}</td><td class='p-2'>{r['meals']}</td><td class='p-2 font-bold'>${r['total_price']:.2f}</td></tr>"

    return HTMLResponse(content=f"""
    <!DOCTYPE html><html><head><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-100 p-4"><div class="max-w-4xl mx-auto bg-white p-6 rounded-xl shadow-lg">
    <h1 class="text-2xl font-bold text-green-800 mb-6">Entries</h1>
    <table class="min-w-full border"><thead class="bg-green-50">
    <tr><th class="p-2 text-left">Player</th><th class="p-2 text-left">Golf</th><th class="p-2 text-left">Lodging</th><th class="p-2 text-left">Meals</th><th class="p-2 text-left">Total</th></tr>
    </thead><tbody>{html_rows}</tbody></table></div></body></html>
    """)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
