import io
import os
import sys
from contextlib import redirect_stdout

import pandas as pd
import streamlit as st

# Import functions from extract_tables module
try:
    import extract_tables
    from extract_tables import (build_final_json, create_pdf_report,
                                extract_quote_data, summarize_policy_data)
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Configure page
st.set_page_config(
    page_title="Insurance Quote Comparison Tool",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set up the Streamlit app
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("PC logo.png", width=300)
    except:
        pass
st.title('🏢 Insurance Quote Comparison Tool')

# Sidebar with explanations
with st.sidebar:
    # Company logo in sidebar
    try:
        st.image("PC logo.png", width=200)
    except:
        pass
    st.markdown("---")
    
    st.markdown("## 🎯 Demo Overview")
    st.markdown("""
    This tool demonstrates how **AI and Python** can automate insurance quote comparison for brokers.
    
    ### 📋 Traditional Manual Process:
    1. Customer requests revised coverage options
    2. Broker approaches multiple insurers for quotes  
    3. **Manual work**: Broker reads through each PDF quote
    4. **Manual work**: Broker extracts figures and creates comparison
    5. Broker sends comparison back to client
    
    ### 🤖 AI-Powered Automation:
    - **PDF Data Extraction**: AI reads and extracts tables from insurer PDFs
    - **Smart Matching**: AI matches coverage types across different insurers
    - **Automated Report**: Professional PDF comparison generated instantly
    """)
    
    st.markdown("---")
    st.markdown("## 📁 Required Files")
    st.markdown("""
    Upload these PDFs in any order:
    - **Original Policy**: Client's current policy
    - **Insurer 1**: First quote with scenarios
    - **Insurer 2A**: Second insurer's quote  
    - **Insurer 2B**: Alternative scenario from second insurer
    """)
    
    st.markdown("---")
    st.markdown("## 🔄 Process Steps")
    
    if not st.session_state.get('data_extracted', False):
        st.markdown("""
        **Step 1**: 📤 Upload PDF files  
        **Step 2**: ⚡ Click 'Generate Report'  
        **Step 3**: ✏️ Review & edit extracted data  
        **Step 4**: 📄 Generate final PDF comparison
        """)
    else:
        st.markdown("""
        ✅ **Step 1**: PDF files uploaded  
        ✅ **Step 2**: Data extracted successfully  
        🔄 **Step 3**: Review & edit data below  
        ⏳ **Step 4**: Generate final PDF comparison
        """)
    
    st.markdown("---")
    st.markdown("## 🛠️ Technology Stack")
    st.markdown("""
    - **PDF Processing**: pdfplumber
    - **AI Extraction**: OpenAI GPT-4
    - **Web Interface**: Streamlit  
    - **Report Generation**: ReportLab
    """)
    
    st.markdown("---")
    st.markdown("## 💡 Key Benefits")
    st.markdown("""
    - ⚡ **Speed**: Seconds vs hours of manual work
    - 🎯 **Accuracy**: AI reduces human errors
    - 📊 **Consistency**: Standardized output format
    - 🔄 **Scalability**: Handle multiple quotes easily
    """)

# Initialize session state
if 'data_extracted' not in st.session_state:
    st.session_state.data_extracted = False
if 'original_coverages' not in st.session_state:
    st.session_state.original_coverages = []
if 'scenario_1_coverages' not in st.session_state:
    st.session_state.scenario_1_coverages = []
if 'scenario_2_coverages' not in st.session_state:
    st.session_state.scenario_2_coverages = []
if 'console_logs' not in st.session_state:
    st.session_state.console_logs = []

# Function to capture console output
def capture_console_output(func, *args, **kwargs):
    f = io.StringIO()
    with redirect_stdout(f):
        result = func(*args, **kwargs)
    output = f.getvalue()
    if output:
        st.session_state.console_logs.extend(output.strip().split('\n'))
    return result

# Main content area
st.markdown("### 📤 Step 1: Upload Insurance Documents")
uploaded_files = st.file_uploader(
    "Choose PDF files", 
    type="pdf", 
    accept_multiple_files=True,
    help="Upload Original Policy, Insurer 1, Insurer 2A, and Insurer 2B PDFs"
)

if uploaded_files:
    st.success(f"✅ **{len(uploaded_files)} files uploaded successfully**")

else:
    st.info("📋 Please upload all 4 PDF documents to begin the automated comparison process.")

# Console logs display
if st.session_state.console_logs:
    st.markdown("### 📊 AI Processing Log")
    with st.expander("View detailed processing steps", expanded=False):
        for log in st.session_state.console_logs:
            st.text(log)

# Step 2: Generate Report
if uploaded_files:
    st.markdown("### ⚡ Step 2: AI Data Extraction")
    if st.button('🚀 Start AI Processing', type="primary", use_container_width=True):
        # Clear previous data and logs
        st.session_state.console_logs = []
        st.session_state.console_logs.append("Starting data extraction...")
        
        # Save uploaded files to a temporary directory
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_paths = {}
        for uploaded_file in uploaded_files:
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            # Match files to keys based on file name
            if "Original Policy" in uploaded_file.name:
                file_paths['original'] = file_path
                st.session_state.console_logs.append(f"Found Original Policy: {uploaded_file.name}")
            elif "Insurer 1" in uploaded_file.name:
                file_paths['insurer1'] = file_path
                st.session_state.console_logs.append(f"Found Insurer 1: {uploaded_file.name}")
            elif "Insurer 2A" in uploaded_file.name:
                file_paths['insurer2a'] = file_path
                st.session_state.console_logs.append(f"Found Insurer 2A: {uploaded_file.name}")
            elif "Insurer 2B" in uploaded_file.name:
                file_paths['insurer2b'] = file_path
                st.session_state.console_logs.append(f"Found Insurer 2B: {uploaded_file.name}")

        original_coverages, scenario_1_coverages, scenario_2_coverages = [], [], []

        # Process Original Policy
        if 'original' in file_paths:
            st.session_state.console_logs.append("Processing Original Policy...")
            raw_original = capture_console_output(extract_quote_data, file_paths['original'])
            if raw_original:
                original_coverages = capture_console_output(summarize_policy_data, raw_original, "This is the client's original, existing policy.")

        # Process Insurer 1
        if 'insurer1' in file_paths:
            st.session_state.console_logs.append("Processing Insurer 1...")
            raw_ins1 = capture_console_output(extract_quote_data, file_paths['insurer1'])
            if raw_ins1 and raw_ins1['pages'].get(1):
                scenario_1_coverages.extend(capture_console_output(summarize_policy_data, raw_ins1['pages'][1], "This is Scenario 1 for Income Protection."))
            if raw_ins1 and raw_ins1['pages'].get(2):
                scenario_2_coverages.extend(capture_console_output(summarize_policy_data, raw_ins1['pages'][2], "This is Scenario 2 for Income Protection."))

        # Process Insurer 2A
        if 'insurer2a' in file_paths:
            st.session_state.console_logs.append("Processing Insurer 2A...")
            raw_ins2a = capture_console_output(extract_quote_data, file_paths['insurer2a'])
            if raw_ins2a and len(raw_ins2a['tables']) > 1:
                extracted_coverages = capture_console_output(summarize_policy_data, raw_ins2a['tables'][1], "This is Scenario 1.")
                scenario_1_coverages.extend(extracted_coverages)

        # Process Insurer 2B
        if 'insurer2b' in file_paths:
            st.session_state.console_logs.append("Processing Insurer 2B...")
            raw_ins2b = capture_console_output(extract_quote_data, file_paths['insurer2b'])
            if raw_ins2b and len(raw_ins2b['tables']) > 2:
                scenario_1_coverages.extend(capture_console_output(summarize_policy_data, raw_ins2b['tables'][1], "This is Scenario 1."))
                scenario_2_coverages.extend(capture_console_output(summarize_policy_data, raw_ins2b['tables'][2], "This is Scenario 2."))
        
        # Store in session state
        st.session_state.original_coverages = original_coverages
        st.session_state.scenario_1_coverages = scenario_1_coverages
        st.session_state.scenario_2_coverages = scenario_2_coverages
        st.session_state.data_extracted = True
        st.session_state.console_logs.append("Data extraction completed!")
        
        # Force rerun to show the results
        st.rerun()

# Show editable tables if data has been extracted
if st.session_state.data_extracted:
    if not st.session_state.original_coverages:
        st.error("CRITICAL ERROR: Could not extract data from the Original Policy. Cannot proceed.")
    else:
        st.success("✅ **Data extraction completed successfully!** Review and edit the tables below before generating the PDF.")
        
        st.markdown("### ✏️ Step 3: Review & Edit Extracted Data")
        st.info("💡 **Tip**: You can edit any cell by clicking on it. Add or remove rows as needed.")
        
        # Convert coverages to DataFrames for editing
        def coverages_to_df(coverages, table_name):
            if not coverages:
                return pd.DataFrame(columns=['Coverage Type', 'Sum Insured', 'Yearly Premium', 'Payment Source'])
            
            data = []
            for coverage in coverages:
                data.append({
                    'Coverage Type': coverage.get('coverage_type', ''),
                    'Sum Insured': coverage.get('sum_insured', ''),
                    'Yearly Premium': str(coverage.get('yearly_premium', '')).replace('$', ''),
                    'Payment Source': coverage.get('payment_source', '')
                })
            return pd.DataFrame(data)
        
        # Create editable tables with improved layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📋 Original Policy")
            st.caption("Client's current insurance coverage")
            original_df = coverages_to_df(st.session_state.original_coverages, "Original")
            edited_original = st.data_editor(
                original_df, 
                use_container_width=True, 
                key="original_table",
                hide_index=True
            )
        
        with col2:
            st.markdown("#### 💼 Scenario 1")
            st.caption("First alternative quote option")
            scenario1_df = coverages_to_df(st.session_state.scenario_1_coverages, "Scenario 1")
            edited_scenario1 = st.data_editor(
                scenario1_df, 
                use_container_width=True, 
                key="scenario1_table",
                hide_index=True
            )
        
        with col3:
            st.markdown("#### 🔄 Scenario 2")
            st.caption("Second alternative quote option")
            scenario2_df = coverages_to_df(st.session_state.scenario_2_coverages, "Scenario 2")
            edited_scenario2 = st.data_editor(
                scenario2_df, 
                use_container_width=True, 
                key="scenario2_table",
                hide_index=True
            )
        
        st.markdown("### 📄 Step 4: Generate Professional Comparison Report")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            generate_pdf = st.button("🎯 Generate Professional PDF Report", type="primary", use_container_width=True)
        with col2:
            reset_button = st.button("🔄 Start Over", use_container_width=True)
        
        if generate_pdf:
            # Convert edited DataFrames back to coverage format
            def df_to_coverages(df):
                coverages = []
                for _, row in df.iterrows():
                    if row['Coverage Type']:  # Only include rows with coverage type
                        coverages.append({
                            'coverage_type': row['Coverage Type'],
                            'sum_insured': row['Sum Insured'],
                            'yearly_premium': row['Yearly Premium'],
                            'payment_source': row['Payment Source']
                        })
                return coverages
            
            # Convert edited data back to coverage format
            edited_original_coverages = df_to_coverages(edited_original)
            edited_scenario1_coverages = df_to_coverages(edited_scenario1)
            edited_scenario2_coverages = df_to_coverages(edited_scenario2)
            
            # Build final structure with edited data
            final_data_structure = build_final_json(edited_original_coverages, edited_scenario1_coverages, edited_scenario2_coverages)
            
            with st.spinner("🤖 AI is generating your professional PDF report..."):
                st.session_state.console_logs.append("Generating PDF report with edited data...")
                create_pdf_report(final_data_structure)
                st.session_state.console_logs.append("PDF generation completed!")
            
            # Display the generated PDF
            st.success("🎉 **PDF Report Generated Successfully!** Your professional insurance comparison report is ready for download.")
            
            with open("Insurance_Comparison_Report.pdf", "rb") as pdf_file:
                st.download_button(
                    label="📥 Download Professional Report", 
                    data=pdf_file, 
                    file_name="Insurance_Comparison_Report.pdf", 
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
        
        if reset_button:
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🤖 <strong>AI-Powered Insurance Quote Comparison</strong> | Demonstrating automation in insurance brokerage workflows</p>
    <p><em>This demo shows how AI can transform manual document processing into instant, accurate comparisons.</em></p>
</div>
""", unsafe_allow_html=True)
