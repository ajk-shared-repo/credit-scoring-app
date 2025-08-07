from flask import Flask, request, render_template
from generate_pdf import generate_credit_report

app = Flask(__name__, template_folder="templates")

@app.route("/health")
def health():
    return "ok", 200

@app.route("/")
def index():
    return """
        <h1>Credit Scoring App</h1>
        <p><a href="/form">Open the scoring form</a></p>
    """

@app.route("/form", methods=["GET"])
def form():
    # Looks up templates/form.html via Flask's Jinja loader
    return render_template("form.html")

@app.route("/score", methods=["POST"])
def score():
    data = request.form
    score = 0

    # --- scoring ---
    age = int(data.get("Age", 0))
    income = float(data.get("Monthly_Income", 0))
    years = int(data.get("Years_in_Business", 0))
    savings = float(data.get("Savings_Account_Balance", 0))

    if 25 <= age <= 55: score += 10
    elif age > 55:      score += 5

    score += {"None":0, "Primary":2, "Secondary":5, "Tertiary":10}.get(data.get("Education_Level"), 0)
    score += {"Unemployed":0, "Self-Employed":5, "Employed":10}.get(data.get("Employment_Status"), 0)

    if income >= 1000: score += 10
    elif income >= 500: score += 5

    if years >= 5: score += 10
    elif years >= 2: score += 5

    score += {"Paid":10, "Defaulted":-10, "No History":0}.get(data.get("Previous_Loan_Status"), 0)

    if savings >= 1000: score += 10
    elif savings >= 500: score += 5

    if data.get("Collateral_Provided") == "Yes": score += 10
    if data.get("House_Ownership_Status") == "Owned": score += 5
    if data.get("Mobile_Money_Usage") == "Frequent": score += 5
    if data.get("Group_Lending_Participation") == "Yes": score += 5

    grade = ("Excellent" if score >= 80 else
             "Good"      if score >= 60 else
             "Fair"      if score >= 40 else
             "Poor"      if score >= 20 else
             "High Risk")

    # --- PDF ---
    filename = f"{data.get('Full_Name', 'credit')}_report.pdf"
    generate_credit_report(data, score, grade, filename)

    # Return page with download link
    return f"""
        <h2>Score: {score}</h2>
        <h3>Grade: {grade}</h3>
        <p><a href='/{filename}' download>Download Credit Report (PDF)</a></p>
        <p><a href='/form'>Score another applicant</a></p>
    """

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
