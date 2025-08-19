import os

import streamlit as st

from extract_tables import (build_final_json, create_pdf_report,
                            extract_quote_data, summarize_policy_data)

# Set up the Streamlit app
st.title('Insurance Quote Comparison Tool')

# File uploader
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

# Placeholder for console logs
console_output = st.empty()

# Process files when uploaded and button is clicked
if uploaded_files and st.button('Generate Report'):
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
        elif "Insurer 1" in uploaded_file.name:
            file_paths['insurer1'] = file_path
        elif "Insurer 2A" in uploaded_file.name:
            file_paths['insurer2a'] = file_path
        elif "Insurer 2B" in uploaded_file.name:
            file_paths['insurer2b'] = file_path

    original_coverages, scenario_1_coverages, scenario_2_coverages = [], [], []

    # Process Original Policy
    if 'original' in file_paths:
        raw_original = extract_quote_data(file_paths['original'])
        if raw_original:
            original_coverages = summarize_policy_data(raw_original, "This is the client's original, existing policy.")

    # Process Insurer 1
    if 'insurer1' in file_paths:
        raw_ins1 = extract_quote_data(file_paths['insurer1'])
        if raw_ins1 and raw_ins1['pages'].get(1):
            scenario_1_coverages.extend(summarize_policy_data(raw_ins1['pages'][1], "This is Scenario 1 for Income Protection."))
        if raw_ins1 and raw_ins1['pages'].get(2):
            scenario_2_coverages.extend(summarize_policy_data(raw_ins1['pages'][2], "This is Scenario 2 for Income Protection."))

    # Process Insurer 2A
    if 'insurer2a' in file_paths:
        raw_ins2a = extract_quote_data(file_paths['insurer2a'])
        if raw_ins2a and len(raw_ins2a['tables']) > 1:
            scenario_1_coverages.extend(summarize_policy_data(raw_ins2a['tables'][1], "This is Scenario 1."))

    # Process Insurer 2B
    if 'insurer2b' in file_paths:
        raw_ins2b = extract_quote_data(file_paths['insurer2b'])
        if raw_ins2b and len(raw_ins2b['tables']) > 2:
            scenario_1_coverages.extend(summarize_policy_data(raw_ins2b['tables'][1], "This is Scenario 1."))
            scenario_2_coverages.extend(summarize_policy_data(raw_ins2b['tables'][2], "This is Scenario 2."))

    if not original_coverages:
        st.error("CRITICAL ERROR: Could not extract data from the Original Policy. Cannot proceed.")
    else:
        final_data_structure = build_final_json(original_coverages, scenario_1_coverages, scenario_2_coverages)

        st.write("--- Final comparison structure created. Generating PDF report... ---")

        create_pdf_report(final_data_structure)

        # Display the generated PDF
        st.write("### Generated PDF Report")
        with open("Insurance_Comparison_Report.pdf", "rb") as pdf_file:
            st.download_button(label="Download PDF", data=pdf_file, file_name="Insurance_Comparison_Report.pdf", mime="application/pdf")

        # Display console logs
        console_output.text("Console logs will appear here...")
