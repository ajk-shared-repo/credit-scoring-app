# generate_pdf.py

from io import BytesIO

from reportlab.lib.pagesizes import A4

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from reportlab.lib.styles import getSampleStyleSheet

def build_pdf_bytes(data, score, grade):

    buf = BytesIO()

    doc = SimpleDocTemplate(buf, pagesize=A4)

    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph(f"Credit Report for {data.get('Full_Name')}", styles['Title']))

    story.append(Spacer(1, 12))

    fields = [

        "Age", "Education_Level", "Employment_Status", "Monthly_Income",

        "Years_in_Business", "Previous_Loan_Status", "Savings_Account_Balance",

        "Collateral_Provided", "House_Ownership_Status", "Mobile_Money_Usage",

        "Group_Lending_Participation"

    ]

    for f in fields:

        story.append(Paragraph(f"{f.replace('_',' ')}: {data.get(f)}", styles['Normal']))

    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Credit Score: {score}", styles['Heading2']))

    story.append(Paragraph(f"Credit Grade: {grade}", styles['Heading2']))

    doc.build(story)

    buf.seek(0)

    return buf

