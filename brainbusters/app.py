"""
BrainBusters - Quizspiel Backend
=================================
Starten: python app.py
Dann im Browser öffnen: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
import time
import hashlib
import random

app = Flask(__name__)
app.secret_key = "brainbusters-secret-2024"

DB_PATH = "brainbusters.db"

# ─────────────────────────────────────────
#  Datenbank Setup
# ─────────────────────────────────────────

def get_db():
    """Verbindung zur SQLite-Datenbank herstellen."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Datenbank-Tabellen erstellen und mit Beispieldaten befüllen."""
    conn = get_db()
    c = conn.cursor()

    # Tabellen erstellen
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            total_score INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            created_at REAL DEFAULT (strftime('%s','now'))
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            icon TEXT DEFAULT '🧠',
            description TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer_a TEXT NOT NULL,
            answer_b TEXT NOT NULL,
            answer_c TEXT NOT NULL,
            answer_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            difficulty INTEGER DEFAULT 1,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id INTEGER,
            player2_id INTEGER,
            player1_score INTEGER DEFAULT 0,
            player2_score INTEGER DEFAULT 0,
            category_id INTEGER,
            status TEXT DEFAULT 'waiting',
            created_at REAL DEFAULT (strftime('%s','now')),
            FOREIGN KEY (player1_id) REFERENCES users(id),
            FOREIGN KEY (player2_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS game_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            user_id INTEGER,
            question_id INTEGER,
            answer TEXT,
            is_correct INTEGER,
            response_time REAL,
            points INTEGER DEFAULT 0
        );
    """)

    # Kategorien einfügen (nur wenn leer)
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        kategorien = [
            ("Allgemeinwissen", "🌍", "Fragen rund um die Welt"),
            ("Wissenschaft", "🔬", "Physik, Chemie, Biologie"),
            ("Geschichte", "📜", "Historische Ereignisse und Persönlichkeiten"),
            ("Sport", "⚽", "Fragen rund um den Sport"),
            ("Technologie", "💻", "IT, Programmierung und Technik"),
            ("Geografie", "🗺️", "Länder, Städte, Flüsse"),
        ]
        c.executemany(
            "INSERT INTO categories (name, icon, description) VALUES (?,?,?)",
            kategorien
        )

    # Fragen einfügen (nur wenn leer)
    c.execute("SELECT COUNT(*) FROM questions")
    if c.fetchone()[0] == 0:
        fragen = [
            # Allgemeinwissen (id=1)
            (1, "Was ist die Hauptstadt von Deutschland?", "München", "Berlin", "Hamburg", "Frankfurt", "B", 1),
            (1, "Wie viele Kontinente gibt es auf der Erde?", "5", "6", "7", "8", "C", 1),
            (1, "Welches ist das größte Organ des menschlichen Körpers?", "Lunge", "Leber", "Herz", "Haut", "D", 1),
            (1, "Welche Sprache wird in Brasilien gesprochen?", "Spanisch", "Portugiesisch", "Englisch", "Französisch", "B", 1),
            (1, "Wie viele Beine hat eine Spinne?", "6", "8", "10", "12", "B", 1),
            (1, "Was ist das chemische Symbol für Gold?", "Go", "Gd", "Au", "Ag", "C", 2),
            (1, "Wer malte die Mona Lisa?", "Michelangelo", "Raffael", "Leonardo da Vinci", "Donatello", "C", 1),
            (1, "In welchem Jahr fiel die Berliner Mauer?", "1987", "1989", "1991", "1993", "B", 2),
            (1, "Welches Land hat die meisten Einwohner?", "Indien", "USA", "China", "Russland", "C", 1),
            (1, "Was ist die längste Brücke der Welt?", "Golden Gate Bridge", "Akashi-Kaikyō-Brücke", "Danyang-Kunshan-Viadukt", "Brooklyn Bridge", "C", 3),
            # Wissenschaft (id=2)
            (2, "Was ist die Lichtgeschwindigkeit (ca.)?", "150.000 km/s", "300.000 km/s", "450.000 km/s", "600.000 km/s", "B", 1),
            (2, "Aus wie vielen Knochen besteht der menschliche Körper?", "186", "206", "226", "246", "B", 2),
            (2, "Was ist H2O?", "Sauerstoff", "Wasserstoff", "Wasser", "Salzsäure", "C", 1),
            (2, "Welches Element hat das Symbol 'Fe'?", "Fluor", "Eisen", "Phosphor", "Francium", "B", 2),
            (2, "Was ist der pH-Wert von reinem Wasser?", "5", "6", "7", "8", "C", 1),
            (2, "Welches Gas macht 78% der Erdatmosphäre aus?", "Sauerstoff", "Kohlendioxid", "Stickstoff", "Argon", "C", 2),
            (2, "Was ist die Einheit der elektrischen Spannung?", "Ampere", "Watt", "Volt", "Ohm", "C", 1),
            (2, "Welcher Planet ist der größte in unserem Sonnensystem?", "Saturn", "Jupiter", "Uranus", "Neptun", "B", 1),
            (2, "Was ist ein Photon?", "Ein Elektron", "Ein Lichtteilchen", "Ein Atom", "Ein Proton", "B", 2),
            (2, "Wie nennt man die Wissenschaft der Erbinformation?", "Zoologie", "Botanik", "Genetik", "Ökologie", "C", 2),
            # Geschichte (id=3)
            (3, "In welchem Jahr begann der Erste Weltkrieg?", "1912", "1914", "1916", "1918", "B", 1),
            (3, "Wer war der erste Mensch auf dem Mond?", "Buzz Aldrin", "Neil Armstrong", "John Glenn", "Yuri Gagarin", "B", 1),
            (3, "Welche Stadt war die Hauptstadt des Römischen Reiches?", "Athen", "Karthago", "Rom", "Konstantinopel", "C", 1),
            (3, "In welchem Jahr endete der Zweite Weltkrieg?", "1943", "1944", "1945", "1946", "C", 1),
            (3, "Wer war der erste Präsident der USA?", "Abraham Lincoln", "Thomas Jefferson", "George Washington", "Benjamin Franklin", "C", 1),
            (3, "Was war die Titanic?", "Ein Flugzeug", "Ein Passagierschiff", "Ein Kriegsschiff", "Ein U-Boot", "B", 1),
            (3, "In welchem Jahr fand die Französische Revolution statt?", "1769", "1779", "1789", "1799", "C", 2),
            (3, "Wer war Napoleon Bonaparte?", "Englischer König", "Französischer Kaiser", "Spanischer General", "Russischer Zar", "B", 1),
            (3, "Welche Mauer trennte Berlin?", "Die Chinesische Mauer", "Die Berliner Mauer", "Der Antifaschistischer Schutzwall", "Die Grenzmauer", "B", 1),
            (3, "Wann wurde die Bundesrepublik Deutschland gegründet?", "1945", "1947", "1949", "1951", "C", 2),
            # Sport (id=4)
            (4, "Wie viele Spieler hat eine Fußballmannschaft?", "9", "10", "11", "12", "C", 1),
            (4, "In welchem Land wurde die FIFA WM 2014 ausgetragen?", "Argentinien", "Brasilien", "Deutschland", "Spanien", "B", 1),
            (4, "Wie hoch ist ein Basketballkorb (in cm)?", "280", "295", "305", "315", "C", 2),
            (4, "Wie viele Runden hat ein Boxkampf maximal (Profiboxen)?", "10", "12", "15", "20", "B", 2),
            (4, "Welche Farbe hat die Mitte der Olympischen Ringe?", "Rot", "Blau", "Schwarz", "Grün", "C", 2),
            (4, "Wo fanden die ersten modernen Olympischen Spiele statt?", "Paris", "London", "Athen", "Rom", "C", 1),
            (4, "Was ist Federer für ein Sport?", "Golf", "Tennis", "Badminton", "Squash", "B", 1),
            (4, "Wie viele Punkte gibt ein Touchdown im American Football?", "3", "6", "7", "8", "B", 2),
            (4, "Welches Land gewann die Fußball-WM 2022?", "Frankreich", "Brasilien", "Argentinien", "Deutschland", "C", 1),
            (4, "Wie viele Spieler stehen beim Volleyball auf dem Feld?", "5", "6", "7", "8", "B", 1),
            # Technologie (id=5)
            (5, "Was bedeutet 'HTTP'?", "HyperText Transfer Protocol", "High Transfer Technology Protocol", "Home Text Transfer Protocol", "HyperText Technical Program", "A", 1),
            (5, "Wer gründete Microsoft?", "Steve Jobs", "Bill Gates", "Mark Zuckerberg", "Jeff Bezos", "B", 1),
            (5, "Was ist ein 'Bug' in der Programmierung?", "Ein Virus", "Ein Fehler im Code", "Eine Schnittstelle", "Ein Datentyp", "B", 1),
            (5, "In welchem Jahr wurde das Internet (WWW) erfunden?", "1985", "1989", "1991", "1995", "C", 2),
            (5, "Was ist 'Python'?", "Ein Betriebssystem", "Eine Datenbank", "Eine Programmiersprache", "Ein Browser", "C", 1),
            (5, "Wie viel Byte hat ein Kilobyte?", "100", "512", "1024", "2048", "C", 1),
            (5, "Was ist 'RAM'?", "Read-Only Memory", "Random Access Memory", "Remote Access Module", "Rapid Application Model", "B", 1),
            (5, "Wofür steht 'CPU'?", "Central Processing Unit", "Computer Power Unit", "Core Processing Unit", "Central Power Unit", "A", 1),
            (5, "Was ist ein 'Algorithmus'?", "Ein Computertyp", "Eine Schritt-für-Schritt-Anleitung", "Ein Netzwerkprotokoll", "Ein Dateiformat", "B", 1),
            (5, "Was bedeutet 'open source'?", "Kostenpflichtige Software", "Software mit offenem Quellcode", "Proprietäre Software", "Cloud-Software", "B", 1),
            # Geografie (id=6)
            (6, "Was ist der längste Fluss der Welt?", "Amazonas", "Nil", "Jangtse", "Mississippi", "B", 1),
            (6, "Welches ist das flächenmäßig größte Land der Welt?", "Kanada", "USA", "China", "Russland", "D", 1),
            (6, "Was ist die Hauptstadt von Australien?", "Sydney", "Melbourne", "Canberra", "Brisbane", "C", 2),
            (6, "Welcher Kontinent ist der kleinste?", "Europa", "Australien", "Antarktis", "Südamerika", "B", 1),
            (6, "Wo liegt der Mount Everest?", "In den Alpen", "Im Himalaya", "In den Anden", "Im Kaukasus", "B", 1),
            (6, "Welches Meer liegt zwischen Europa und Afrika?", "Atlantik", "Rotes Meer", "Mittelmeer", "Schwarzes Meer", "C", 1),
            (6, "Wie heißt die Hauptstadt von Japan?", "Osaka", "Kyoto", "Tokio", "Hiroshima", "C", 1),
            (6, "Welches Land hat die längste Küstenlinie der Welt?", "Australien", "Norwegen", "Kanada", "Russland", "C", 2),
            (6, "In welchem Land liegt der Amazonas-Regenwald hauptsächlich?", "Kolumbien", "Peru", "Brasilien", "Venezuela", "C", 1),
            (6, "Was ist das Tote Meer?", "Ein Ozean", "Ein See", "Ein Fluss", "Ein Meeresarm", "B", 2),
        ]
        c.executemany(
            "INSERT INTO questions (category_id, question, answer_a, answer_b, answer_c, answer_d, correct_answer, difficulty) VALUES (?,?,?,?,?,?,?,?)",
            fragen
        )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────
#  Hilfsfunktionen
# ─────────────────────────────────────────

def hash_password(password):
    """Passwort mit SHA-256 hashen."""
    return hashlib.sha256(password.encode()).hexdigest()


def calculate_points(is_correct, response_time, difficulty):
    """
    Punkte berechnen basierend auf:
    - Korrektheit (richtig/falsch)
    - Antwortzeit (schneller = mehr Punkte)
    - Schwierigkeit (1-3)
    """
    if not is_correct:
        return 0
    base_points = 100 * difficulty
    # Zeitbonus: bis zu 50% extra bei sehr schneller Antwort (unter 3 Sekunden)
    time_bonus = max(0, int(50 * (1 - response_time / 20)))
    return base_points + time_bonus


# ─────────────────────────────────────────
#  Routen - Seiten
# ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/game")
def game():
    return render_template("game.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


# ─────────────────────────────────────────
#  API - Authentifizierung
# ─────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    """Neuen Spieler registrieren."""
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Benutzername und Passwort erforderlich"}), 400
    if len(username) < 3:
        return jsonify({"error": "Benutzername muss mindestens 3 Zeichen haben"}), 400
    if len(password) < 4:
        return jsonify({"error": "Passwort muss mindestens 4 Zeichen haben"}), 400

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return jsonify({"success": True, "username": username, "id": user["id"]})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Benutzername bereits vergeben"}), 400
    finally:
        conn.close()


@app.route("/api/login", methods=["POST"])
def login():
    """Spieler einloggen."""
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password_hash=?",
        (username, hash_password(password))
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "Falscher Benutzername oder Passwort"}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify({"success": True, "username": user["username"], "id": user["id"]})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/me")
def me():
    if "user_id" not in session:
        return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "username": session["username"], "id": session["user_id"]})


# ─────────────────────────────────────────
#  API - Kategorien & Fragen
# ─────────────────────────────────────────

@app.route("/api/categories")
def get_categories():
    conn = get_db()
    cats = conn.execute("SELECT *, (SELECT COUNT(*) FROM questions WHERE category_id=categories.id) as question_count FROM categories").fetchall()
    conn.close()
    return jsonify([dict(c) for c in cats])


@app.route("/api/questions/<int:category_id>")
def get_questions(category_id):
    count = request.args.get("count", 10, type=int)
    conn = get_db()
    questions = conn.execute(
        "SELECT * FROM questions WHERE category_id=? ORDER BY RANDOM() LIMIT ?",
        (category_id, count)
    ).fetchall()
    conn.close()
    # Antworten mischen, korrekte Antwort nicht verraten
    result = []
    for q in questions:
        q_dict = dict(q)
        answers = [
            {"key": "A", "text": q_dict["answer_a"]},
            {"key": "B", "text": q_dict["answer_b"]},
            {"key": "C", "text": q_dict["answer_c"]},
            {"key": "D", "text": q_dict["answer_d"]},
        ]
        random.shuffle(answers)
        q_dict["answers"] = answers
        q_dict.pop("correct_answer")  # Nicht an Frontend schicken!
        result.append(q_dict)
    return jsonify(result)


@app.route("/api/check_answer", methods=["POST"])
def check_answer():
    """Antwort prüfen und Punkte berechnen."""
    data = request.json
    question_id = data.get("question_id")
    answer = data.get("answer")
    response_time = data.get("response_time", 10)

    conn = get_db()
    q = conn.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()
    conn.close()

    if not q:
        return jsonify({"error": "Frage nicht gefunden"}), 404

    is_correct = answer == q["correct_answer"]
    points = calculate_points(is_correct, response_time, q["difficulty"])

    return jsonify({
        "correct": is_correct,
        "correct_answer": q["correct_answer"],
        "points": points,
        "explanation": f"Die richtige Antwort ist {q['correct_answer']}: {q['answer_' + q['correct_answer'].lower()]}"
    })


# ─────────────────────────────────────────
#  API - Spielverwaltung
# ─────────────────────────────────────────

@app.route("/api/game/start", methods=["POST"])
def start_game():
    """Spiel starten (Singleplayer oder Multiplayer)."""
    if "user_id" not in session:
        return jsonify({"error": "Nicht eingeloggt"}), 401

    data = request.json
    category_id = data.get("category_id")
    mode = data.get("mode", "single")

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO games (player1_id, category_id, status) VALUES (?,?,?)",
        (session["user_id"], category_id, "running" if mode == "single" else "waiting")
    )
    game_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"game_id": game_id, "mode": mode})


@app.route("/api/game/join/<int:game_id>", methods=["POST"])
def join_game(game_id):
    """Einem Multiplayer-Spiel beitreten."""
    if "user_id" not in session:
        return jsonify({"error": "Nicht eingeloggt"}), 401

    conn = get_db()
    game = conn.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()

    if not game:
        conn.close()
        return jsonify({"error": "Spiel nicht gefunden"}), 404
    if game["status"] != "waiting":
        conn.close()
        return jsonify({"error": "Spiel bereits voll"}), 400
    if game["player1_id"] == session["user_id"]:
        conn.close()
        return jsonify({"error": "Du kannst nicht gegen dich selbst spielen"}), 400

    conn.execute(
        "UPDATE games SET player2_id=?, status='running' WHERE id=?",
        (session["user_id"], game_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "game_id": game_id})


@app.route("/api/game/open_games")
def open_games():
    """Offene Multiplayer-Spiele anzeigen."""
    conn = get_db()
    games = conn.execute("""
        SELECT g.id, u.username as host, c.name as category, c.icon
        FROM games g
        JOIN users u ON g.player1_id = u.id
        JOIN categories c ON g.category_id = c.id
        WHERE g.status = 'waiting'
        ORDER BY g.created_at DESC LIMIT 10
    """).fetchall()
    conn.close()
    return jsonify([dict(g) for g in games])


@app.route("/api/game/submit_score", methods=["POST"])
def submit_score():
    """Spielergebnis speichern."""
    if "user_id" not in session:
        return jsonify({"error": "Nicht eingeloggt"}), 401

    data = request.json
    score = data.get("score", 0)
    game_id = data.get("game_id")

    conn = get_db()
    game = conn.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()

    if game:
        if game["player1_id"] == session["user_id"]:
            conn.execute("UPDATE games SET player1_score=? WHERE id=?", (score, game_id))
        else:
            conn.execute("UPDATE games SET player2_score=?, status='finished' WHERE id=?", (score, game_id))

    # Gesamtpunktzahl des Spielers aktualisieren
    conn.execute(
        "UPDATE users SET total_score = total_score + ?, games_played = games_played + 1 WHERE id=?",
        (score, session["user_id"])
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ─────────────────────────────────────────
#  API - Rangliste
# ─────────────────────────────────────────

@app.route("/api/leaderboard")
def leaderboard():
    """Top-Spieler zurückgeben."""
    conn = get_db()
    players = conn.execute("""
        SELECT username, total_score, games_played,
               CASE WHEN games_played > 0 THEN ROUND(total_score * 1.0 / games_played, 1) ELSE 0 END as avg_score
        FROM users
        ORDER BY total_score DESC
        LIMIT 20
    """).fetchall()
    conn.close()
    return jsonify([dict(p) for p in players])


# ─────────────────────────────────────────
#  API - Admin Backend
# ─────────────────────────────────────────

@app.route("/api/admin/questions", methods=["GET"])
def admin_get_questions():
    conn = get_db()
    questions = conn.execute("""
        SELECT q.*, c.name as category_name
        FROM questions q JOIN categories c ON q.category_id = c.id
        ORDER BY c.name, q.id
    """).fetchall()
    conn.close()
    return jsonify([dict(q) for q in questions])


@app.route("/api/admin/questions", methods=["POST"])
def admin_add_question():
    """Neue Frage hinzufügen."""
    data = request.json
    required = ["category_id", "question", "answer_a", "answer_b", "answer_c", "answer_d", "correct_answer"]
    if not all(k in data for k in required):
        return jsonify({"error": "Fehlende Felder"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO questions (category_id, question, answer_a, answer_b, answer_c, answer_d, correct_answer, difficulty) VALUES (?,?,?,?,?,?,?,?)",
        (data["category_id"], data["question"], data["answer_a"], data["answer_b"],
         data["answer_c"], data["answer_d"], data["correct_answer"].upper(), data.get("difficulty", 1))
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/admin/questions/<int:question_id>", methods=["DELETE"])
def admin_delete_question(question_id):
    conn = get_db()
    conn.execute("DELETE FROM questions WHERE id=?", (question_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/admin/categories", methods=["POST"])
def admin_add_category():
    data = request.json
    name = data.get("name", "").strip()
    icon = data.get("icon", "🧠")
    desc = data.get("description", "")

    if not name:
        return jsonify({"error": "Name erforderlich"}), 400

    conn = get_db()
    try:
        conn.execute("INSERT INTO categories (name, icon, description) VALUES (?,?,?)", (name, icon, desc))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Kategorie existiert bereits"}), 400
    conn.close()
    return jsonify({"success": True})


@app.route("/api/admin/stats")
def admin_stats():
    conn = get_db()
    stats = {
        "total_users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "total_questions": conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0],
        "total_games": conn.execute("SELECT COUNT(*) FROM games").fetchone()[0],
        "total_categories": conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0],
    }
    conn.close()
    return jsonify(stats)


# ─────────────────────────────────────────
#  Start
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  BrainBusters Quiz - Server startet...")
    print("  Öffne: http://localhost:5000")
    print("  Admin: http://localhost:5000/admin")
    print("=" * 50)
    init_db()
    app.run(debug=True, port=5000)
