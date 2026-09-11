"""
LGC Trader - Standalone Desktop Launcher
Boots the multi-agent quant backend and opens a native dark-mode desktop window.
"""

import os
import sys
import time
import socket
import threading
import logging
import urllib.request
import webbrowser
import subprocess

# PyInstaller bundle path resolution
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
    os.chdir(os.path.dirname(sys.executable))
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.chdir(BUNDLE_DIR)

sys.path.insert(0, BUNDLE_DIR)

from version import APP_VERSION, APP_NAME

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("DesktopLauncher")


def find_free_port(preferred_port=8000):
    """Checks if preferred_port is open; if not, finds an available one."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', preferred_port)) != 0:
            return preferred_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


SERVER_PORT = find_free_port(8000)
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"


def start_uvicorn_server():
    """Runs the FastAPI server inside a background thread."""
    import uvicorn
    from server import app
    logger.info(f"Starting LGC Quant Engine on {SERVER_URL}...")
    uvicorn.run(app, host="127.0.0.1", port=SERVER_PORT, log_level="warning")


def wait_for_server(timeout=15.0):
    """Wait until the backend responds to HTTP requests."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(f"{SERVER_URL}/api/state", timeout=1.0) as response:
                if response.status == 200:
                    logger.info("LGC Quant Engine is live and responding.")
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def launch_browser_fallback():
    """Fallback to Microsoft Edge or Chrome App Mode if webview cannot initialize."""
    logger.info("Attempting to launch standalone browser window in App Mode...")
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    
    for p in edge_paths + chrome_paths:
        if os.path.exists(p):
            try:
                subprocess.Popen([p, f"--app={SERVER_URL}", "--window-size=1440,900"])
                return
            except Exception as e:
                logger.warning(f"Failed to launch {p}: {e}")
                
    webbrowser.open(SERVER_URL)


def main():
    logger.info(f"Launching {APP_NAME} v{APP_VERSION} Desktop Environment...")

    # Start FastAPI backend in background daemon thread
    server_thread = threading.Thread(target=start_uvicorn_server, daemon=True)
    server_thread.start()

    # Wait for server readiness
    if not wait_for_server(timeout=15.0):
        logger.error("Timed out waiting for backend server to initialize.")

    # Try launching native WebView window
    try:
        import webview
        logger.info("Initializing PyWebView native desktop window...")
        window = webview.create_window(
            title=f"{APP_NAME} v{APP_VERSION} - Autonomous Quant Terminal",
            url=SERVER_URL,
            width=1460,
            height=920,
            min_size=(1080, 720),
            background_color="#0a0b0e",
            text_select=True,
            zoomable=True
        )
        webview.start(debug=False)
        logger.info("Desktop window closed by user. Exiting LGC Trader.")
        sys.exit(0)
    except Exception as e:
        logger.warning(f"PyWebView initialization failed ({e}). Falling back to App Mode...")
        launch_browser_fallback()
        
        # Keep process alive while browser window is open
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupted. Shutting down.")
            sys.exit(0)


if __name__ == "__main__":
    main()
