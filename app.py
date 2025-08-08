from flask import Flask, render_template, request, send_file, Response
from jinja2 import TemplateNotFound
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
import io, datetime

# Explicit template folder to avoid path issues on Render
app = Flask(__name__, template_folder="templates")

# --------------------------
# Credit Scoring Logic
# --------------------------
def calculate_credit_score(data):
    score = 300  # base
    # Payment history (35%)
    score += (data["payment_history_score"] / 100.0) * 185
    # Utilization (30%) - lower is better
    util_good = max(0.0, 100.0 - data["credit_utilization_ratio"])
    score += (util_good / 100.0) * 165
    # Length of history (15%)
    years = data["length_credit_history_years"]
    if years >= 10: score += 80
    elif years >= 5: score += 55
    elif years >= 2: score += 35
    else: score += 15
    # Inquiries (10%) - fewer better
    inquiries = max(0, data["recent_inquiries_12m"])
    score += max(0, 60 - min(60, inquiries * 12))  # up to -60
    # DTI (10%) - lower better
    dti_good = max(0.0, 100.0 - data["debt_to_income_ratio"])
    score += (dti_good / 100.0) * 55
    # Past due penalty
    past_due = max(0, data["past_due_accounts"])
    score -= min(80, past_due * 20)
    # Open lines sweet spot
    lines = max(0, data["open_credit_lines"])
    if lines == 0: score -= 20
    elif 1 <= lines <= 8: score += 20
    elif lines > 12: score -= 10
    # Collateral bonus
    collat = (data["collateral_provided"] or "").strip().lower()
    if collat and collat not in {"none", "n/a", "na"}:
        score += 15
    # Employment/income tiny adjustments
    employment = (data["employment"] or "").strip().lower()
    income = (data["income_level"] or "").strip().lower()
    if employment in {"self-employed", "contract", "informal"}:
        score -= 10
    if any(k in income for k in ["high", "upper", ">$", "above"]):
        score += 10
    elif any(k in income for k in ["low", "minimum", "<$"]):
        score -= 10
    # Macro risk
    risk = (data["macroeconomic_risk"] or "").strip().lower()
    if "high" in risk: score -= 25
    elif "medium" in risk: score -= 10
    # Clamp & category
    score = int(max(300, min(850, round(score))))
    if score < 580: category = "Poor"
    elif score < 670: category = "Fair"
    elif score < 740: category = "Good"
    else: category = "Excellent"
    return score, category


def _draw_wrapped(c, text, x, y, max_width, leading=14):
    lines = simpleSplit(text, "Helvetica", 11, max_width)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def generate_pdf(form_data, score, category):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    left = 20 * mm
    right = w - 20 * mm
    y = h - 20 * mm

    p.setFont("Helvetica-Bold", 16)
    p.drawString(left, y, "Credit Scoring Report")
    y -= 10 * mm
    p.setFont("Helvetica", 11)

    fields = [
        ("Full Name", form_data["full_name"]),
        ("Date of Birth", form_data["dob"]),
        ("National ID", form_data["national_id"]),
        ("Current Address", form_data["current_address"]),
        ("Phone Number", form_data["phone_number"]),
        ("Employment", form_data["employment"]),
        ("Employer", form_data["employer"]),
        ("Income Level", form_data["income_level"]),
        ("Account Types", form_data["account_types"]),
        ("Collateral Provided", form_data["collateral_provided"]),
        ("Macroeconomic Risk Adjustment", form_data["macroeconomic_risk"]),
        ("Credit Utilization Ratio", f'{form_data["credit_utilization_ratio"]}%'),
        ("Payment History Score", f'{form_data["payment_history_score"]}%'),
        ("Debt-to-Income Ratio", f'{form_data["debt_to_income_ratio"]}%'),
        ("Open Credit Lines", str(form_data["open_credit_lines"])),
        ("Past Due Accounts", str(form_data["past_due_accounts"])),
        ("Length of Credit History", f'{form_data["length_credit_history_years"]} years'),
        ("Recent Credit Inquiries (12m)", str(form_data["recent_inquiries_12m"])),
        ("Score Range", "300 – 850"),
        ("Credit Score (FICO-like)", str(score)),
        ("Score Category", category),
    ]

    for label, value in fields:
        if y < 30 * mm:
            p.showPage()
            y = h - 20 * mm
            p.setFont("Helvetica", 11)
        y = _draw_wrapped(p, f"{label}: {value}", left, y, right - left)

    y -= 6 * mm
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(left, y, f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    p.showPage()
    p.save()
    buf.seek(0)
    return buf


# --------------------------
# Routes
# --------------------------
@app.route("/health", methods=["GET", "HEAD"])
def health():
    if request.method == "HEAD":
        return Response(status=200)
    return {"status": "ok"}, 200


@app.route("/", methods=["GET", "POST", "HEAD"])
def index():
    if request.method == "HEAD":
        return Response(status=200)

    if request.method == "GET":
        try:
            return render_template("form.html")
        except TemplateNotFound as e:
            # Helpful message if template path is wrong in deployment
            return f"Template not found: {e}. Ensure /templates/form.html exists at repo root or set template_folder correctly.", 500

    # POST
    try:
        fd = {
            "full_name": request.form.get("full_name", "").strip(),
            "dob": request.form.get("dob", "").strip(),
            "national_id": request.form.get("national_id", "").strip(),
            "current_address": request.form.get("current_address", "").strip(),
            "phone_number": request.form.get("phone_number", "").strip(),
            "employment": request.form.get("employment", "").strip(),
            "employer": request.form.get("employer", "").strip(),
            "income_level": request.form.get("income_level", "").strip(),
            "credit_utilization_ratio": float(request.form.get("credit_utilization_ratio", "0") or 0),
            "payment_history_score": float(request.form.get("payment_history_score", "0") or 0),
            "debt_to_income_ratio": float(request.form.get("debt_to_income_ratio", "0") or 0),
            "open_credit_lines": int(request.form.get("open_credit_lines", "0") or 0),
            "past_due_accounts": int(request.form.get("past_due_accounts", "0") or 0),
            "length_credit_history_years": int(request.form.get("length_credit_history", "0") or 0),
            "recent_inquiries_12m": int(request.form.get("recent_inquiries", "0") or 0),
            "collateral_provided": request.form.get("collateral_provided", "").strip(),
            "account_types": request.form.get("account_types", "").strip(),
            "macroeconomic_risk": request.form.get("macroeconomic_risk", "").strip(),
        }
    except ValueError:
        return render_template("form.html", error="Please ensure numeric fields contain valid numbers.")

    score, category = calculate_credit_score(fd)

    if request.form.get("action") == "download_pdf":
        pdf = generate_pdf(fd, score, category)
        return send_file(pdf, as_attachment=True, download_name="credit_report.pdf", mimetype="application/pdf")

    return render_template("result.html", data=fd, score=score, category=category)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
