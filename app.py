
import os
from pathlib import Path
from flask import Flask, render_template, request, send_file, Response, jsonify
from jinja2 import TemplateNotFound
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
import io, datetime, sys

ROOT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT_DIR / "templates"

def _fix_templates_dir():
    try:
        if TEMPLATES_DIR.exists() and not TEMPLATES_DIR.is_dir():
            bad_path = TEMPLATES_DIR
            backup = ROOT_DIR / "templates_conflict_backup"
            try:
                bad_path.rename(backup)
                print("[repair] Renamed file 'templates' -> 'templates_conflict_backup'", file=sys.stderr)
            except Exception as e:
                print("[repair] Rename failed, unlinking 'templates': %s" % e, file=sys.stderr)
                bad_path.unlink(missing_ok=True)
            TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
            print("[repair] Created templates directory at %s" % TEMPLATES_DIR, file=sys.stderr)
        elif not TEMPLATES_DIR.exists():
            TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
            print("[repair] Created templates directory at %s" % TEMPLATES_DIR, file=sys.stderr)
    except Exception as e:
        print("[repair] _fix_templates_dir error: %s" % e, file=sys.stderr)

FALLBACK_FORM = """<!doctype html>
<html>
<head><meta charset="utf-8"><title>Credit Scoring Form</title></head>
<body>
<h1>Credit Scoring - Data Entry</h1>
<form method="POST">
<p><label>Full Name <input name="full_name" required></label></p>
<p><label>Date of Birth <input type="date" name="dob" required></label></p>
<p><label>National ID <input name="national_id" required></label></p>
<p><label>Current Address <input name="current_address" required></label></p>
<p><label>Phone Number <input name="phone_number" required></label></p>
<p><label>Employment <input name="employment"></label></p>
<p><label>Employer <input name="employer"></label></p>
<p><label>Income Level <input name="income_level"></label></p>
<p><label>Credit Utilization Ratio (%) <input type="number" step="0.1" name="credit_utilization_ratio" required></label></p>
<p><label>Payment History Score (%) <input type="number" step="0.1" name="payment_history_score" required></label></p>
<p><label>Debt-to-Income Ratio (%) <input type="number" step="0.1" name="debt_to_income_ratio" required></label></p>
<p><label>Open Credit Lines <input type="number" name="open_credit_lines" required></label></p>
<p><label>Past Due Accounts <input type="number" name="past_due_accounts" required></label></p>
<p><label>Length of Credit History (years) <input type="number" name="length_credit_history" required></label></p>
<p><label>Recent Credit Inquiries (12m) <input type="number" name="recent_inquiries" required></label></p>
<p><label>Collateral Provided <input name="collateral_proed"></label></p>
<p><label>Account Types <input name="account_types"></label></p>
<p><label>Macroeconomic Risk Adjustment <input name="macroeconomic_risk"></label></p>
<p>
<button type="submit" name="action" value="preview">Calculate and Preview</button>
<button type="submit" name="action" value="download_pdf">Download PDF</button>
</p>
<p><a href="/debug">Debug</a></p>
</form>
</body></html>"""

FALLBACK_RESULT = """<!doctype html>
<html><head><meta charset="utf-8"><title>Result</title></head>
<body>
<h1>Score: {{ score }} ({{ category }})</h1>
<form method="POST">
  {% for k, v in data.items() %}
    <input type="hidden" name="{{ k }}" value="{{ v }}">
  {% endfor %}
  <button type="submit" name="action" value="download_pdf">Download PDF</button>
</form>
<p><a href="/">Back</a></p>
</body></html>"""

def ensure_templates():
    _fix_templates_dir()
    try:
        form_p = TEMPLATES_DIR / "form.html"
        result_p = TEMPLATES_DIR / "result.html"
        if not form_p.exists():
            form_p.write_text(FALLBACK_FORM, encoding="utf-8")
            print("[failsafe] Wrote fallback form.html", file=sys.stderr)
        if not result_p.exists():
            result_p.write_text(FALLBACK_RESULT, encoding="utf-8")
            print("[failsafe] Wrote fallback result.html", file=sys.stderr)
    except Exception as e:
        print("[failsafe] ensure_templates error: %s" % e, file=sys.stderr)

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

def calculate_credit_score(data):
    score = 300
    score += (data["payment_history_score"]/100.0)*185
    util_good = max(0.0, 100.0 - data["credit_utilization_ratio"])
    score += (util_good/100.0)*165
    years = data["length_credit_history_years"]
    if years >= 10: score += 80
    elif years >= 5: score += 55
    elif years >= 2: score += 35
    else: score += 15
    inquiries = max(0, data["recent_inquiries_12m"])
    score += max(0, 60 - min(60, inquiries*12))
    dti_good = max(0.0, 100.0 - data["debt_to_income_ratio"])
    score += (dti_good/100.0)*55
    past_due = max(0, data["past_due_accounts"])
    score -= min(80, past_due*20)
    lines = max(0, data["open_credit_lines"])
    if lines == 0: score -= 20
    elif 1 <= lines <= 8: score += 20
    elif lines > 12: score -= 10
    collat = (data["collateral_provided"] or "").strip().lower()
    if collat and collat not in {"none","n/a","na"}: score += 15
    employment = (data["employment"] or "").strip().lower()
    income = (data["income_level"] or "").strip().lower()
    if employment in {"self-employed","contract","informal"}: score -= 10
    if any(k in income for k in ["high","upper",">$","above"]): score += 10
    elif any(k in income for k in ["low","minimum","<$"]): score -= 10
    risk = (data["macroeconomic_risk"] or "").strip().lower()
    if "high" in risk: score -= 25
    elif "medium" in risk: score -= 10
    score = int(max(300, min(850, round(score))))
    if score < 580: category = "Poor"
    elif score < 670: category = "Fair"
    elif score < 740: category = "Good"
    else: category = "Excellent"
    return score, category

