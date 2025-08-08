from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
import datetime

app = Flask(__name__)

def calculate_credit_score(data):
    score = 300
    score += (data["payment_history_score"] / 100) * 185
    utilization_factor = max(0, 100 - data["credit_utilization_ratio"])
    score += (utilization_factor / 100) * 165
    if data["length_credit_history"] >= 10:
        score += 80
    elif data["length_credit_history"] >= 5:
        score += 50
    else:
        score += 25
    inquiries_penalty = min(data["recent_inquiries"] * 10, 60)
    score += 60 - inquiries_penalty
    dti_factor = max(0, 100 - data["debt_to_income_ratio"])
    score += (dti_factor / 100) * 55
    if data["collateral_provided"].lower() not in ["none", ""]:
        score += 20
    score = max(300, min(850, int(score)))
    if score < 580:
        category = "Poor"
    elif score < 670:
        category = "Fair"
    elif score < 740:
        category = "Good"
    else:
        category = "Excellent"
    return score, category

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form_data = {
            "full_name": request.form["full_name"],
            "dob": request.form["dob"],
            "national_id": request.form["national_id"],
            "current_address": request.form["current_address"],
            "phone_number": request.form["phone_number"],
            "employment": request.form["employment"],
            "employer": request.form["employer"],
            "income_level": request.form["income_level"],
            "credit_utilization_ratio": float(request.form["credit_utilization_ratio"]),
            "payment_history_score": float(request.form["payment_history_score"]),
            "debt_to_income_ratio": float(request.form["debt_to_income_ratio"]),
            "open_credit_lines": int(request.form["open_credit_lines"]),
            "past_due_accounts": int(request.form["past_due_accounts"]),
            "length_credit_history": int(request.form["length_credit_history"]),
            "recent_inquiries": int(request.form["recent_inquiries"]),
            "collateral_provided": request.form["collateral_provided"],
            "account_types": request.form["account_types"],
            "macroeconomic_risk": request.form["macroeconomic_risk"]
        }
        score, category = calculate_credit_score(form_data)
        form_data["score"] = score
        form_data["category"] = category
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, 800, "Credit Scoring Report")
        p.setFont("Helvetica", 12)
        y = 770
        for key, value in form_data.items():
            p.drawString(50, y, f"{key.replace('_', ' ').title()}: {value}")
            y -= 20
        p.drawString(50, y - 20, f"Generated On: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        p.showPage()
        p.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="credit_report.pdf", mimetype="application/pdf")
    return render_template("form.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
