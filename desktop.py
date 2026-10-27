"""desktop.py - launches the DTR Generator in its own native window (no browser, no console).

    python desktop.py
Falls back to the default browser if the native window cannot start (e.g. WebView2 missing).
"""
import logging, os, socket, sys, threading, time, traceback, webbrowser

if sys.stdout is None: sys.stdout = open(os.devnull, "w")     # windowed .exe has no console
if sys.stderr is None: sys.stderr = open(os.devnull, "w")
logging.getLogger("werkzeug").setLevel(logging.ERROR)

import app as A


def start_server():
    A.auto_backup()
    """Start the local server on a free port and return that port."""
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    threading.Thread(target=lambda: A.app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False),
                     daemon=True).start()
    for _ in range(100):                                       # wait until it answers
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close(); break
        except OSError:
            time.sleep(0.1)
    return port


def log_error():
    with open(os.path.join(A.DATA, "error.log"), "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + traceback.format_exc() + "\n")


def main():
    port = start_server(); url = f"http://127.0.0.1:{port}"
    try:
        import webview
        webview.settings["ALLOW_DOWNLOADS"] = True            # PDF / ZIP / Excel downloads show a Save dialog
        webview.create_window("DTR Generator - CSC Form 48", url, width=1380, height=880, min_size=(1000, 650))
        webview.start()
    except Exception:                                          # no pywebview / no WebView2 -> use the browser
        log_error()
        webbrowser.open(url)
        while True:
            time.sleep(3600)


if __name__ == "__main__":
    main()
