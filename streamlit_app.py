
import subprocess
import sys
import streamlit as st

# Install missing packages
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install("yfinance")  # Add other missing packages here

# Rest of your code...

st.title("Stock Trading App")

# Verify file exists
if not os.path.exists("your_original_script.py"):
    st.error("Script file missing! Upload your_original_script.py to the repo.")
else:
    if st.button("Run Analysis"):
        with st.spinner("Running..."):
            result = subprocess.run(
                ["python", "your_original_script.py"], 
                capture_output=True, 
                text=True,
                cwd=os.getcwd()  # Sets working directory
            )
        
        st.code(result.stdout, language='bash')
        if result.stderr:
            st.error(result.stderr)
