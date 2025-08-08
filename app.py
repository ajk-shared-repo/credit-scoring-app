
from flask import Flask, request, render_template, send_file
from generate_pdf import build_pdf_bytes

app = Flask(__name__, template_folder="templates")

@app.route("/health")
def health():
    return "ok", 200

@app.route("/")
def index():
    return '<h1>Prime Credit Reference Bureau</h1><p><a href="/form">Open the Individual Credit Report form</a></p>'

@app.route("/form", methods=["GET"])
def form():
    return render_template("form.html")

@app.route("/score", methods=["POST"])
def score():
    data = request.form.to_dict()
    data.setdefault("report_title", "Prime Credit Reference Bureau")
    data.setdefault("report_subtitle", "Individual Credit Report")

    pdf = build_pdf_bytes(data)
    filename = f"{data.get('Full_Name','credit_report')}_report.pdf".replace(' ', '_')
    return send_file(pdf, as_attachment=True, download_name=filename, mimetype="application/pdf")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
