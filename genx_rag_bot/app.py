"""
CLI and optional minimal web UI for drafting Gen X influencer DM/comment replies.
Usage:
  python app.py              -- interactive CLI (paste message, get reply)
  python app.py --web        -- run minimal web server (textarea + Get reply)
Requires GOOGLE_API_KEY in .env or environment. Run python embed.py first to build the FAISS index.

Vercel imports the module-level `app` (Flask) for deployment.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def check_api_key() -> None:
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY is not set. Add it to .env or set the environment variable.")
        sys.exit(1)


def run_cli() -> None:
    from rag_chain import get_reply

    check_api_key()
    print("Gen X RAG Reply Bot (internal draft tool)")
    print("Paste a DM or comment, then press Enter. Empty line to exit.\n")

    while True:
        try:
            line = input("Paste DM or comment: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not line:
            print("Empty input. Exiting.")
            break
        try:
            reply = get_reply(line)
            print("\nSuggested reply:")
            print(reply)
            print()
        except Exception as e:
            print(f"Error: {e}\n")


# --- Flask app at module level for Vercel ---
try:
    from flask import Flask, request, jsonify, render_template_string
except ImportError:
    Flask = None  # type: ignore

HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Gen X Reply Draft</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; }
    textarea { width: 100%; min-height: 100px; margin-bottom: 0.5rem; }
    button { padding: 0.5rem 1rem; cursor: pointer; }
    .reply { margin-top: 1rem; white-space: pre-wrap; padding: 0.75rem; background: #f5f5f5; border-radius: 6px; }
    .error { color: #c00; }
  </style>
</head>
<body>
  <h1>Gen X RAG Reply Draft</h1>
  <p>Paste a DM or comment below and get an on-brand reply draft.</p>
  <form method="post" action="/">
    <textarea name="message" placeholder="Paste DM or comment here..." required></textarea>
    <br>
    <button type="submit">Get reply</button>
  </form>
  {% if reply is not none %}
  <div class="reply"><strong>Suggested reply:</strong><br>{{ reply }}</div>
  {% endif %}
  {% if error %}
  <div class="error">{{ error }}</div>
  {% endif %}
</body>
</html>
"""

if Flask is not None:
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index():
        from rag_chain import get_reply
        reply = None
        error = None
        if request.method == "POST":
            message = (request.form.get("message") or "").strip()
            if not message:
                error = "Please enter a message."
            else:
                try:
                    reply = get_reply(message)
                except Exception as e:
                    error = str(e)
        return render_template_string(HTML, reply=reply, error=error)

    @app.route("/api/reply", methods=["POST"])
    def api_reply():
        from rag_chain import get_reply
        data = request.get_json(force=True, silent=True) or {}
        message = (data.get("message") or "").strip()
        if not message:
            return jsonify({"error": "message is required"}), 400
        try:
            reply = get_reply(message)
            return jsonify({"reply": reply})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
else:
    app = None  # type: ignore


def run_web() -> None:
    check_api_key()
    if app is None:
        print("Install Flask for --web: pip install flask")
        sys.exit(1)
    print("Starting server at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    if "--web" in sys.argv:
        run_web()
    else:
        run_cli()
