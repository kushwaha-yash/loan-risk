from flask import Flask, render_template, request, jsonify, redirect, session
import sqlite3
import pickle
import json
import numpy as np

app = Flask(__name__)
app.secret_key = "secret123"

# ===============================
# Load Questions
# ===============================
with open("questions.json", "r") as f:
    QUESTIONS = json.load(f)

# ===============================
# Load ML Model
# ===============================
with open("loan_risk_model.pkl", "rb") as f:
    model_data = pickle.load(f)

model = model_data["model"]
scaler = model_data["scaler"]
FEATURES = model_data["features"]

print("MODEL FEATURES:", FEATURES)

# ===============================
# DB Helper
# ===============================
def get_db():
    return sqlite3.connect("database.db")

# ===============================
# API → QUESTIONS
# ===============================
@app.route("/api/questions")
def get_questions():
    return jsonify(QUESTIONS)

# ===============================
# Feature Mapping (STRICT & CLEAN)
# ===============================
def prepare_input(user_answers):
    final = {}

    for feature in FEATURES:
        if feature not in user_answers:
            raise ValueError(f"Missing input for feature: {feature}")

        final[feature] = float(user_answers[feature])

    print("FINAL MODEL INPUT:", final)

    X = np.array([final[f] for f in FEATURES], dtype=float)
    return X

# ===============================
# Routes
# ===============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        action = request.form.get("action")
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()

        if action == "signup":
            name = request.form.get("name")
            cur.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()
            conn.close()
            return redirect("/auth")

        if action == "login":
            cur.execute(
                "SELECT * FROM users WHERE email=? AND password=?",
                (email, password)
            )
            user = cur.fetchone()
            conn.close()

            if user:
                session["user"] = user[1]
                return redirect("/dashboard")
            else:
                return "Invalid credentials"

    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/auth")
    return render_template("dashboard.html")

@app.route("/assessment")
def assessment():
    if "user" not in session:
        return redirect("/auth")
    return render_template("assessment.html")

# ===============================
# SUBMIT ASSESSMENT (FINAL LOGIC)
# ===============================
@app.route("/submit_assessment", methods=["POST"])
def submit_assessment():
    try:
        user_data = request.json
        print("ASSESSMENT DATA:", user_data)

        # Prepare input (STRICT)
        X = prepare_input(user_data).reshape(1, -1)

        # Apply scaling (same as training)
        X_scaled = scaler.transform(X)

        # Model predicts PAID probability (loan_paid_back = 1)
        paid_prob = model.predict_proba(X_scaled)[0][1]

        # Convert to DEFAULT probability
        default_prob = 1 - paid_prob

        print("PAID PROBABILITY:", paid_prob)
        print("DEFAULT PROBABILITY:", default_prob)

        # ===============================
        # Risk Decision Logic
        # ===============================
        if default_prob >= 0.30:
            risk = "HIGH"
            recommendation = "Do Not Approve"
        elif default_prob >= 0.15:
            risk = "MEDIUM"
            recommendation = "Manual Review"
        else:
            risk = "LOW"
            recommendation = "Approve"

        session["risk"] = risk
        session["recommendation"] = recommendation
        session["probability"] = round(default_prob * 100, 2)

        return jsonify({"redirect": "/result"})

    except Exception as e:
        print("❌ BACKEND ERROR:", e)
        return jsonify({"error": str(e)}), 500

# ===============================
# RESULT
# ===============================
@app.route("/result")
def result():
    return render_template(
        "result.html",
        risk=session.get("risk", "N/A"),
        probability=session.get("probability", 0),
        recommendation=session.get("recommendation", "N/A")
    )

# ===============================
# Logout
# ===============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ===============================
# Run
# ===============================
if __name__ == "__main__":
    app.run(debug=True)
