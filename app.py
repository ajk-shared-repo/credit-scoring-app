
from flask import Flask, request, render_template, send_file
from generate_pdf import build_pdf_bytes

app = Flask(__name__, template_folder="templates")

@app.route("/health")
def health():
    return "ok", 200

@app.route("/")
def index():
    return '<h1>Credit Scoring App</h1><p><a href="/form">Open the scoring form</a></p>'

@app.route("/form", methods=["GET"])
def form():
    return render_template("form.html")

def compute_score(data):
    s = 0
    age = int(data.get("Age", 0))
    income = float(data.get("Monthly_Income", 0))
    years = int(data.get("Years_in_Business", 0))
    savings = float(data.get("Savings_Account_Balance", 0))

    if 25 <= age <= 55: s += 10
    elif age > 55:      s += 5
    s += {"None":0,"Primary":2,"Secondary":5,"Tertiary":10}.get(data.get("Education_Level"),0)
    s += {"Unemployed":0,"Self-Employed":5,"Employed":10}.get(data.get("Employment_Status"),0)
    if income >= 1000: s += 10
    elif income >= 500: s += 5
    if years >= 5: s += 10
    elif years >= 2: s += 5
    s += {"Paid":10,"Defaulted":-10,"No History":0}.get(data.get("Previous_Loan_Status"),0)
    if savings >= 1000: s += 10
    elif savings >= 500: s += 5
    if data.get("Collateral_Provided") == "Yes": s += 10
    if data.get("House_Ownership_Status") == "Owned": s += 5
    if data.get("Mobile_Money_Usage") == "Frequent": s += 5
    if data.get("Group_Lending_Participation") == "Yes": s += 5
    return s

def grade_from_score(s):
    if s >= 80: return "Excellent"
    if s >= 60: return "Good"
    if s >= 40: return "Fair"
    if s >= 20: return "Poor"
    return "High Risk"

@app.route("/score", methods=["POST"])
def score():
    data = request.form.to_dict()
    s = compute_score(data)
    g = grade_from_score(s)
    pdf = build_pdf_bytes(data, s, g)
    filename = f"{data.get('Full_Name','credit')}_report.pdf"
    # immediate download
    return send_file(pdf, as_attachment=True, download_name=filename, mimetype="application/pdf")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

