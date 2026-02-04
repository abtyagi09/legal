"""Create a test PDF invoice for testing Document Intelligence"""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def create_invoice_pdf(filename="test_legal_invoice.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1*inch, height - 1*inch, "LEGAL SERVICES INVOICE")
    
    # Invoice details
    c.setFont("Helvetica", 12)
    y = height - 1.5*inch
    
    lines = [
        "",
        "Invoice Number: INV-2026-12345",
        "Date: February 4, 2026",
        "Due Date: March 4, 2026",
        "",
        "BILL TO:",
        "Tech Corporation LLC",
        "789 Innovation Drive",
        "San Francisco, CA 94105",
        "",
        "FROM:",
        "Legal Advisory Services",
        "321 Attorney Street",
        "New York, NY 10013",
        "",
        "SERVICES PROVIDED:",
        "- Contract Review and Analysis: $8,500.00",
        "- Legal Consultation (10 hours): $3,000.00",
        "- Document Preparation and Filing: $2,200.00",
        "- Research and Due Diligence: $1,800.00",
        "- Court Appearance Fee: $5,000.00",
        "",
        "SUBTOTAL: $20,500.00",
        "TAX (9%): $1,845.00",
        "TOTAL DUE: $22,345.00",
        "",
        "Payment Terms: Net 30 days",
        "Payment Methods: Wire Transfer, Check, ACH",
        "",
        "Thank you for choosing Legal Advisory Services.",
        "For questions, contact billing@legaladvisory.com"
    ]
    
    for line in lines:
        c.drawString(1*inch, y, line)
        y -= 0.25*inch
    
    c.save()
    print(f"Created {filename}")

if __name__ == "__main__":
    create_invoice_pdf()
