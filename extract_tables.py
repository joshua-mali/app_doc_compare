import json
import os
import re
from datetime import datetime

import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

# --- Step 0: Load Environment Variables ---
load_dotenv()
client = OpenAI()

# ==============================================================================
# --- PART 1: PDF DATA EXTRACTION ---
# ==============================================================================
def extract_quote_data(pdf_path):
    """
    Extracts raw text and tables from a PDF document.
    """
    print(f"--- Extracting raw data from: {pdf_path} ---")
    data = {"file_name": pdf_path, "tables": [], "pages": {}}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                page_text = page.extract_text()
                data["pages"][page_num] = page_text if page_text else ""
                
                # Use a robust table extraction strategy
                tables = page.extract_tables(table_settings={
                    "vertical_strategy": "lines", "horizontal_strategy": "lines", "snap_tolerance": 3
                })
                if not tables:
                    tables = page.extract_tables(table_settings={
                        "vertical_strategy": "text", "horizontal_strategy": "text", "snap_x_tolerance": 5
                    })
                
                if tables:
                    data["tables"].extend(tables)
    except Exception as e:
        print(f"ERROR reading {pdf_path}: {e}")
        return None
    return data

# ==============================================================================
# --- PART 2: FOCUSED AI SUMMARIZATION ---
# ==============================================================================
def summarize_policy_data(extracted_json, context_hint):
    """
    Takes raw extracted data from ONE PDF and asks the AI to
    summarize it into a clean, structured format, applying business rules.
    """
    prompt = f"""
    You are a data extraction specialist. From the RAW DATA provided below, extract all insurance coverages.
    Use this critical CONTEXT HINT to understand the data: "{context_hint}"

    Follow these rules precisely:
    1. Identify each distinct type of insurance coverage (e.g., "Life Insurance", "TPD", "Income Protection").
    2. For each coverage, find its `Sum Insured` and `Yearly Premium`. If a premium is monthly, multiply it by 12.
    3. **Determine the `Payment Source` using this strict rule: If the source text contains "Super" or "Superannuation", you MUST output "Superannuation". For ALL other cases (including "Personal", "Ordinary", "Cash Flow", or if it is not mentioned), you MUST output "Cash Flow". These are the only two valid options.**
    4. If any information is not found, use an empty string "" or null.
    5. Your output MUST be a JSON object containing a list called "coverages".

    RAW DATA:
    ```json
    {json.dumps(extracted_json)}
    ```

    REQUIRED JSON OUTPUT:
    ```json
    {{
      "coverages": [
        {{
          "coverage_type": "Life Insurance",
          "sum_insured": "$1,000,000",
          "yearly_premium": "2425.00",
          "payment_source": "Superannuation"
        }}
      ]
    }}
    ```
    """
    print(f"--- Getting clean data for context: {context_hint} ---")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data extraction AI that outputs only valid JSON according to strict rules."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("coverages", [])  # Return the list of coverages
    except Exception as e:
        print(f"An error occurred while cleaning data for '{context_hint}': {e}")
        return []

# ==============================================================================
# --- PART 3: FINAL REPORT ASSEMBLY ---
# ==============================================================================
def is_same_coverage_type(type1, type2):
    """
    A helper function to perform a smarter, keyword-based match between coverage types.
    """
    if not type1 or not type2:
        return False
    type1, type2 = type1.upper(), type2.upper()
    KEYWORDS = {
        "LIFE": ["LIFE"], "TPD": ["TPD", "TOTAL AND PERMANENT", "DISABLEMENT"],
        "INCOME": ["INCOME PROTECTION", "INCOME SECURE"], "TRAUMA": ["TRAUMA", "CRITICAL ILLNESS", "RECOVERY INSURANCE"]
    }
    for category, keywords in KEYWORDS.items():
        match1 = any(keyword in type1 for keyword in keywords)
        match2 = any(keyword in type2 for keyword in keywords)
        if match1 and match2:
            return True
    return False

