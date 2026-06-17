"""
BrainBusters – Automatisierte Tests
=====================================
Ausführen mit: python test_brainbusters.py
"""

import unittest
import json
import os
import sys

# App importieren (Datenbank wird separat für Tests erstellt)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, init_db, hash_password, calculate_points, get_db, DB_PATH


class TestSetup(unittest.TestCase):
    """Hilfsmethoden für alle Tests"""

    def setUp(self):
        """Testumgebung vorbereiten: temporäre Testdatenbank"""
        # Testdatenbank verwenden
        import app as app_module
        app_module.DB_PATH = "test_brainbusters.db"
        global DB_PATH
        DB_PATH = "test_brainbusters.db"

        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        self.client = app.test_client()

        # Datenbank initialisieren
        init_db()

    def tearDown(self):
        """Testdatenbank nach jedem Test aufräumen"""
        import app as app_module
        try:
            os.remove("test_brainbusters.db")
        except FileNotFoundError:
            pass
        app_module.DB_PATH = "brainbusters.db"

    def register_and_login(self, username="testuser", password="test1234"):
        """Hilfsfunktion: Nutzer registrieren und einloggen"""
        self.client.post("/api/register",
            data=json.dumps({"username": username, "password": password}),
            content_type="application/json")
        return self.client.post("/api/login",
            data=json.dumps({"username": username, "password": password}),
            content_type="application/json")


# ─────────────────────────────────────────
#  Test 1: Hilfsfunktionen
# ─────────────────────────────────────────
class TestHelperFunctions(TestSetup):
    """Testet die internen Hilfsfunktionen"""

    def test_hash_password_returns_string(self):
        """hash_password gibt einen String zurück"""
        result = hash_password("meinpasswort")
        self.assertIsInstance(result, str)

    def test_hash_password_consistent(self):
        """Gleiches Passwort → gleicher Hash"""
        self.assertEqual(hash_password("passwort123"), hash_password("passwort123"))

    def test_hash_password_different_inputs(self):
        """Verschiedene Passwörter → verschiedene Hashes"""
        self.assertNotEqual(hash_password("abc"), hash_password("xyz"))

    def test_calculate_points_correct_answer(self):
        """Richtige Antwort liefert Punkte > 0"""
        points = calculate_points(True, 5.0, 1)
        self.assertGreater(0, points)

    def test_calculate_points_wrong_answer(self):
        """Falsche Antwort → 0 Punkte"""
        points = calculate_points(False, 5.0, 1)
        self.assertEqual(points, 0)

    def test_calculate_points_fast_answer_bonus(self):
        """Schnelle Antwort gibt mehr Punkte als langsame"""
        fast = calculate_points(True, 1.0, 1)
        slow = calculate_points(True, 18.0, 1)
        self.assertGreater(fast, slow)

    def test_calculate_points_difficulty_scaling(self):
        """Schwierigere Fragen geben mehr Punkte"""
        easy = calculate_points(True, 5.0, 1)
        hard = calculate_points(True, 5.0, 3)
        self.assertGreater(hard, easy)

    def test_calculate_points_max_difficulty(self):
        """Schwierigkeit 3 gibt mindestens 300 Basispunkte"""
        points = calculate_points(True, 0.5, 3)
        self.assertGreaterEqual(points, 300)


