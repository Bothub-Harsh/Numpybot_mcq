import os

TOKEN = os.environ.get("TOKEN")

if not TOKEN:
    raise RuntimeError("Missing TOKEN environment variable. Set it in Render before starting the bot.")
