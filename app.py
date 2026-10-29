import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

app = Flask(__name__)
app.secret_key = "threat_vector_secret_key"

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    user = conn.execute("SELECT * FROM users WHERE username = ?", ("admin",)).fetchone()
    if not user:
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))
        conn.commit()
    conn.close()

init_db()

@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        try:
            conn = get_db_connection()
            g.user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            conn.close()
        except Exception:
            g.user = None

@app.route("/")
def index():
    return render_template("index.html", user=g.user)

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()
    
    if user:
        session["user_id"] = user["id"]
        return redirect(url_for("index"))
    else:
        flash("Invalid username or password.", "danger")
        return redirect(url_for("index"))

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        flash("Registration successful! Please log in.", "success")
    except Exception as e:
        flash(f"Error creating account: {e}", "danger")
        
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@app.route("/drills")
@app.route("/inspector")
@app.route("/ctf")
@app.route("/war_room")
@app.route("/leaderboard")
@app.route("/profile")
def protected_views():
    return render_template("index.html", user=g.user)

if __name__ == "__main__":
    app.run(debug=True, port=5000)