def build_final_json(original_coverages, scenario_1_coverages, scenario_2_coverages):
    """
    Takes the clean lists of coverages and assembles the final JSON object
    needed for the PDF report using smart matching.
    """
    print("\n--- Assembling final report from clean data (using smart matching) ---")
    final_data = {"comparison_summary": [], "total_premiums": []}
    
    for original_cov in original_coverages:
        original_coverage_type = original_cov.get("coverage_type")
        scen1_cov = next((c for c in scenario_1_coverages if is_same_coverage_type(c.get("coverage_type"), original_coverage_type)), {})
        scen2_cov = next((c for c in scenario_2_coverages if is_same_coverage_type(c.get("coverage_type"), original_coverage_type)), {})

        quotes = []
        if scen1_cov:
            quotes.append({"insurer": "Scenario 1", **scen1_cov})
        if scen2_cov:
            quotes.append({"insurer": "Scenario 2", **scen2_cov})

        final_data["comparison_summary"].append({
            "coverage_type": original_coverage_type,
            "original_details": original_cov,
            "quotes": quotes
        })

    # (Placeholder for a more advanced totals calculation)
    final_data["total_premiums"].append({"insurer": "Original Policy"})
    if scenario_1_coverages: final_data["total_premiums"].append({"insurer": "Scenario 1"})
    if scenario_2_coverages: final_data["total_premiums"].append({"insurer": "Scenario 2"})
    return final_data

# ==============================================================================
# --- PART 4: PDF REPORT GENERATION ---
# ==============================================================================
def create_pdf_report(comparison_data, filename="Insurance_Comparison_Report.pdf"):
    """
    Generates the final PDF report from the structured data.
    """
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleStyle', fontName='Helvetica-Bold', fontSize=16, alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='DateStyle', fontName='Helvetica', fontSize=9, alignment=TA_RIGHT, leading=12))
    styles.add(ParagraphStyle(name='HeaderStyle', fontName='Helvetica-Bold', fontSize=14, spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name='TableHeaderStyle', fontName='Helvetica-Bold', fontSize=9, alignment=TA_CENTER, textColor=colors.whitesmoke))
    styles.add(ParagraphStyle(name='TableCellStyle', fontName='Helvetica', fontSize=9, alignment=TA_CENTER))

    def get_ordinal_day(d):
        return str(d) + ("th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th"))

    try: logo = Image('PC logo.png', width=1.5*inch, height=0.75*inch)
    except Exception: logo = Spacer(0, 0)
    now = datetime.now()
    formatted_date_str = f"{get_ordinal_day(now.day)} {now.strftime('%B %Y')}"
    title = Paragraph("Discussion Paper For Client as at", styles['TitleStyle'])
    current_date = Paragraph(formatted_date_str, styles['DateStyle'])
    header_table = Table([[logo, [title, current_date]]], colWidths=[1.7*inch, 5.8*inch])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(header_table)
    story.append(Spacer(1, 0.2*inch))

    TABLE_COL_WIDTHS = [3.0*inch, 1.8*inch, 1.3*inch, 1.4*inch]
    header_strings = ["Type of Policy", "Sum Insured", "Sample Yearly Premium", "Where is the premium being paid from?"]
    TABLE_HEADERS = [Paragraph(text, styles['TableHeaderStyle']) for text in header_strings]
    table_style = TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002060')), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F2F2F2'))])
    
    story.append(Paragraph("Existing Insurance and Premiums", styles['HeaderStyle']))
    original_table_data = [TABLE_HEADERS]
    for item in comparison_data.get("comparison_summary", []):
        details = item.get("original_details", {})
        row = [Paragraph(item.get("coverage_type", ""), styles['TableCellStyle']), Paragraph(details.get("sum_insured", ""), styles['TableCellStyle']), Paragraph(f'${details.get("yearly_premium", "0.00")}', styles['TableCellStyle']), Paragraph(details.get("payment_source", ""), styles['TableCellStyle'])]
        original_table_data.append(row)
    original_table = Table(original_table_data, colWidths=TABLE_COL_WIDTHS, repeatRows=1)
    original_table.setStyle(table_style)
    story.append(original_table)
    story.append(Spacer(1, 0.3*inch))

    scenarios = {}
    for item in comparison_data.get("comparison_summary", []):
        for quote in item.get("quotes", []):
            insurer = quote.get("insurer", "Unknown")
            if insurer not in scenarios: scenarios[insurer] = []
            scenarios[insurer].append([Paragraph(item.get("coverage_type", ""), styles['TableCellStyle']), Paragraph(quote.get("sum_insured", ""), styles['TableCellStyle']), Paragraph(f'${quote.get("yearly_premium", "0.00")}', styles['TableCellStyle']), Paragraph(quote.get("payment_source", ""), styles['TableCellStyle'])])
    
    for insurer, table_rows in scenarios.items():
        story.append(Paragraph(f"{insurer}", styles['HeaderStyle']))
        scenario_table_data = [TABLE_HEADERS] + table_rows
        scenario_table = Table(scenario_table_data, colWidths=TABLE_COL_WIDTHS, repeatRows=1)
        scenario_table.setStyle(table_style)
        story.append(scenario_table)
        story.append(Spacer(1, 0.3*inch))
        
    doc.build(story)
    print(f"\nSuccessfully generated PDF report: '{filename}'")

