from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    with open('../ganz-dijital-FINAL.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return html_content

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)