# ─────────────────────────────────────────
#  Test 2: Benutzer-Authentifizierung
# ─────────────────────────────────────────
class TestAuthentication(TestSetup):
    """Testet Registrierung, Login und Session"""

    def test_register_new_user(self):
        """Neuer Nutzer kann sich registrieren"""
        res = self.client.post("/api/register",
            data=json.dumps({"username": "neuer_spieler", "password": "passwort123"}),
            content_type="application/json")
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("username"), "neuer_spieler")

    def test_register_duplicate_username(self):
        """Doppelter Benutzername wird abgelehnt"""
        self.client.post("/api/register",
            data=json.dumps({"username": "spieler1", "password": "pass1234"}),
            content_type="application/json")
        res = self.client.post("/api/register",
            data=json.dumps({"username": "spieler1", "password": "anderes_pass"}),
            content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_register_short_username(self):
        """Zu kurzer Benutzername wird abgelehnt"""
        res = self.client.post("/api/register",
            data=json.dumps({"username": "ab", "password": "pass1234"}),
            content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_register_short_password(self):
        """Zu kurzes Passwort wird abgelehnt"""
        res = self.client.post("/api/register",
            data=json.dumps({"username": "gutername", "password": "abc"}),
            content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_login_correct_credentials(self):
        """Login mit richtigen Daten erfolgreich"""
        self.client.post("/api/register",
            data=json.dumps({"username": "testlogin", "password": "sicher1234"}),
            content_type="application/json")
        res = self.client.post("/api/login",
            data=json.dumps({"username": "testlogin", "password": "sicher1234"}),
            content_type="application/json")
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))

    def test_login_wrong_password(self):
        """Login mit falschem Passwort schlägt fehl"""
        self.client.post("/api/register",
            data=json.dumps({"username": "testuser2", "password": "richtig"}),
            content_type="application/json")
        res = self.client.post("/api/login",
            data=json.dumps({"username": "testuser2", "password": "falsch"}),
            content_type="application/json")
        self.assertEqual(res.status_code, 401)

    def test_me_logged_out(self):
        """/api/me gibt logged_in=False zurück wenn nicht eingeloggt"""
        res = self.client.get("/api/me")
        data = json.loads(res.data)
        self.assertFalse(data.get("logged_in"))

    def test_me_logged_in(self):
        """/api/me gibt logged_in=True zurück nach Login"""
        self.register_and_login("checkme", "check1234")
        res = self.client.get("/api/me")
        data = json.loads(res.data)
        self.assertTrue(data.get("logged_in"))
        self.assertEqual(data.get("username"), "checkme")

    def test_logout(self):
        """Logout leert die Session"""
        self.register_and_login("logouttest", "pass1234")
        self.client.post("/api/logout")
        res = self.client.get("/api/me")
        data = json.loads(res.data)
        self.assertFalse(data.get("logged_in"))


# ─────────────────────────────────────────
#  Test 3: Kategorien und Fragen
# ─────────────────────────────────────────
class TestCategoriesAndQuestions(TestSetup):
    """Testet die Fragen- und Kategorie-API"""

    def test_get_categories_returns_list(self):
        """/api/categories gibt eine Liste zurück"""
        res = self.client.get("/api/categories")
        data = json.loads(res.data)
        self.assertIsInstance(data, list)

    def test_categories_have_required_fields(self):
        """Jede Kategorie hat id, name, icon"""
        res = self.client.get("/api/categories")
        cats = json.loads(res.data)
        self.assertGreater(len(cats), 0)
        for cat in cats:
            self.assertIn("id", cat)
            self.assertIn("name", cat)
            self.assertIn("icon", cat)

    def test_get_questions_for_category(self):
        """Fragen für Kategorie 1 werden zurückgegeben"""
        res = self.client.get("/api/questions/1?count=5")
        data = json.loads(res.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_questions_count_parameter(self):
        """count-Parameter begrenzt die Anzahl der Fragen"""
        res = self.client.get("/api/questions/1?count=3")
        data = json.loads(res.data)
        self.assertLessEqual(len(data), 3)

    def test_questions_no_correct_answer(self):
        """Korrekte Antwort wird nicht ans Frontend geschickt"""
        res = self.client.get("/api/questions/1?count=5")
        questions = json.loads(res.data)
        for q in questions:
            self.assertNotIn("correct_answer", q)

    def test_questions_have_shuffled_answers(self):
        """Fragen haben gemischte Antworten als Liste"""
        res = self.client.get("/api/questions/1?count=1")
        questions = json.loads(res.data)
        if questions:
            self.assertIn("answers", questions[0])
            self.assertEqual(len(questions[0]["answers"]), 4)

    def test_check_answer_correct(self):
        """Richtige Antwort wird korrekt bewertet"""
        # Direkt aus DB die richtige Antwort holen
        import app as app_module
        conn = app_module.get_db()
        q = conn.execute("SELECT * FROM questions LIMIT 1").fetchone()
        conn.close()

        res = self.client.post("/api/check_answer",
            data=json.dumps({"question_id": q["id"], "answer": q["correct_answer"], "response_time": 5.0}),
            content_type="application/json")
        data = json.loads(res.data)
        self.assertTrue(data["correct"])
        self.assertGreater(data["points"], 0)

    def test_check_answer_wrong(self):
        """Falsche Antwort wird korrekt bewertet"""
        import app as app_module
        conn = app_module.get_db()
        q = conn.execute("SELECT * FROM questions LIMIT 1").fetchone()
        conn.close()

        wrong = "B" if q["correct_answer"] != "B" else "A"
        res = self.client.post("/api/check_answer",
            data=json.dumps({"question_id": q["id"], "answer": wrong, "response_time": 5.0}),
            content_type="application/json")
        data = json.loads(res.data)
        self.assertFalse(data["correct"])
        self.assertEqual(data["points"], 0)


# ─────────────────────────────────────────
#  Test 4: Spielverwaltung
# ─────────────────────────────────────────
class TestGameManagement(TestSetup):
    """Testet Spielstart, Beitreten und Punktevergabe"""

    def test_start_game_requires_login(self):
        """Spiel starten ohne Login schlägt fehl"""
        res = self.client.post("/api/game/start",
            data=json.dumps({"category_id": 1, "mode": "single"}),
            content_type="application/json")
        self.assertEqual(res.status_code, 401)

    def test_start_game_logged_in(self):
        """Eingeloggter Nutzer kann Spiel starten"""
        self.register_and_login()
        res = self.client.post("/api/game/start",
            data=json.dumps({"category_id": 1, "mode": "single"}),
            content_type="application/json")
        data = json.loads(res.data)
        self.assertIn("game_id", data)

    def test_submit_score(self):
        """Spielergebnis kann gespeichert werden"""
        self.register_and_login()
        start_res = self.client.post("/api/game/start",
            data=json.dumps({"category_id": 1, "mode": "single"}),
            content_type="application/json")
        game_id = json.loads(start_res.data)["game_id"]

        res = self.client.post("/api/game/submit_score",
            data=json.dumps({"game_id": game_id, "score": 750}),
            content_type="application/json")
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))

    def test_leaderboard_after_game(self):
        """Nach einem Spiel erscheint Spieler in der Rangliste"""
        self.register_and_login("ranglistenspieler", "test1234")
        start_res = self.client.post("/api/game/start",
            data=json.dumps({"category_id": 1, "mode": "single"}),
            content_type="application/json")
        game_id = json.loads(start_res.data)["game_id"]
        self.client.post("/api/game/submit_score",
            data=json.dumps({"game_id": game_id, "score": 500}),
            content_type="application/json")

        res = self.client.get("/api/leaderboard")
        data = json.loads(res.data)
        usernames = [p["username"] for p in data]
        self.assertIn("ranglistenspieler", usernames)


