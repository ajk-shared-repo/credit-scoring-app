from flask import Flask, render_template, request, send_file, url_for, redirect
import os, csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

app = Flask(__name__)

def calculate_metrics(data):
    utilization = 0
    payment_history = 0
    dti = 0
    if data.get('credit_limit') and data.get('credit_balance'):
        try:
            utilization = round((float(data['credit_balance']) / float(data['credit_limit'])) * 100, 2)
        except ZeroDivisionError:
            utilization = 0
    if data.get('on_time_payments') and data.get('total_payments'):
        try:
            payment_history = round((int(data['on_time_payments']) / int(data['total_payments'])) * 100, 2)
        except ZeroDivisionError:
            payment_history = 0
    if data.get('monthly_debt') and data.get('gross_income'):
        try:
            dti = round((float(data['monthly_debt']) / float(data['gross_income'])) * 100, 2)
        except ZeroDivisionError:
            dti = 0
    return utilization, payment_history, dti

def generate_pdf(data, score, category, utilization, payment_history, dti):
    filename = "/mnt/data/report.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    logo_path = os.path.join("static", "logo.png")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, width/2 - 50, height - 100, width=100, preserveAspectRatio=True, mask='auto')
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 120, "Credit Scoring Report")
    y = height - 150
    c.setFont("Helvetica", 12)
    fields = [
        ("Full Name", data.get('full_name')),
        ("Date of Birth", data.get('dob')),
        ("National ID", data.get('national_id')),
        ("Current Address", data.get('address')),
        ("Phone Number", data.get('phone')),
        ("Employment", data.get('employment')),
        ("Employer", data.get('employer')),
        ("Income Level", data.get('income')),
        ("Credit Score", f"{score} ({category})"),
        ("Credit Utilization Ratio", f"{utilization}%"),
        ("Payment History Score", f"{payment_history}%"),
        ("Debt-to-Income Ratio", f"{dti}%"),
        ("Open Credit Lines", data.get('open_lines')),
        ("Past Due Accounts", data.get('past_due')),
        ("Length of Credit History", data.get('credit_history_length')),
        ("Recent Credit Inquiries", data.get('recent_inquiries')),
        ("Collateral Provided", data.get('collateral')),
        ("Account Types", data.get('account_types')),
        ("Macroeconomic Risk Adjustment", data.get('macro_risk')),
    ]
    for field, value in fields:
        c.drawString(50, y, f"{field}: {value}")
        y -= 20
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 30, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.save()
    return filename

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form_data = request.form.to_dict()
        utilization, payment_history, dti = calculate_metrics(form_data)
        score = 512
        category = "Poor"
        if request.form.get("action") == "save_csv":
            with open("data/records.csv", "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([form_data.get('full_name'), score, category, utilization, payment_history, dti])
        return render_template("result.html", score=score, category=category, utilization=utilization, payment_history=payment_history, dti=dti)
    return render_template("form.html")

@app.route("/download_pdf")
def download_pdf():
    # Placeholder: would retrieve data from a saved context/session in real app
    dummy_data = {"full_name": "John Doe", "dob": "1990-01-01"}
    utilization, payment_history, dti = 50, 80, 40
    filename = generate_pdf(dummy_data, 512, "Poor", utilization, payment_history, dti)
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
