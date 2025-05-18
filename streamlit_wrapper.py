import subprocess
import streamlit as st

st.title("Your Stock Analysis App")

# Run your original script
if st.button("Run Analysis"):
    with st.spinner("Analyzing stocks..."):
        result = subprocess.run(["python", "your_original_script.py"], 
                              capture_output=True, text=True)
        
    st.success("Analysis Complete!")
    st.text(result.stdout)  # Display console output
    if result.stderr:
        st.error(result.stderr)
