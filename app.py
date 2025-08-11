
import os, csv, sys, io, datetime
from pathlib import Path
from flask import Flask, render_template, request, send_file, Response, jsonify
from jinja2 import TemplateNotFound
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit, ImageReader
from reportlab.lib import colors

ROOT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT_DIR / "templates"
STATIC_DIR = ROOT_DIR / "static"
DATA_DIR = ROOT_DIR / "data"
CSV_PATH = DATA_DIR / "records.csv"

# ---------- Failsafe templates (pretty HTML + auto-calc) ----------
FALLBACK_FORM = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Credit Scoring Form</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 24px; background: #f6f7fb; }
    .card { max-width: 980px; margin: 0 auto; background: #fff; padding: 24px; border-radius: 10px; box-shadow: 0 6px 20px rgba(0,0,0,.08); }
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px 16px; }
    label { font-weight: bold; display: block; margin-bottom: 4px; }
    input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; }
    .actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px; }
    .btn { padding: 10px 14px; border: none; border-radius: 8px; cursor: pointer; }
    .primary { background: #2f6fed; color: #fff; }
    .secondary { background: #e9edf7; }
    .danger { background: #f8d7da; }
    .logo { text-align:center; margin-bottom:20px; }
    .logo img { max-height: 60px; }
    .hint { color:#555; font-size:12px }
    .subgrid { display:grid; grid-template-columns: repeat(3,1fr); gap: 8px 12px; background:#fafbff; padding:12px; border:1px dashed #cbd2e6; border-radius:8px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">
      <img src="{{ url_for('static', filename='logo.png') }}" alt="Logo" onerror="this.style.display='none'">
    </div>
    <h1>Credit Scoring - Data Entry</h1>
    <form method="POST" id="credit-form">
      <h3>Identity</h3>
      <div class="grid">
        <div><label>Full Name</label><input name="full_name" required></div>
        <div><label>Date of Birth</label><input type="date" name="dob" required></div>
        <div><label>National ID</label><input name="national_id" required></div>
        <div><label>Phone Number</label><input name="phone_number" required></div>
        <div style="grid-column:1 / -1"><label>Current Address</label><input name="current_address" required></div>
      </div>

      <h3>Employment and Income</h3>
      <div class="grid">
        <div>
          <label>Employment</label>
          <select name="employment">
            <option value="">-- select --</option>
            <option>Full-time</option>
            <option>Part-time</option>
            <option>Self-employed</option>
            <option>Contract</option>
            <option>Informal</option>
            <option>Unemployed</option>
          </select>
        </div>
        <div><label>Employer</label><input name="employer"></div>
        <div>
          <label>Income Level</label>
          <select name="income_level">
            <option value="">-- select --</option>
            <option>Low</option>
            <option>Medium</option>
            <option>High</option>
          </select>
        </div>
      </div>

      <h3>Auto-calculated Metrics (for new customers)</h3>
      <p class="hint">Enter raw figures; the three percentages will be calculated automatically.</p>
      <div class="subgrid">
        <div><label>Total Revolving Credit Limit</label><input name="total_credit_limit" type="number" step="0.01" min="0" placeholder="e.g., 1000"></div>
        <div><label>Total Revolving Balances</label><input name="total_credit_balance" type="number" step="0.01" min="0" placeholder="e.g., 720"></div>
        <div><label>Credit Utilization Ratio (%)</label><input name="credit_utilization_ratio" type="number" step="0.1" min="0" max="100" readonly></div>

        <div><label>On-time Payments (count)</label><input name="on_time_payments" type="number" min="0" placeholder="e.g., 58"></div>
        <div><label>Total Payments (count)</label><input name="total_payments" type="number" min="0" placeholder="e.g., 100"></div>
        <div><label>Payment History Score (%)</label><input name="payment_history_score" type="number" step="0.1" min="0" max="100" readonly></div>

        <div><label>Monthly Debt Payments</label><input name="monthly_debt_payments" type="number" step="0.01" min="0" placeholder="e.g., 650"></div>
        <div><label>Gross Monthly Income</label><input name="gross_monthly_income" type="number" step="0.01" min="0" placeholder="e.g., 1000"></div>
        <div><label>Debt-to-Income Ratio (%)</label><input name="debt_to_income_ratio" type="number" step="0.1" min="0" max="100" readonly></div>
      </div>

      <h3>Credit File Details</h3>
      <div class="grid">
        <div><label>Open Credit Lines</label><input name="open_credit_lines" type="number" min="0" required></div>
        <div><label>Past Due Accounts</label><input name="past_due_accounts" type="number" min="0" required></div>
        <div><label>Length of Credit History (years)</label><input name="length_credit_history" type="number" min="0" required></div>
        <div><label>Recent Credit Inquiries (12m)</label><input name="recent_inquiries" type="number" min="0" placeholder="e.g., 3" required></div>
        <div><label>Collateral Provided</label><input name="collateral_provided" placeholder="None"></div>
        <div style="grid-column:1 / -1">
          <label>Account Types</label><input name="account_types" placeholder="e.g., Mobile Money Loan, Local Store Credit">
        </div>
        <div>
          <label>Macroeconomic Risk Adjustment</label>
          <select name="macroeconomic_risk">
            <option>Low</option>
            <option>Medium</option>
            <option selected>High</option>
          </select>
        </div>
      </div>

      <div class="actions">
        <button class="btn primary" type="submit" name="action" value="preview">Calculate and Preview</button>
        <button class="btn secondary" type="submit" name="action" value="download_pdf">Download PDF</button>
        <button class="btn secondary" type="submit" name="action" value="save_csv">Save to CSV</button>
        <button class="btn danger" type="reset">Reset</button>
      </div>
    </form>
    <p><a href="/debug">Debug</a></p>
  </div>

  <script>
    function clamp(val, lo, hi) {
      if (isNaN(val)) return 0;
      return Math.max(lo, Math.min(hi, val));
    }
    function compute() {
      const limit = parseFloat(document.querySelector('[name="total_credit_limit"]').value) || 0;
      const bal = parseFloat(document.querySelector('[name="total_credit_balance"]').value) || 0;
      const util = (limit > 0) ? (bal / limit) * 100 : 0;
      document.querySelector('[name="credit_utilization_ratio"]').value = clamp(util, 0, 9999).toFixed(1);

      const otp = parseFloat(document.querySelector('[name="on_time_payments"]').value) || 0;
      const totp = parseFloat(document.querySelector('[name="total_payments"]').value) || 0;
      const ph = (totp > 0) ? (otp / totp) * 100 : 0;
      document.querySelector('[name="payment_history_score"]').value = clamp(ph, 0, 100).toFixed(1);

      const mdp = parseFloat(document.querySelector('[name="monthly_debt_payments"]').value) || 0;
      const gmi = parseFloat(document.querySelector('[name="gross_monthly_income"]').value) || 0;
      const dti = (gmi > 0) ? (mdp / gmi) * 100 : 0;
      document.querySelector('[name="debt_to_income_ratio"]').value = clamp(dti, 0, 9999).toFixed(1);
    }

    ['total_credit_limit','total_credit_balance','on_time_payments','total_payments','monthly_debt_payments','gross_monthly_income']
      .forEach(n => {
        const el = document.querySelector('[name="'+n+'"]');
        el.addEventListener('input', compute);
        el.addEventListener('change', compute);
      });
  </script>
</body>
</html>"""

FALLBACK_RESULT = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Credit Result</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 24px; background: #f6f7fb; }
    .card { max-width: 980px; margin: 0 auto; background: #fff; padding: 24px; border-radius: 10px; box-shadow: 0 6px 20px rgba(0,0,0,.08); }
    .pill { display:inline-block; padding:6px 10px; border-radius:20px; background:#e9edf7; }
    .grid { display:grid; grid-template-columns: repeat(2, 1fr); gap:8px 16px; }
    .btn { padding:10px 14px; border:none; border-radius:8px; cursor:pointer; background:#2f6fed; color:#fff }
    .logo { text-align:center; margin-bottom:16px; }
    .logo img { max-height:60px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">
      <img src="{{ url_for('static', filename='logo.png') }}" alt="Logo" onerror="this.style.display='none'">
    </div>
    <h1>Credit Scoring Result</h1>
    <p>Score Range: 300-850</p>
    <h2>Score: {{ score }} <span class="pill">{{ category }}</span></h2>
    <div class="grid">
      {% for k, v in data.items() %}
        <div><strong>{{ k }}</strong><br>{{ v }}</div>
      {% endfor %}
    </div>
    <form method="POST" style="margin-top:16px;">
      {% for k, v in data.items() %}
        <input type="hidden" name="{{ k }}" value="{{ v }}">
      {% endfor %}
      <button class="btn" type="submit" name="action" value="download_pdf">Download PDF Report</button>
    </form>
    <p style="margin-top:12px;"><a href="/">New customer</a></p>
  </div>
</body>
</html>"""

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
        elif not TEMPLATES_DIR.exists():
            TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print("[repair] _fix_templates_dir error: %s" % e, file=sys.stderr)

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

def _pct(num, den):
    try:
        num = float(num); den = float(den)
        if den <= 0: return 0.0
        return max(0.0, (num/den)*100.0)
    except Exception:
        return 0.0

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

def _wrap(c, text, x, y, width, leading=14, font="Helvetica", size=11):
    c.setFont(font, size)
    lines = simpleSplit(text, font, size, width)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y

def _kv_pair(c, label, value, x, y, w_label, w_value, leading=13):
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, f"{label}:")
    c.setFont("Helvetica", 11)
    return _wrap(c, str(value), x + w_label, y, w_value, leading=leading, font="Helvetica", size=11)

def generate_pdf(form_data, score, category):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    margin = 18*mm
    x_left = margin
    x_right = w - margin
    y = h - margin

    # Logo (optional)
    logo_path = STATIC_DIR / "logo.png"
    if logo_path.exists():
        try:
            img = ImageReader(str(logo_path))
            box_w = 50*mm; box_h = 18*mm
            iw, ih = img.getSize()
            ratio = min(box_w/iw, box_h/ih)
            lw = iw * ratio; lh = ih * ratio
            c.drawImage(img, (w - lw)/2, y - lh, lw, lh, preserveAspectRatio=True, mask='auto')
            y -= lh + 6*mm
        except Exception:
            y -= 2*mm

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w/2, y, "Credit Scoring Report")
    y -= 10*mm

    # Score banner
    c.setFillColor(colors.HexColor("#2f6fed"))
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x_left, y, f"Score: {score}  ({category})    Range: 300–850")
    c.setFillColor(colors.black)
    y -= 7*mm

    # Sections
    def section(title):
        nonlocal y
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x_left, y, title)
        y -= 1*mm
        c.setStrokeColor(colors.HexColor("#cbd2e6"))
        c.line(x_left, y, x_right, y)
        c.setStrokeColor(colors.black)
        y -= 5*mm

    col_gap = 12
    col_w = (x_right - x_left - col_gap)/2.0
    label_w = 52*mm
    value_w = col_w - label_w

    # Identity
    section("Identity")
    y0 = y
    y = _kv_pair(c, "Full Name", form_data["full_name"], x_left, y, label_w, value_w)
    y = _kv_pair(c, "Date of Birth", form_data["dob"], x_left, y, label_w, value_w)
    y = _kv_pair(c, "National ID", form_data["national_id"], x_left, y, label_w, value_w)
    y = _kv_pair(c, "Phone Number", form_data["phone_number"], x_left, y, label_w, value_w)
    y_r = y0
    y_r = _kv_pair(c, "Current Address", form_data["current_address"], x_left + col_w + col_gap, y_r, label_w, value_w)
    y = min(y, y_r) - 6*mm

    # Employment & Income
    section("Employment & Income")
    y0 = y
    y = _kv_pair(c, "Employment", form_data["employment"], x_left, y, label_w, value_w)
    y = _kv_pair(c, "Employer", form_data["employer"], x_left, y, label_w, value_w)
    y_r = y0
    y_r = _kv_pair(c, "Income Level", form_data["income_level"], x_left + col_w + col_gap, y_r, label_w, value_w)
    y = min(y, y_r) - 6*mm

    # Calculated Metrics
    section("Calculated Metrics")
    y0 = y
    y = _kv_pair(c, "Credit Utilization Ratio (%)", f'{form_data["credit_utilization_ratio"]:.1f}', x_left, y, label_w, value_w)
    y = _kv_pair(c, "Payment History Score (%)", f'{form_data["payment_history_score"]:.1f}', x_left, y, label_w, value_w)
    y_r = y0
    y_r = _kv_pair(c, "Debt-to-Income Ratio (%)", f'{form_data["debt_to_income_ratio"]:.1f}', x_left + col_w + col_gap, y_r, label_w, value_w)
    y = min(y, y_r) - 6*mm

    # Credit File Details
    section("Credit File Details")
    y0 = y
    y = _kv_pair(c, "Open Credit Lines", form_data["open_credit_lines"], x_left, y, label_w, value_w)
    y = _kv_pair(c, "Past Due Accounts", form_data["past_due_accounts"], x_left, y, label_w, value_w)
    y = _kv_pair(c, "Length of Credit History (years)", form_data["length_credit_history_years"], x_left, y, label_w, value_w)
    y_r = y0
    y_r = _kv_pair(c, "Recent Credit Inquiries (12m)", form_data["recent_inquiries_12m"], x_left + col_w + col_gap, y_r, label_w, value_w)
    y_r = _kv_pair(c, "Collateral Provided", form_data["collateral_provided"], x_left + col_w + col_gap, y_r, label_w, value_w)
    y_r = _kv_pair(c, "Account Types", form_data["account_types"], x_left + col_w + col_gap, y_r, label_w, value_w)
    y = min(y, y_r) - 6*mm

    # Macroeconomic
    section("Macroeconomic Risk")
    y = _kv_pair(c, "Adjustment", form_data["macroeconomic_risk"], x_left, y, label_w, value_w) - 4*mm

    # Footer / timestamp
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawRightString(x_right, margin, "Generated: " + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    c.setFillColor(colors.black)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf

def _ensure_csv_header(path: Path):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp","full_name","dob","national_id","current_address","phone_number",
                "employment","employer","income_level",
                "credit_utilization_ratio_pct","payment_history_score_pct","debt_to_income_ratio_pct",
                "open_credit_lines","past_due_accounts","length_credit_history_years","recent_inquiries_12m",
                "collateral_provided","account_types","macroeconomic_risk",
                "score","category"
            ])

