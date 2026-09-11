"""
LGC Trader - Standalone Desktop Launcher
Boots the multi-agent quant backend and opens a native dark-mode desktop window.
"""

import os
import sys
import io
import time
import socket
import threading
import logging
import urllib.request
import webbrowser
import subprocess
import traceback
import multiprocessing

# Critical fix for PyInstaller --windowed / --noconsole mode
# On Windows windowed apps, sys.stdout, sys.stderr, and sys.stdin are None.
# Libraries like uvicorn call sys.stdout.isatty(), causing AttributeError: 'NoneType' object has no attribute 'isatty'.
class SafeStream(io.StringIO):
    def write(self, s):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False

if sys.stdout is None:
    sys.stdout = SafeStream()
if sys.stderr is None:
    sys.stderr = SafeStream()
if sys.stdin is None:
    sys.stdin = io.StringIO()


# Windows native message box for critical diagnostics
def show_native_error(message: str, title: str = "LGC Trader - Startup Error"):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # MB_ICONERROR
    except Exception:
        pass


# Persistent logging directory
LOG_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "LGCTrader")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

log_handlers = [logging.FileHandler(LOG_FILE, encoding="utf-8")]
if sys.stdout and not isinstance(sys.stdout, SafeStream):
    log_handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=log_handlers
)
logger = logging.getLogger("DesktopLauncher")

# PyInstaller bundle path resolution
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BUNDLE_DIR)

from version import APP_VERSION, APP_NAME

def find_available_port(preferred_port: int = 8000) -> int:
    for port in [preferred_port, 8001, 8080, 8888, 9000, 9090]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


SERVER_PORT = find_available_port(8000)
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"
server_error = None


def start_uvicorn_server():
    """Runs the FastAPI server inside a background thread with full error handling."""
    global server_error
    try:
        import uvicorn
        from server import app
        logger.info(f"Starting LGC Quant Engine on {SERVER_URL}...")
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=SERVER_PORT,
            log_level="warning",
            log_config=None,
            loop="asyncio"
        )
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        server_error = traceback.format_exc()
        logger.critical(f"FATAL: Uvicorn server failed to start:\n{server_error}")


def wait_for_server(timeout=30.0):
    """Wait until the backend responds to HTTP requests."""
    start_time = time.time()
    logger.info(f"Waiting for backend to respond at {SERVER_URL}/api/state...")
    while time.time() - start_time < timeout:
        if server_error:
            logger.error(f"Server thread encountered fatal error:\n{server_error}")
            return False
        try:
            with urllib.request.urlopen(f"{SERVER_URL}/api/state", timeout=1.5) as response:
                if response.status == 200:
                    logger.info("LGC Quant Engine is live and responding.")
                    return True
        except Exception:
            time.sleep(0.5)
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
    multiprocessing.freeze_support()
    logger.info(f"Launching {APP_NAME} v{APP_VERSION} Desktop Environment...")

    # Start FastAPI backend in background daemon thread
    server_thread = threading.Thread(target=start_uvicorn_server, daemon=True)
    server_thread.start()

    # Wait for server readiness - DO NOT launch window until server is confirmed UP!
    if not wait_for_server(timeout=30.0):
        err_msg = server_error or "Backend server did not respond within 30 seconds.\nPlease check firewall and port 8000."
        logger.error(f"Server failed to start. {err_msg}")
        show_native_error(
            f"LGC Trader Engine failed to start:\n\n{err_msg}\n\nLog saved to:\n{LOG_FILE}",
            "LGC Trader Startup Error"
        )
        sys.exit(1)

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
