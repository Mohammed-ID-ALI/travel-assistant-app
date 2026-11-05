from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder="../frontend", static_url_path="")
DB_PATH = os.path.join(os.path.dirname(__file__), "travel_assistant.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS trips (
            id TEXT PRIMARY KEY,
            destination TEXT NOT NULL,
            country TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            budget REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            style TEXT DEFAULT 'Cultural & Scenic',
            weather_summary TEXT DEFAULT '22°C · Mild & Sunny',
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS itinerary (
            id TEXT PRIMARY KEY,
            trip_id TEXT NOT NULL,
            day INTEGER NOT NULL,
            time TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            cost REAL DEFAULT 0,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id TEXT PRIMARY KEY,
            trip_id TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS packing (
            id TEXT PRIMARY KEY,
            trip_id TEXT NOT NULL,
            item TEXT NOT NULL,
            category TEXT NOT NULL,
            packed INTEGER DEFAULT 0,
            FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    return response


@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "WanderFlow Travel Assistant API",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.route("/api/trips", methods=["GET", "POST"])
def handle_trips():
    conn = get_db()
    if request.method == "GET":
        trips = [dict(row) for row in conn.execute("SELECT * FROM trips").fetchall()]
        for t in trips:
            tid = t["id"]
            t["itinerary"] = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM itinerary WHERE trip_id = ? ORDER BY day ASC, time ASC", (tid,)
                ).fetchall()
            ]
            t["expenses"] = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM expenses WHERE trip_id = ? ORDER BY date DESC", (tid,)
                ).fetchall()
            ]
            t["packing"] = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM packing WHERE trip_id = ?", (tid,)
                ).fetchall()
            ]
        conn.close()
        return jsonify({"trips": trips})

    data = request.get_json(force=True)
    trip_id = data.get("id") or f"trip_{int(datetime.utcnow().timestamp() * 1000)}"
    conn.execute(
        """
        INSERT INTO trips (id, destination, country, start_date, end_date, budget, currency, style, weather_summary, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            trip_id,
            data["destination"],
            data.get("country", "International"),
            data["start_date"],
            data["end_date"],
            float(data.get("budget", 1500)),
            data.get("currency", "USD"),
            data.get("style", "Cultural & Scenic"),
            data.get("weather_summary", "22°C · Pleasant"),
            data.get("notes", ""),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "created", "id": trip_id}), 201


@app.route("/api/trips/<trip_id>", methods=["DELETE"])
def delete_trip(trip_id):
    conn = get_db()
    conn.execute("DELETE FROM itinerary WHERE trip_id = ?", (trip_id,))
    conn.execute("DELETE FROM expenses WHERE trip_id = ?", (trip_id,))
    conn.execute("DELETE FROM packing WHERE trip_id = ?", (trip_id,))
    conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted", "id": trip_id})


@app.route("/api/trips/<trip_id>/itinerary", methods=["POST"])
def add_itinerary_item(trip_id):
    data = request.get_json(force=True)
    item_id = data.get("id") or f"itin_{int(datetime.utcnow().timestamp() * 1000)}"
    conn = get_db()
    conn.execute(
        """
        INSERT INTO itinerary (id, trip_id, day, time, title, category, location, cost, completed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item_id,
            trip_id,
            int(data.get("day", 1)),
            data.get("time", "09:00"),
            data["title"],
            data.get("category", "Sightseeing"),
            data.get("location", "City Center"),
            float(data.get("cost", 0)),
            int(bool(data.get("completed", False))),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "created", "id": item_id}), 201


@app.route("/api/itinerary/<item_id>", methods=["PATCH", "DELETE"])
def modify_itinerary_item(item_id):
    conn = get_db()
    if request.method == "DELETE":
        conn.execute("DELETE FROM itinerary WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted", "id": item_id})

    data = request.get_json(force=True)
    conn.execute(
        "UPDATE itinerary SET completed = ? WHERE id = ?",
        (int(bool(data.get("completed", False))), item_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "updated", "id": item_id})


@app.route("/api/trips/<trip_id>/expenses", methods=["POST"])
def add_expense(trip_id):
    data = request.get_json(force=True)
    exp_id = data.get("id") or f"exp_{int(datetime.utcnow().timestamp() * 1000)}"
    conn = get_db()
    conn.execute(
        """
        INSERT INTO expenses (id, trip_id, title, category, amount, date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            exp_id,
            trip_id,
            data["title"],
            data.get("category", "Dining"),
            float(data["amount"]),
            data.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "created", "id": exp_id}), 201


@app.route("/api/expenses/<exp_id>", methods=["DELETE"])
def delete_expense(exp_id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id = ?", (exp_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted", "id": exp_id})


@app.route("/api/trips/<trip_id>/packing", methods=["POST"])
def add_packing_item(trip_id):
    data = request.get_json(force=True)
    pack_id = data.get("id") or f"pack_{int(datetime.utcnow().timestamp() * 1000)}"
    conn = get_db()
    conn.execute(
        """
        INSERT INTO packing (id, trip_id, item, category, packed)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            pack_id,
            trip_id,
            data["item"],
            data.get("category", "Essentials"),
            int(bool(data.get("packed", False))),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "created", "id": pack_id}), 201


@app.route("/api/packing/<pack_id>", methods=["PATCH", "DELETE"])
def modify_packing_item(pack_id):
    conn = get_db()
    if request.method == "DELETE":
        conn.execute("DELETE FROM packing WHERE id = ?", (pack_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted", "id": pack_id})

    data = request.get_json(force=True)
    conn.execute(
        "UPDATE packing SET packed = ? WHERE id = ?",
        (int(bool(data.get("packed", False))), pack_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "updated", "id": pack_id})


@app.route("/api/assistant/ask", methods=["POST"])
def ask_assistant():
    data = request.get_json(force=True)
    prompt = (data.get("prompt") or "").lower()
    destination = data.get("destination", "your destination")
    budget = float(data.get("budget", 1500))
    spent = float(data.get("spent", 0))
    remaining = max(0.0, budget - spent)

    if "food" in prompt or "eat" in prompt or "dining" in prompt:
        reply = (
            f"For {destination}, prioritize morning markets and family-run bistros away from main transit hubs. "
            f"With ${remaining:.0f} remaining in your budget, allocating $35–$50/day lets you enjoy one signature regional dinner plus authentic street-food lunches."
        )
    elif "budget" in prompt or "cost" in prompt or "save" in prompt:
        reply = (
            f"You have spent ${spent:.0f} of your ${budget:.0f} budget (${remaining:.0f} left). "
            f"Tip: Bundle museum/attraction passes and use regional rail or metro day-passes in {destination} to cut transit costs by ~30%."
        )
    elif "pack" in prompt or "weather" in prompt:
        reply = (
            f"For {destination}, pack breathable layers, a lightweight rain shell, a universal power adapter, "
            f"and broken-in walking shoes (expect 12,000+ steps/day)."
        )
    else:
        reply = (
            f"Here is a balanced strategy for {destination}: group morning sightseeing by neighborhood to minimize transit time, "
            f"schedule a 2-hour midday rest or café break, and book popular sunset viewpoints at least 48 hours ahead."
        )

    return jsonify({
        "reply": reply,
        "suggested_activity": {
            "day": 1,
            "time": "16:30",
            "title": f"Guided Old Town & Scenic Viewpoint Walk ({destination})",
            "category": "Sightseeing",
            "location": f"{destination} Historic Quarter",
            "cost": 25
        }
    })


if __name__ == "__main__":
    init_db()
    print("WanderFlow Travel Assistant Backend running on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
