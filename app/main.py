import os
from flask import Flask, abort

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.route('/')
def home():
    html_path = os.path.join(BASE_DIR, 'ganz-dijital-FINAL.html')
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        abort(404)
    return html_content

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)