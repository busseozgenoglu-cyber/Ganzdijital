from flask import Flask
from pathlib import Path

app = Flask(__name__)


@app.route("/")
def home():
    index_path = Path(__file__).resolve().parent.parent / "index.html"
    return index_path.read_text(encoding="utf-8")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)