# ==============================================================================
# --- MAIN EXECUTION SCRIPT ---
# ==============================================================================
if __name__ == "__main__":
    
    files_to_process = {
        'original': 'data/Original Policy.pdf',
        'insurer1': 'data/Insurer 1.pdf',
        'insurer2a': 'data/Insurer 2A.pdf',
        'insurer2b': 'data/Insurer 2B.pdf',
    }
    
    original_coverages, scenario_1_coverages, scenario_2_coverages = [], [], []

    # Process Original Policy
    raw_original = extract_quote_data(files_to_process['original'])
    if raw_original:
        original_coverages = summarize_policy_data(raw_original, "This is the client's original, existing policy.")

    # Process Insurer 1
    raw_ins1 = extract_quote_data(files_to_process['insurer1'])
    if raw_ins1 and raw_ins1['pages'].get(1):
        scenario_1_coverages.extend(summarize_policy_data(raw_ins1['pages'][1], "This is Scenario 1 for Income Protection."))
    if raw_ins1 and raw_ins1['pages'].get(2):
        scenario_2_coverages.extend(summarize_policy_data(raw_ins1['pages'][2], "This is Scenario 2 for Income Protection."))
        
    # Process Insurer 2A
    raw_ins2a = extract_quote_data(files_to_process['insurer2a'])
    if raw_ins2a and len(raw_ins2a['tables']) > 1:
        scenario_1_coverages.extend(summarize_policy_data(raw_ins2a['tables'][1], "This is Scenario 1."))
        
    # Process Insurer 2B
    raw_ins2b = extract_quote_data(files_to_process['insurer2b'])
    if raw_ins2b and len(raw_ins2b['tables']) > 2:
        scenario_1_coverages.extend(summarize_policy_data(raw_ins2b['tables'][1], "This is Scenario 1."))
        scenario_2_coverages.extend(summarize_policy_data(raw_ins2b['tables'][2], "This is Scenario 2."))

    if not original_coverages:
        print("\nCRITICAL ERROR: Could not extract data from the Original Policy. Cannot proceed.")
    else:
        final_data_structure = build_final_json(original_coverages, scenario_1_coverages, scenario_2_coverages)
        
        print("\n--- Final comparison structure created. Generating PDF report... ---")
        # print(json.dumps(final_data_structure, indent=2)) # Uncomment to debug the final structure
        
        create_pdf_report(final_data_structure)