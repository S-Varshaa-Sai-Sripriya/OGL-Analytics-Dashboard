import os
import sys
import streamlit.web.cli as stcli

def handler(request):
    # This redirects the Vercel request to the Streamlit execution
    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        "--server.port", "8080",
        "--server.address", "0.0.0.0",
    ]
    stcli.main()