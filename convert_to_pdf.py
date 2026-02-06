"""
Convert legal text documents to PDF format
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
import os

def create_pdf_from_text(text_file, pdf_file):
    """Convert a text file to a formatted PDF"""
    
    # Read the text content
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Create custom styles only if they don't exist
    if 'Justify' not in styles:
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontSize=11, leading=14))
    if 'CustomTitle' not in styles:
        styles.add(ParagraphStyle(name='CustomTitle', fontSize=16, alignment=TA_CENTER, spaceAfter=20, bold=True))
    if 'CustomHeading' not in styles:
        styles.add(ParagraphStyle(name='CustomHeading', fontSize=13, spaceAfter=12, bold=True))
    
    # Process content line by line
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            # Add spacing for empty lines
            elements.append(Spacer(1, 0.2 * inch))
            continue
        
        # Determine style based on content
        if line.isupper() and len(line) < 100:
            # All caps short lines are likely titles/headers
            style = styles['CustomTitle']
        elif line.startswith('ARTICLE') or line.startswith('Section ') or line.startswith('WHEREAS'):
            style = styles['CustomHeading']
        else:
            style = styles['Justify']
        
        # Create paragraph
        try:
            para = Paragraph(line, style)
            elements.append(para)
        except Exception as e:
            # Fallback for problematic text
            para = Paragraph(line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), style)
            elements.append(para)
    
    # Build PDF
    doc.build(elements)
    print(f"Created: {pdf_file}")

def convert_all_documents():
    """Convert all text documents in sample_documents to PDF"""
    
    source_dir = "sample_documents"
    
    # Get all .txt files
    txt_files = [f for f in os.listdir(source_dir) if f.endswith('.txt')]
    
    print(f"Converting {len(txt_files)} documents to PDF...\n")
    
    for txt_file in txt_files:
        txt_path = os.path.join(source_dir, txt_file)
        pdf_file = txt_file.replace('.txt', '.pdf')
        pdf_path = os.path.join(source_dir, pdf_file)
        
        try:
            create_pdf_from_text(txt_path, pdf_path)
        except Exception as e:
            print(f"Error converting {txt_file}: {e}")
    
    print(f"\n✓ Conversion complete! PDFs created in {source_dir}/")

if __name__ == "__main__":
    convert_all_documents()
