import streamlit.web.cli as stcli
import os, sys
import threading
import time
import webbrowser
import subprocess

def resolve_path(path):
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

def open_browser_in_app_mode(url):
    """Attempts to open the URL in 'App Mode' (no address bar) using Chrome/Edge."""
    time.sleep(2) # Give Streamlit time to start
    
    # Common paths for Chrome and Edge on Windows
    browser_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
    ]
    
    found_browser = False
    for path in browser_paths:
        if os.path.exists(path):
            try:
                subprocess.Popen([path, f"--app={url}"])
                found_browser = True
                break
            except Exception:
                continue
                
    if not found_browser:
        # Fallback to standard browser open
        webbrowser.open(url)

if __name__ == "__main__":
    app_path = resolve_path("app.py")
    
    # Start the browser launcher in a separate thread
    # Streamlit defaults to port 8501
    threading.Thread(target=open_browser_in_app_mode, args=("http://localhost:8501",), daemon=True).start()
    
    # Run Streamlit
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=true",  # Important: Don't let Streamlit open the browser itself
        "--server.port=8501",
        "--theme.base=light"
    ]
    
    sys.exit(stcli.main())