def _append_csv(path: Path, fd: dict, score: int, category: str):
    _ensure_csv_header(path)
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.utcnow().isoformat(),
            fd["full_name"], fd["dob"], fd["national_id"], fd["current_address"], fd["phone_number"],
            fd["employment"], fd["employer"], fd["income_level"],
            f'{fd["credit_utilization_ratio"]:.1f}', f'{fd["payment_history_score"]:.1f}', f'{fd["debt_to_income_ratio"]:.1f}',
            fd["open_credit_lines"], fd["past_due_accounts"], fd["length_credit_history_years"], fd["recent_inquiries_12m"],
            fd["collateral_provided"], fd["account_types"], fd["macroeconomic_risk"],
            score, category
        ])

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
        "static_dir": str(STATIC_DIR),
        "static_list": os.listdir(STATIC_DIR) if STATIC_DIR.is_dir() else [],
        "data_dir": str(DATA_DIR),
        "data_list": os.listdir(DATA_DIR) if DATA_DIR.is_dir() else [],
        "csv_path": str(CSV_PATH) if CSV_PATH.exists() else None,
        "tree": tree
    })

@app.route("/repair", methods=["GET"])
def repair():
    ensure_templates()
    return jsonify({
        "repaired": True,
        "templates_dir": str(TEMPLATES_DIR),
        "has_templates_dir": TEMPLATES_DIR.is_dir(),
        "templates_list": os.listdir(TEMPLATES_DIR) if TEMPLATES_DIR.is_dir() else [],
    })