# ─────────────────────────────────────────
#  Test 5: Admin API
# ─────────────────────────────────────────
class TestAdminAPI(TestSetup):
    """Testet das Admin-Backend"""

    def test_admin_get_questions(self):
        """Admin kann alle Fragen abrufen"""
        res = self.client.get("/api/admin/questions")
        data = json.loads(res.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_admin_add_question(self):
        """Admin kann neue Frage hinzufügen"""
        new_q = {
            "category_id": 1,
            "question": "Was ist 2 + 2?",
            "answer_a": "3",
            "answer_b": "4",
            "answer_c": "5",
            "answer_d": "6",
            "correct_answer": "B",
            "difficulty": 1
        }
        res = self.client.post("/api/admin/questions",
            data=json.dumps(new_q),
            content_type="application/json")
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))

    def test_admin_add_question_missing_fields(self):
        """Unvollständige Frage wird abgelehnt"""
        res = self.client.post("/api/admin/questions",
            data=json.dumps({"question": "Unvollständig"}),
            content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_admin_delete_question(self):
        """Frage kann gelöscht werden"""
        import app as app_module
        conn = app_module.get_db()
        q = conn.execute("SELECT id FROM questions LIMIT 1").fetchone()
        conn.close()

        res = self.client.delete(f"/api/admin/questions/{q['id']}")
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))

    def test_admin_add_category(self):
        """Neue Kategorie kann erstellt werden"""
        res = self.client.post("/api/admin/categories",
            data=json.dumps({"name": "Musik", "icon": "🎵", "description": "Alles über Musik"}),
            content_type="application/json")
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))

    def test_admin_stats(self):
        """Admin-Statistiken werden zurückgegeben"""
        res = self.client.get("/api/admin/stats")
        data = json.loads(res.data)
        self.assertIn("total_users", data)
        self.assertIn("total_questions", data)
        self.assertIn("total_games", data)
        self.assertIn("total_categories", data)


# ─────────────────────────────────────────
#  Test 6: Seiten erreichbar
# ─────────────────────────────────────────
class TestPages(TestSetup):
    """Testet ob alle Seiten erreichbar sind"""

    def test_homepage(self):
        """Startseite ist erreichbar"""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

    def test_game_page(self):
        """Spielseite ist erreichbar"""
        res = self.client.get("/game")
        self.assertEqual(res.status_code, 200)

    def test_admin_page(self):
        """Admin-Seite ist erreichbar"""
        res = self.client.get("/admin")
        self.assertEqual(res.status_code, 200)


# ─────────────────────────────────────────
#  Main
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  BrainBusters – Automatisierte Tests")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Alle Test-Klassen hinzufügen
    test_classes = [
        TestHelperFunctions,
        TestAuthentication,
        TestCategoriesAndQuestions,
        TestGameManagement,
        TestAdminAPI,
        TestPages,
    ]
    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print(f"  Tests gesamt:    {result.testsRun}")
    print(f"  ✅ Erfolgreich:  {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  ❌ Fehler:       {len(result.failures) + len(result.errors)}")
    print("=" * 60)
    sys.exit(0 if result.wasSuccessful() else 1)