def _wrap(c, text, x, y, max_width, leading=14):
    lines = simpleSplit(text, "Helvetica", 11, max_width)
    for line in lines:
        c.drawString(x, y, line); y -= leading
    return y

def generate_pdf(form_data, score, category):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    left = 20*mm; right = w-20*mm; y = h-20*mm
    p.setFont("Helvetica-Bold", 16); p.drawString(left, y, "Credit Scoring Report"); y -= 10*mm
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
        ("Credit Utilization Ratio (%)", str(form_data["credit_utilization_ratio"])),
        ("Payment History Score (%)", str(form_data["payment_history_score"])),
        ("Debt-to-Income Ratio (%)", str(form_data["debt_to_income_ratio"])),
        ("Open Credit Lines", str(form_data["open_credit_lines"])),
        ("Past Due Accounts", str(form_data["past_due_accounts"])),
        ("Length of Credit History (years)", str(form_data["length_credit_history_years"])),
        ("Recent Credit Inquiries (12m)", str(form_data["recent_inquiries_12m"])),
        ("Collateral Provided", form_data["collateral_provided"]),
        ("Account Types", form_data["account_types"]),
        ("Macroeconomic Risk Adjustment", form_data["macroeconomic_risk"]),
        ("Score Range", "300-850"),
        ("Credit Score", str(score)),
        ("Score Category", category),
    ]
    for label, value in fields:
        y -= 8
        if y < 40:
            p.showPage(); y = h - 40; p.setFont("Helvetica", 11)
        p.drawString(left, y, f"{label}: {value}")
    p.showPage(); p.save(); buf.seek(0)
    return buf

@app.route("/health", methods=["GET","HEAD"])
def health():
    if request.method == "HEAD":
        return Response(status=200)
    return {"status": "ok"}, 200

@app.route("/debug")
def debug():
    tree = []
    for root, dirs, files in os.walk(".", topdown=True):
        depth = root.count(os.sep)
        if depth > 2: continue
        tree.append({"root": root, "dirs": dirs, "files": files})
    return jsonify({
        "cwd": os.getcwd(),
        "root_dir": str(ROOT_DIR),
        "templates_dir": str(TEMPLATES_DIR),
        "has_templates_dir": TEMPLATES_DIR.is_dir(),
        "templates_list": os.listdir(TEMPLATES_DIR) if TEMPLATES_DIR.is_dir() else [],
        "tree": tree
    })

@app.route("/repair", methods=["POST","GET"])
def repair():
    _fix_templates_dir()
    ensure_templates()
    return jsonify({
        "repaired": True,
        "templates_dir": str(TEMPLATES_DIR),
        "has_templates_dir": TEMPLATES_DIR.is_dir(),
        "templates_list": os.listdir(TEMPLATES_DIR) if TEMPLATES_DIR.is_dir() else []
    })

@app.route("/", methods=["GET","POST","HEAD"])
def index():
    if request.method == "HEAD":
        return Response(status=200)
    ensure_templates()
    if request.method == "GET":
        try:
            return render_template("form.html")
        except TemplateNotFound as e:
            return "Template not found: %s. Expected at: %s" % (e, TEMPLATES_DIR), 500
    fd = {
        "full_name": request.form.get("full_name",""),
        "dob": request.form.get("dob",""),
        "national_id": request.form.get("national_id",""),
        "current_address": request.form.get("current_address",""),
        "phone_number": request.form.get("phone_number",""),
        "employment": request.form.get("employment",""),
        "employer": request.form.get("employer",""),
        "income_level": request.form.get("income_level",""),
        "credit_utilization_ratio": float(request.form.get("credit_utilization_ratio","0")),
        "payment_history_score": float(request.form.get("payment_history_score","0")),
        "debt_to_income_ratio": float(request.form.get("debt_to_income_ratio","0")),
        "open_credit_lines": int(request.form.get("open_credit_lines","0")),
        "past_due_accounts": int(request.form.get("past_due_accounts","0")),
        "length_credit_history_years": int(request.form.get("length_credit_history","0")),
        "recent_inquiries_12m": int(request.form.get("recent_inquiries","0")),
        "collateral_provided": request.form.get("collateral_provided",""),
        "account_types": request.form.get("account_types",""),
        "macroeconomic_risk": request.form.get("macroeconomic_risk",""),
    }
    score, category = calculate_credit_score(fd)
    if request.form.get("action") == "download_pdf":
        pdf = generate_pdf(fd, score, category)
        return send_file(pdf, as_attachment=True, download_name="credit_report.pdf", mimetype="application/pdf")
    return render_template("result.html", data=fd, score=score, category=category)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
