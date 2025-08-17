"""
Insurance Quote Data Extraction Module

This module handles PDF text extraction and data parsing for insurance quotes.
Each insurer uses different terminology, so we'll create mappings for common terms.
"""

import io
import re
from typing import Any, Dict, List, Optional

import pdfplumber
import PyPDF2


class InsuranceDataExtractor:
    """Main class for extracting structured data from insurance quote PDFs"""
    
    def __init__(self):
        """Initialize the extractor with predefined mappings for different insurers"""
        
        # Define life insurance term mappings for the demo
        self.term_mappings = {
            # Life Insurance Sum Insured
            'life_insurance_sum': [
                'life insurance', 'sum insured life', 'life cover', 'death benefit',
                'life insurance sum insured', 'death cover', 'life benefit amount'
            ],
            
            # TPD Any Occupation Sum Insured
            'tpd_any_sum': [
                'tpd (any occupation)', 'tpd any occupation', 'total permanent disability any occupation',
                'tpd any occ', 'total permanent disability (any occupation)', 'tpd - any occupation'
            ],
            
            # TPD Own Occupation Sum Insured  
            'tpd_own_sum': [
                'tpd (own occupation)', 'tpd own occupation', 'total permanent disability own occupation',
                'tpd own occ', 'total permanent disability (own occupation)', 'tpd - own occupation'
            ],
            
            # Critical Illness Sum Insured
            'critical_illness_sum': [
                'critical illness insurance', 'critical illness', 'trauma insurance',
                'trauma cover', 'critical illness cover', 'serious illness cover'
            ],
            
            # Income Protection Sum Insured
            'income_protection_sum': [
                'income protection insurance', 'income protection', 'disability income',
                'monthly benefit', 'income cover', 'salary protection'
            ],
            
            # Premium variations for each type
            'life_insurance_premium': [
                'life insurance premium', 'life premium', 'death cover premium'
            ],
            
            'tpd_any_premium': [
                'tpd any occupation premium', 'tpd (any occupation) premium', 'tpd any occ premium'
            ],
            
            'tpd_own_premium': [
                'tpd own occupation premium', 'tpd (own occupation) premium', 'tpd own occ premium'
            ],
            
            'critical_illness_premium': [
                'critical illness premium', 'trauma premium', 'critical illness insurance premium'
            ],
            
            'income_protection_premium': [
                'income protection premium', 'income protection insurance premium', 'disability income premium'
            ],
            
            # Payment source
            'premium_source': [
                'premium paid from', 'where premium paid', 'payment source', 'funded from',
                'super fund', 'personal', 'superannuation', 'external'
            ],
            
            # Policy details
            'policy_number': [
                'policy number', 'policy no', 'quote number', 'quote no',
                'reference number', 'ref no', 'proposal number'
            ],
            
            'insurer_name': [
                'insurer', 'insurance company', 'underwriter', 'provider'
            ]
        }
        
        # Regex patterns for extracting monetary values
        self.money_patterns = [
            r'\$[\d,]+\.?\d*',  # $1,000.00 or $1,000
            r'[\d,]+\.?\d*\s*dollars?',  # 1,000 dollars
            r'AUD\s*[\d,]+\.?\d*',  # AUD 1,000
        ]
        
        # Regex patterns for policy numbers
        self.policy_patterns = [
            r'[A-Z]{2,4}\d{6,10}',  # ABC123456789
            r'\d{8,12}',  # 123456789012
            r'[A-Z]\d{7,9}',  # A12345678
        ]

    def extract_text_from_pdf(self, pdf_file) -> str:
        """
        Extract text from PDF using multiple methods for better coverage
        
        Args:
            pdf_file: File-like object containing PDF data
            
        Returns:
            str: Extracted text from the PDF
        """
        text = ""
        
        try:
            # Method 1: Try pdfplumber first (better for complex layouts)
            pdf_file.seek(0)
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # If pdfplumber didn't get much text, try PyPDF2
            if len(text.strip()) < 100:
                pdf_file.seek(0)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                    
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            
        return text

    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere
        text = re.sub(r'[^\w\s\$\.,\-\(\)]', ' ', text)
        return text.strip()

    def find_term_value(self, text: str, term_type: str) -> Optional[str]:
        """
        Find the value associated with a specific insurance term
        
        Args:
            text: The full text to search in
            term_type: The type of term to look for (from term_mappings)
            
        Returns:
            str: The found value or None
        """
        if term_type not in self.term_mappings:
            return None
            
        text_lower = text.lower()
        
        for term in self.term_mappings[term_type]:
            # Look for the term followed by currency or numeric values
            pattern = rf'{re.escape(term.lower())}[:\s]*([^\n]*?)(?:\n|$)'
            match = re.search(pattern, text_lower)
            
            if match:
                value_text = match.group(1).strip()
                
                # Extract monetary value if this is a money field
                if term_type in ['premium', 'excess', 'building_cover', 'contents_cover', 'liability_cover']:
                    money_value = self.extract_money_value(value_text)
                    if money_value:
                        return money_value
                        
                # For non-money fields, return the cleaned text
                elif term_type in ['policy_number', 'insurer_name']:
                    return value_text[:50]  # Limit length
                    
        return None

    def extract_money_value(self, text: str) -> Optional[float]:
        """Extract monetary value from text"""
        for pattern in self.money_patterns:
            match = re.search(pattern, text)
            if match:
                # Clean the matched value
                value_str = match.group(0)
                # Remove currency symbols and convert to float
                value_str = re.sub(r'[^\d,.]', '', value_str)
                value_str = value_str.replace(',', '')
                
                try:
                    return float(value_str)
                except ValueError:
                    continue
                    
        return None

    def identify_insurer(self, text: str, filename: str = "") -> str:
        """
        Identify the insurance company from the document
        
        Args:
            text: Full document text
            filename: Original filename for hints
            
        Returns:
            str: Identified insurer name
        """
        # Common Australian insurers
        known_insurers = [
            'AAMI', 'Allianz', 'Budget Direct', 'NRMA', 'Suncorp',
            'QBE', 'Youi', 'RACV', 'CommInsure', 'Virgin Money',
            'Woolworths Insurance', 'Coles Insurance', 'SGIC'
        ]
        
        text_upper = text.upper()
        
        # Check filename first
        for insurer in known_insurers:
            if insurer.upper() in filename.upper():
                return insurer
                
        # Then check document content
        for insurer in known_insurers:
            if insurer.upper() in text_upper:
                return insurer
                
        # Fallback: try to find "insurance" in the first few lines
        lines = text.split('\n')[:10]
        for line in lines:
            if 'insurance' in line.lower():
                # Extract potential company name
                words = line.split()
                for i, word in enumerate(words):
                    if 'insurance' in word.lower():
                        if i > 0:
                            return words[i-1]
                        
        return "Unknown Insurer"

    def extract_data_from_pdf(self, pdf_file, filename: str = "") -> Dict[str, Any]:
        """
        Main method to extract all relevant data from a PDF quote
        
        Args:
            pdf_file: File-like object containing PDF data
            filename: Original filename
            
        Returns:
            Dict containing extracted insurance data
        """
        # Extract and clean text
        raw_text = self.extract_text_from_pdf(pdf_file)
        clean_text = self.clean_text(raw_text)
        
        # Extract all the key data points for life insurance
        extracted_data = {
            'source_file': filename,
            'insurer': self.identify_insurer(clean_text, filename),
            'policy_number': self.find_term_value(clean_text, 'policy_number') or f"DEMO-{hash(filename) % 10000}",
            'raw_text': clean_text[:1000] + "..." if len(clean_text) > 1000 else clean_text,  # Store sample for debugging
        }
        
        # Extract Sum Insured amounts for each coverage type
        coverage_sums = {}
        coverage_sums['life_insurance'] = self.find_term_value(clean_text, 'life_insurance_sum')
        coverage_sums['tpd_any_occupation'] = self.find_term_value(clean_text, 'tpd_any_sum')
        coverage_sums['tpd_own_occupation'] = self.find_term_value(clean_text, 'tpd_own_sum')
        coverage_sums['critical_illness'] = self.find_term_value(clean_text, 'critical_illness_sum')
        coverage_sums['income_protection'] = self.find_term_value(clean_text, 'income_protection_sum')
        
        extracted_data['coverage_sums'] = coverage_sums
        
        # Extract Premium amounts for each coverage type
        premiums = {}
        premiums['life_insurance'] = self.find_term_value(clean_text, 'life_insurance_premium')
        premiums['tpd_any_occupation'] = self.find_term_value(clean_text, 'tpd_any_premium')
        premiums['tpd_own_occupation'] = self.find_term_value(clean_text, 'tpd_own_premium')
        premiums['critical_illness'] = self.find_term_value(clean_text, 'critical_illness_premium')
        premiums['income_protection'] = self.find_term_value(clean_text, 'income_protection_premium')
        
        extracted_data['premiums'] = premiums
        
        # Extract premium payment source
        premium_source = self.find_term_value(clean_text, 'premium_source')
        extracted_data['premium_source'] = premium_source
        
        return extracted_data

    def process_multiple_quotes(self, uploaded_files) -> List[Dict[str, Any]]:
        """
        Process multiple quote files and return structured data
        
        Args:
            uploaded_files: List of uploaded file objects from Streamlit
            
        Returns:
            List of dictionaries containing extracted data
        """
        all_quotes = []
        
        for file in uploaded_files:
            try:
                # Create a file-like object for processing
                pdf_bytes = io.BytesIO(file.read())
                
                # Extract data
                quote_data = self.extract_data_from_pdf(pdf_bytes, file.name)
                all_quotes.append(quote_data)
                
                # Reset file pointer for potential reuse
                file.seek(0)
                
            except Exception as e:
                print(f"Error processing {file.name}: {e}")
                # Add error placeholder with life insurance structure
                all_quotes.append({
                    'source_file': file.name,
                    'insurer': 'Error - Could not process',
                    'error': str(e),
                    'policy_number': 'N/A',
                    'coverage_sums': {
                        'life_insurance': 0,
                        'tpd_any_occupation': 0,
                        'tpd_own_occupation': 0,
                        'critical_illness': 0,
                        'income_protection': 0
                    },
                    'premiums': {
                        'life_insurance': 0,
                        'tpd_any_occupation': 0,
                        'tpd_own_occupation': 0,
                        'critical_illness': 0,
                        'income_protection': 0
                    },
                    'premium_source': 'Unknown'
                })
                
        return all_quotes


def customize_extraction_for_demo(extractor: InsuranceDataExtractor, 
                                demo_mappings: Dict[str, List[str]]) -> None:
    """
    Customize the extractor with specific terms you want to demo
    
    Args:
        extractor: The InsuranceDataExtractor instance
        demo_mappings: Dictionary of term types and their variations to look for
    """
    # Update the term mappings with demo-specific terms
    for term_type, variations in demo_mappings.items():
        if term_type in extractor.term_mappings:
            # Add demo terms to existing mappings
            extractor.term_mappings[term_type].extend(variations)
        else:
            # Create new mapping
            extractor.term_mappings[term_type] = variations


# Example usage and testing
if __name__ == "__main__":
    # Test the extractor
    extractor = InsuranceDataExtractor()
    
    # Example of how to customize for your demo
    demo_terms = {
        'premium': ['total annual premium', 'yearly payment'],
        'excess': ['standard excess', 'claim excess amount'],
        'building_cover': ['sum insured building', 'dwelling amount']
    }
    
    customize_extraction_for_demo(extractor, demo_terms)
    
    print("Data extractor initialized and ready for demo!")
    print(f"Configured to look for {len(extractor.term_mappings)} different term types")
