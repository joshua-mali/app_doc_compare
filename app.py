import base64
import io
from datetime import datetime

import pandas as pd
import streamlit as st

# Import our custom data extractor
from data_extractor import (InsuranceDataExtractor,
                            customize_extraction_for_demo)

# Page configuration
st.set_page_config(
    page_title="Insurance Quote Comparison Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #333;
        margin-bottom: 1rem;
    }
    .upload-section {
        border: 2px dashed #1f77b4;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .processing-box {
        background-color: #f0f8ff;
        border-left: 5px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #f0fff0;
        border-left: 5px solid #32cd32;
        padding: 1rem;
        margin: 1rem 0;
    }
    .comparison-table {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


def main():
    # Main header
    st.markdown(
        '<h1 class="main-header">🏢 Life Insurance Quote Comparison Tool</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="text-align: center; font-size: 1.2rem; color: #666;">Automate life insurance quote comparison with AI-powered data extraction</p>',
        unsafe_allow_html=True,
    )

    # Sidebar for demo info
    with st.sidebar:
        st.header("📋 Demo Overview")
        st.write(
            """
        **Manual Process (Before):**
        1. ✅ Customer requests life insurance review
        2. ✅ Broker contacts multiple insurers
        3. ✅ Receive PDF quotes with different layouts
        4. ❌ **Manual extraction of coverage amounts**
        5. ❌ **Manual extraction of premiums**
        6. ❌ **Create comparison spreadsheet**
        
        **AI Process (After):**
        1. ✅ Upload multiple insurer PDF quotes
        2. 🤖 **AI extracts coverage sums & premiums**
        3. 🤖 **Generate structured comparison**
        4. ✅ Download Excel report for client
        """
        )

        st.divider()

        st.header("🎯 Benefits")
        st.write(
            """
        - ⚡ **90% faster** quote processing
        - 🎯 **Eliminate manual extraction errors**
        - 📊 **Standardized life insurance comparisons**
        - 💰 **More time for client advisory**
        - 🔍 **Consistent data across all quotes**
        """
        )

    # Initialize session state
    if "processing_complete" not in st.session_state:
        st.session_state.processing_complete = False
    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = None

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        # Step 1: File Upload Section
        st.markdown(
            '<h2 class="sub-header">📄 Step 1: Upload Insurance Quotes</h2>',
            unsafe_allow_html=True,
        )

        with st.container():
            uploaded_files = st.file_uploader(
                "Choose PDF quote files",
                type=["pdf"],
                accept_multiple_files=True,
                help="Upload insurance quote PDFs from different insurers",
            )

            st.markdown("</div>", unsafe_allow_html=True)

        # Step 2: Template Upload
        st.markdown(
            '<h2 class="sub-header">📋 Step 2: Upload Quote Template (Optional)</h2>',
            unsafe_allow_html=True,
        )

        template_file = st.file_uploader(
            "Choose template file (Excel/PDF)",
            type=["xlsx", "xls", "pdf"],
            help="Upload your standard quote template or previous quote for reference",
        )

        # Step 3: Processing Section
        st.markdown(
            '<h2 class="sub-header">🤖 Step 3: AI Processing</h2>',
            unsafe_allow_html=True,
        )

        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} quote file(s) uploaded successfully")

            if st.button(
                "🚀 Start AI Processing", type="primary", use_container_width=True
            ):
                process_quotes(uploaded_files, template_file)
        else:
            st.info("👆 Upload quote files to begin processing")

    with col2:
        # Processing Status Panel
        st.markdown(
            '<h3 class="sub-header">📊 Processing Status</h3>', unsafe_allow_html=True
        )

        if uploaded_files:
            show_file_summary(uploaded_files)

        if st.session_state.processing_complete:
            show_processing_results()

    # Results Section (full width)
    if st.session_state.processing_complete and st.session_state.extracted_data:
        st.divider()
        st.markdown(
            '<h2 class="sub-header">📋 Step 4: Review & Download Results</h2>',
            unsafe_allow_html=True,
        )
        show_comparison_results()


def show_file_summary(uploaded_files):
    """Display summary of uploaded files"""
    st.markdown('<div class="processing-box">', unsafe_allow_html=True)
    st.write("**Uploaded Files:**")
    for i, file in enumerate(uploaded_files, 1):
        st.write(f"{i}. {file.name} ({file.size/1024:.1f} KB)")
    st.markdown("</div>", unsafe_allow_html=True)


