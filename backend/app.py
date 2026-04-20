from __future__ import annotations

from flask import Flask, jsonify, request
from flask_cors import CORS

from sql_generator import generate_sql_script


app = Flask(__name__)
CORS(app)


@app.get("/api/health")
def health() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@app.post("/api/generate-sql")
def generate_sql() -> tuple[dict[str, str], int]:
    payload = request.get_json(silent=True) or {}
    try:
        sql_script = generate_sql_script(payload)
    except ValueError:
        return jsonify({"error": "Invalid ERD schema payload"}), 400

    return jsonify({"sql": sql_script}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
