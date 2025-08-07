
from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return render_template_string(open("templates/form.html").read())

@app.route("/score", methods=["POST"])
def score():
    data = request.form
    score = 0

    age = int(data.get("Age", 0))
    income = float(data.get("Monthly_Income", 0))
    years = int(data.get("Years_in_Business", 0))
    savings = float(data.get("Savings_Account_Balance", 0))

    if 25 <= age <= 55:
        score += 10
    elif age > 55:
        score += 5

    education = data.get("Education_Level")
    education_scores = {"None": 0, "Primary": 2, "Secondary": 5, "Tertiary": 10}
    score += education_scores.get(education, 0)

    employment = data.get("Employment_Status")
    employment_scores = {"Unemployed": 0, "Self-Employed": 5, "Employed": 10}
    score += employment_scores.get(employment, 0)

    if income >= 1000:
        score += 10
    elif income >= 500:
        score += 5

    if years >= 5:
        score += 10
    elif years >= 2:
        score += 5

    status = data.get("Previous_Loan_Status")
    score += {"Paid": 10, "Defaulted": -10, "No History": 0}.get(status, 0)

    if savings >= 1000:
        score += 10
    elif savings >= 500:
        score += 5

    if data.get("Collateral_Provided") == "Yes":
        score += 10

    if data.get("House_Ownership_Status") == "Owned":
        score += 5

    if data.get("Mobile_Money_Usage") == "Frequent":
        score += 5

    if data.get("Group_Lending_Participation") == "Yes":
        score += 5

    if score >= 80:
        grade = "Excellent"
    elif score >= 60:
        grade = "Good"
    elif score >= 40:
        grade = "Fair"
    elif score >= 20:
        grade = "Poor"
    else:
        grade = "High Risk"

    
from generate_pdf import generate_credit_report
generate_credit_report(data, score, grade, filename=f"{data.get('Full_Name', 'credit')}_report.pdf")

return f"""
    <h2>Score: {score}</h2>
    <h3>Grade: {grade}</h3>
    <a href='/{data.get("Full_Name", "credit")}_report.pdf' download>Download Credit Report (PDF)</a>
"""
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