def process_quotes(uploaded_files, template_file=None):
    """Process uploaded quote files with real AI extraction"""

    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Step 1: Initialize extractor
        status_text.text("🔧 Initializing AI extraction engine...")
        progress_bar.progress(0.2)
        
        extractor = InsuranceDataExtractor()
        
        # Customize for demo (you can modify these based on your specific PDFs)
        demo_terms = get_demo_term_mappings()
        customize_extraction_for_demo(extractor, demo_terms)

        # Step 2: Extract text from PDFs
        status_text.text("📄 Extracting text from PDFs...")
        progress_bar.progress(0.4)
        import time
        time.sleep(1)  # Brief pause for demo effect

        # Step 3: AI analysis
        status_text.text("🤖 AI analyzing quote content...")
        progress_bar.progress(0.6)
        
        # Process all uploaded files
        quotes_data = extractor.process_multiple_quotes(uploaded_files)
        
        # Step 4: Structure data
        status_text.text("📊 Structuring comparison data...")
        progress_bar.progress(0.8)
        time.sleep(0.5)

        # Step 5: Complete
        status_text.text("✅ Processing complete!")
        progress_bar.progress(1.0)

        # Prepare final data structure
        extracted_data = {
            'quotes': quotes_data,
            'processing_info': {
                'files_processed': len(uploaded_files),
                'extraction_method': 'AI-powered PDF analysis',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        # Store results in session state
        st.session_state.processing_complete = True
        st.session_state.extracted_data = extracted_data
        
        # Show success message with details
        with st.expander("🔍 View Extraction Details", expanded=False):
            for i, quote in enumerate(quotes_data):
                st.write(f"**File {i+1}: {quote['source_file']}**")
                st.write(f"- Insurer: {quote.get('insurer', 'Not detected')}")
                st.write(f"- Policy Number: {quote.get('policy_number', 'Not found')}")
                st.write(f"- Premium Source: {quote.get('premium_source', 'Not found')}")
                
                # Show coverage sums
                coverage_sums = quote.get('coverage_sums', {})
                st.write("**Coverage Sums:**")
                for coverage_type, amount in coverage_sums.items():
                    if amount:
                        st.write(f"  • {coverage_type.replace('_', ' ').title()}: ${amount:,.0f}" if isinstance(amount, (int, float)) else f"  • {coverage_type.replace('_', ' ').title()}: {amount}")
                    else:
                        st.write(f"  • {coverage_type.replace('_', ' ').title()}: Not found")
                
                # Show premiums
                premiums = quote.get('premiums', {})
                st.write("**Annual Premiums:**")
                for coverage_type, premium in premiums.items():
                    if premium:
                        st.write(f"  • {coverage_type.replace('_', ' ').title()}: ${premium:,.2f}" if isinstance(premium, (int, float)) else f"  • {coverage_type.replace('_', ' ').title()}: {premium}")
                    else:
                        st.write(f"  • {coverage_type.replace('_', ' ').title()}: Not found")
                
                if 'raw_text' in quote:
                    with st.expander("📄 Raw Text Preview"):
                        st.text(quote['raw_text'][:500] + "..." if len(quote['raw_text']) > 500 else quote['raw_text'])
                
                st.divider()

        st.rerun()
        
    except Exception as e:
        st.error(f"Error during processing: {str(e)}")
        status_text.text("❌ Processing failed")
        progress_bar.progress(0)


def get_demo_term_mappings():
    """
    Define specific terms to look for in your life insurance demo PDFs.
    These are customized for the life insurance quote template you provided.
    """
    return {
        # Life Insurance variations
        'life_insurance_sum': [
            'life insurance', 'sum insured life', 'life cover', 'death benefit',
            'life insurance sum insured', 'death cover amount'
        ],
        'life_insurance_premium': [
            'life insurance premium', 'life premium', 'death cover premium',
            'life insurance yearly premium', 'annual life premium'
        ],
        
        # TPD Any Occupation variations
        'tpd_any_sum': [
            'tpd (any occupation)', 'tpd any occupation', 'tpd any occ',
            'total permanent disability any occupation', 'tpd - any occupation'
        ],
        'tpd_any_premium': [
            'tpd any occupation premium', 'tpd (any occupation) premium',
            'tpd any occ premium', 'any occupation premium'
        ],
        
        # TPD Own Occupation variations  
        'tpd_own_sum': [
            'tpd (own occupation)', 'tpd own occupation', 'tpd own occ',
            'total permanent disability own occupation', 'tpd - own occupation'
        ],
        'tpd_own_premium': [
            'tpd own occupation premium', 'tpd (own occupation) premium',
            'tpd own occ premium', 'own occupation premium'
        ],
        
        # Critical Illness variations
        'critical_illness_sum': [
            'critical illness insurance', 'critical illness', 'trauma insurance',
            'trauma cover', 'serious illness', 'critical illness cover'
        ],
        'critical_illness_premium': [
            'critical illness premium', 'trauma premium', 'critical illness insurance premium',
            'serious illness premium'
        ],
        
        # Income Protection variations
        'income_protection_sum': [
            'income protection insurance', 'income protection', 'disability income',
            'monthly benefit', 'income cover', 'salary protection'
        ],
        'income_protection_premium': [
            'income protection premium', 'income protection insurance premium',
            'disability income premium', 'monthly benefit premium'
        ],
        
        # Premium source
        'premium_source': [
            'premium paid from', 'where premium paid from', 'payment source',
            'funded from', 'super fund', 'personal', 'superannuation'
        ]
    }


def generate_mock_data(uploaded_files):
    """Generate mock extracted data for demo purposes"""

    # Mock data structure representing extracted quote information
    data = {"quotes": []}

    # Generate mock data for each uploaded file
    insurer_names = ["Allianz Insurance", "AAMI Insurance", "Budget Direct"]

    for i, file in enumerate(uploaded_files):
        quote_data = {
            "source_file": file.name,
            "insurer": insurer_names[i % len(insurer_names)],
            "policy_number": f"POL-{1000 + i}",
            "premium": 1200 + (i * 150),
            "excess": 500 + (i * 100),
            "coverage_limits": {
                "building": 800000 + (i * 50000),
                "contents": 100000 + (i * 20000),
                "liability": 20000000,
            },
            "features": [
                "Flood cover included",
                "New for old replacement",
                "24/7 claims service",
            ],
        }
        data["quotes"].append(quote_data)

    return data


def show_processing_results():
    """Show processing completion status"""
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.write("✅ **Processing Complete!**")
    st.write("🤖 AI successfully extracted data from all quotes")
    st.write("📊 Comparison table generated")
    st.markdown("</div>", unsafe_allow_html=True)


def show_comparison_results():
    """Display the comparison results and download options"""

    data = st.session_state.extracted_data

    if not data or "quotes" not in data:
        st.error("No data available for comparison")
        return

    # Create comparison table
    st.markdown(
        '<h3 class="sub-header">📊 Quote Comparison</h3>', unsafe_allow_html=True
    )

    # Prepare data for display - Life Insurance specific
    comparison_data = []
    for quote in data["quotes"]:
        # Handle life insurance data structure
        coverage_sums = quote.get('coverage_sums', {})
        premiums = quote.get('premiums', {})
        
        # Format monetary values safely
        def format_money(value):
            if isinstance(value, (int, float)) and value > 0:
                return f"${value:,.0f}"
            elif isinstance(value, str) and value.replace(',', '').replace('$', '').replace('.', '').isdigit():
                return f"${float(value.replace(',', '').replace('$', '')):,.0f}"
            else:
                return "Not found"
        
        # Calculate total premium
        total_premium = 0
        for premium_val in premiums.values():
            if isinstance(premium_val, (int, float)):
                total_premium += premium_val
        
        comparison_data.append(
            {
                "Insurer": quote.get("insurer", "Unknown"),
                "Source File": quote.get("source_file", "Unknown"),
                "Life Insurance Sum": format_money(coverage_sums.get('life_insurance', 0)),
                "TPD Any Occ Sum": format_money(coverage_sums.get('tpd_any_occupation', 0)),
                "TPD Own Occ Sum": format_money(coverage_sums.get('tpd_own_occupation', 0)),
                "Critical Illness Sum": format_money(coverage_sums.get('critical_illness', 0)),
                "Income Protection Sum": format_money(coverage_sums.get('income_protection', 0)),
                "Total Annual Premium": format_money(total_premium) if total_premium > 0 else "Not calculated",
                "Premium Source": quote.get('premium_source', 'Not found'),
            }
        )

    # Display as DataFrame
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True)

    # Download section
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Download Excel Report", use_container_width=True):
            excel_file = create_excel_report(data)
            st.download_button(
                label="💾 Save Excel File",
                data=excel_file,
                file_name=f"insurance_comparison_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with col2:
        if st.button("📄 Download PDF Report", use_container_width=True):
            st.info("PDF generation will be implemented next!")

    with col3:
        if st.button("🔄 Process New Quotes", use_container_width=True):
            # Reset session state
            st.session_state.processing_complete = False
            st.session_state.extracted_data = None
            st.rerun()


def create_excel_report(data):
    """Create Excel report from extracted data"""

    # Create Excel file in memory
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Life Insurance Summary sheet
        summary_data = []
        for quote in data["quotes"]:
            coverage_sums = quote.get('coverage_sums', {})
            premiums = quote.get('premiums', {})
            
            # Calculate total premium
            total_premium = sum(p for p in premiums.values() if isinstance(p, (int, float)))
            
            summary_data.append(
                {
                    "Insurer": quote.get("insurer", "Unknown"),
                    "Source File": quote.get("source_file", "Unknown"),
                    "Policy Number": quote.get("policy_number", "N/A"),
                    "Premium Source": quote.get("premium_source", "Unknown"),
                    "Life Insurance Sum": coverage_sums.get("life_insurance", 0),
                    "TPD Any Occupation Sum": coverage_sums.get("tpd_any_occupation", 0),
                    "TPD Own Occupation Sum": coverage_sums.get("tpd_own_occupation", 0),
                    "Critical Illness Sum": coverage_sums.get("critical_illness", 0),
                    "Income Protection Sum": coverage_sums.get("income_protection", 0),
                    "Life Insurance Premium": premiums.get("life_insurance", 0),
                    "TPD Any Occupation Premium": premiums.get("tpd_any_occupation", 0),
                    "TPD Own Occupation Premium": premiums.get("tpd_own_occupation", 0),
                    "Critical Illness Premium": premiums.get("critical_illness", 0),
                    "Income Protection Premium": premiums.get("income_protection", 0),
                    "Total Annual Premium": total_premium,
                }
            )

        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name="Quote Comparison", index=False)

        # Add a life insurance recommendations sheet
        if data['quotes']:
            # Find quote with lowest total premium
            lowest_premium_quote = min(data['quotes'], 
                                     key=lambda q: sum(p for p in q.get('premiums', {}).values() if isinstance(p, (int, float))))
            
            # Find quote with highest total coverage
            highest_coverage_quote = max(data['quotes'], 
                                       key=lambda q: sum(c for c in q.get('coverage_sums', {}).values() if isinstance(c, (int, float))))
            
            lowest_total = sum(p for p in lowest_premium_quote.get('premiums', {}).values() if isinstance(p, (int, float)))
            highest_total = sum(c for c in highest_coverage_quote.get('coverage_sums', {}).values() if isinstance(c, (int, float)))
            
            recommendations = pd.DataFrame(
                {
                    "Recommendation": [
                        "Lowest Premium Option",
                        "Highest Coverage Option",
                        "Key Considerations",
                        "Next Steps",
                    ],
                    "Details": [
                        f"{lowest_premium_quote.get('insurer', 'Unknown')} - ${lowest_total:,.0f} total annual premium",
                        f"{highest_coverage_quote.get('insurer', 'Unknown')} - ${highest_total:,.0f} total coverage",
                        "Compare coverage types, premium sources (super vs personal), and waiting periods",
                        "Review policy terms, exclusions, and client's specific needs and budget",
                    ],
                }
            )
        else:
            recommendations = pd.DataFrame({
                "Recommendation": ["No Data"],
                "Details": ["No quotes processed successfully"]
            })
        recommendations.to_excel(writer, sheet_name="Recommendations", index=False)

    output.seek(0)
    return output.getvalue()


if __name__ == "__main__":
    main()
