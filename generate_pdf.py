
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_credit_report(data, score, grade, filename="credit_report.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Credit Report for {data.get('Full_Name')}", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Age: {data.get('Age')}", styles['Normal']))
    story.append(Paragraph(f"Education Level: {data.get('Education_Level')}", styles['Normal']))
    story.append(Paragraph(f"Employment Status: {data.get('Employment_Status')}", styles['Normal']))
    story.append(Paragraph(f"Monthly Income: ${data.get('Monthly_Income')}", styles['Normal']))
    story.append(Paragraph(f"Years in Business: {data.get('Years_in_Business')}", styles['Normal']))
    story.append(Paragraph(f"Previous Loan Status: {data.get('Previous_Loan_Status')}", styles['Normal']))
    story.append(Paragraph(f"Savings Account Balance: ${data.get('Savings_Account_Balance')}", styles['Normal']))
    story.append(Paragraph(f"Collateral Provided: {data.get('Collateral_Provided')}", styles['Normal']))
    story.append(Paragraph(f"House Ownership Status: {data.get('House_Ownership_Status')}", styles['Normal']))
    story.append(Paragraph(f"Mobile Money Usage: {data.get('Mobile_Money_Usage')}", styles['Normal']))
    story.append(Paragraph(f"Group Lending Participation: {data.get('Group_Lending_Participation')}", styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Credit Score: {score}", styles['Heading2']))
    story.append(Paragraph(f"Credit Grade: {grade}", styles['Heading2']))

    doc.build(story)
