
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_credit_report(data, score, grade, filename="credit_report.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4)
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
    for field in fields:
        story.append(Paragraph(f"{field.replace('_', ' ')}: {data.get(field)}", styles['Normal']))

    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Credit Score: {score}", styles['Heading2']))
    story.append(Paragraph(f"Credit Grade: {grade}", styles['Heading2']))

    doc.build(story)
