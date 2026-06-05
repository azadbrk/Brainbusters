# BrainBusters – Quizspiel 🧠

Ein vollständiges Quiz-Spiel mit Python (Flask) Backend und Web-Frontend.

---

## 🚀 Schnellstart (3 Schritte)

### Schritt 1: Python & Abhängigkeiten installieren

```bash
pip install flask flask-cors
```

> ⚠️ Falls `pip` nicht gefunden wird: `pip3 install flask flask-cors`

### Schritt 2: Server starten

```bash
python app.py
```

> ⚠️ Falls `python` nicht gefunden wird: `python3 app.py`

### Schritt 3: Browser öffnen

- **Spiel:** http://localhost:5000
- **Admin-Backend:** http://localhost:5000/admin

---

## 📁 Projektstruktur

```
brainbusters/
│
├── app.py                  # Haupt-Backend (Flask Server)
├── requirements.txt        # Python-Pakete
├── test_brainbusters.py    # Automatisierte Tests
├── brainbusters.db         # Datenbank (wird automatisch erstellt)
│
└── templates/
    ├── index.html          # Startseite mit Rangliste
    ├── game.html           # Spielseite
    └── admin.html          # Admin-Backend
```

---

## 🎮 Funktionen

| Funktion | Status |
|---|---|
| Benutzerregistrierung & Login | ✅ |
| 6 Fragekategorien | ✅ |
| Singleplayer gegen die Zeit | ✅ |
| Multiplayer (Spiel erstellen/beitreten) | ✅ |
| Zeitbonus (schnelle Antworten = mehr Punkte) | ✅ |
| Schwierigkeitsgrade (⭐⭐⭐) | ✅ |
| Globale Rangliste | ✅ |
| Admin-Backend (Fragen verwalten) | ✅ |
| 60+ Quizfragen in der Datenbank | ✅ |
| Automatisierte Tests | ✅ |

---

## 🧪 Tests ausführen

```bash
python test_brainbusters.py
```

---

## 📊 Punktesystem

| Faktor | Punkte |
|---|---|
| Falsche Antwort | 0 |
| Richtig (leicht ⭐) | 100 + Zeitbonus |
| Richtig (mittel ⭐⭐) | 200 + Zeitbonus |
| Richtig (schwer ⭐⭐⭐) | 300 + Zeitbonus |
| Zeitbonus (max) | +50 Punkte |
| Zeitlimit pro Frage | 20 Sekunden |

---

## ➕ Neue Fragen hinzufügen

1. http://localhost:5000/admin aufrufen
2. Tab **"Frage hinzufügen"** wählen
3. Kategorie, Frage, 4 Antworten und richtige Antwort eingeben
4. Speichern!

---

## 🛠️ Technologien

- **Backend:** Python 3, Flask, SQLite
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Fonts:** Bebas Neue, Outfit (Google Fonts)
- **Tests:** Python unittest

---

## 💡 Hinweis für Schüler

Dieser Code erfüllt folgende Anforderungen der Aufgabenstellung:

- ✅ **Must Have**: Eigene Funktionen, lesbarer Code, Tests, Klassendiagramm-äquivalente Struktur
- ✅ **Should Have**: Web-Oberfläche, Datenbank, Benutzeraccounts, Rangliste, 3+ automatisierte Tests
- ✅ **Could Have**: Mehrspielermodus, Admin-Backend zur Fragenverwaltung, 5+ Tests
