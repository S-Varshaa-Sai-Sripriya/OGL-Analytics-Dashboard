import os
import sys
import streamlit.web.cli as stcli

# Vercel needs a top-level variable or function named 'handler' or 'app'
def handler(request):
    """
    This function acts as the entrypoint for Vercel's serverless runtime.
    It manually triggers the Streamlit CLI to run your main dashboard.
    """
    # Ensure we point to the correct app.py path relative to the root
    sys.argv = [
        "streamlit",
        "run",
        "app.py", 
        "--server.port", "8080",
        "--server.address", "0.0.0.0",
    ]
    # This invokes the streamlit main loop
    return stcli.main()

# For some versions of Vercel Python runtime, you might also need:
app = handler