def _parse_float_form(name):
    try:
        return float(request.form.get(name,"") or 0)
    except Exception:
        return 0.0

def _parse_int_form(name):
    try:
        return int(request.form.get(name,"") or 0)
    except Exception:
        return 0

@app.route("/", methods=["GET","POST","HEAD"])
def index():
    if request.method == "HEAD":
        return Response(status=200)
    ensure_templates()
    if request.method == "GET":
        try:
            return render_template("form.html")
        except TemplateNotFound as e:
            return f"Template not found: {e}. Expected at: {TEMPLATES_DIR}", 500

    fd = {
        "full_name": request.form.get("full_name","").strip(),
        "dob": request.form.get("dob","").strip(),
        "national_id": request.form.get("national_id","").strip(),
        "current_address": request.form.get("current_address","").strip(),
        "phone_number": request.form.get("phone_number","").strip(),
        "employment": request.form.get("employment","").strip(),
        "employer": request.form.get("employer","").strip(),
        "income_level": request.form.get("income_level","").strip(),
        "total_credit_limit": _parse_float_form("total_credit_limit"),
        "total_credit_balance": _parse_float_form("total_credit_balance"),
        "on_time_payments": _parse_float_form("on_time_payments"),
        "total_payments": _parse_float_form("total_payments"),
        "monthly_debt_payments": _parse_float_form("monthly_debt_payments"),
        "gross_monthly_income": _parse_float_form("gross_monthly_income"),
        "credit_utilization_ratio": _parse_float_form("credit_utilization_ratio"),
        "payment_history_score": _parse_float_form("payment_history_score"),
        "debt_to_income_ratio": _parse_float_form("debt_to_income_ratio"),
        "open_credit_lines": _parse_int_form("open_credit_lines"),
        "past_due_accounts": _parse_int_form("past_due_accounts"),
        "length_credit_history_years": _parse_int_form("length_credit_history"),
        "recent_inquiries_12m": _parse_int_form("recent_inquiries"),
        "collateral_provided": request.form.get("collateral_provided","").strip(),
        "account_types": request.form.get("account_types","").strip(),
        "macroeconomic_risk": request.form.get("macroeconomic_risk","").strip(),
    }

    # server-side auto-calc
    util = _pct(fd["total_credit_balance"], max(0.0, fd["total_credit_limit"]))
    ph = _pct(fd["on_time_payments"], max(0.0, fd["total_payments"]))
    dti = _pct(fd["monthly_debt_payments"], max(0.0, fd["gross_monthly_income"]))
    if fd["total_credit_limit"] > 0: fd["credit_utilization_ratio"] = util
    if fd["total_payments"] > 0: fd["payment_history_score"] = ph
    if fd["gross_monthly_income"] > 0: fd["debt_to_income_ratio"] = dti

    score, category = calculate_credit_score(fd)
    action = request.form.get("action","preview")

    if action == "download_pdf":
        pdf = generate_pdf(fd, score, category)
        return send_file(pdf, as_attachment=True, download_name="credit_report.pdf", mimetype="application/pdf")

    if action == "save_csv":
        try:
            _append_csv(CSV_PATH, fd, score, category)
            fd["message"] = "Saved to CSV. Download latest at /csv"
        except Exception as e:
            fd["message"] = f"Failed to write CSV: {e}"

    return render_template("result.html", data=fd, score=score, category=category)

@app.route("/csv", methods=["GET"])
def csv_download():
    if not CSV_PATH.exists():
        return "No CSV yet. Use 'Save to CSV' first.", 404
    return send_file(str(CSV_PATH), as_attachment=True, download_name="records.csv", mimetype="text/csv")

if __name__ == "__main__":
    # Ensure templates exist even if mispackaged
    ensure_templates()
    app.run(host="0.0.0.0", port=5000, debug=True)
