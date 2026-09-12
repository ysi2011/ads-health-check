"""Ads Health Check — web entry point (Vercel serverless function).

Wraps the same CLI logic (parser.py / report.py / html_report.py) behind a
tiny Flask app: GET shows an upload form, POST runs the CSV through the
existing analysis and returns the rendered HTML report.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request

from html_report import generate_empty_html_report, generate_html_report
from parser import load_keyword_report
from report import low_ctr_keywords, optimization_suggestions, wasted_spend_keywords

app = Flask(__name__)

UPLOAD_FORM = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Ads Health Check</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         max-width: 640px; margin: 4rem auto; padding: 0 1.5rem; color: #1a1a1a; }
  h1 { margin-bottom: 0.25rem; }
  p.subtitle { color: #666; margin-top: 0; }
  form { border: 2px dashed #ddd; border-radius: 10px; padding: 2rem; margin-top: 2rem; text-align: center; }
  input[type=submit] { margin-top: 1rem; background: #1a1a1a; color: #fff; border: none;
                        border-radius: 6px; padding: 0.6rem 1.4rem; font-size: 0.95rem; cursor: pointer; }
  .error { color: #b42318; background: #fef2f1; border-radius: 6px; padding: 0.75rem 1rem; margin-top: 1rem; }
</style>
</head>
<body>
  <h1>Ads Health Check</h1>
  <p class="subtitle">Upload a Google Ads keyword-performance CSV export to get a report.</p>
  <form method="post" enctype="multipart/form-data">
    <input type="file" name="csv_file" accept=".csv" required>
    <br>
    <input type="submit" value="Analyze">
  </form>
  {{error_html}}
</body>
</html>
"""


def _render_form(error_html: str = "") -> str:
    return UPLOAD_FORM.replace("{{error_html}}", error_html)


@app.route("/", defaults={"_path": ""}, methods=["GET", "POST"])
@app.route("/<path:_path>", methods=["GET", "POST"])
def handle(_path):
    if request.method == "GET":
        return index()
    return analyze()


def index():
    return _render_form()


def analyze():
    uploaded = request.files.get("csv_file")
    if not uploaded or not uploaded.filename:
        return _render_form('<p class="error">Please choose a CSV file.</p>')

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        uploaded.save(tmp.name)
        tmp_path = tmp.name

    try:
        df = load_keyword_report(tmp_path)
    except (FileNotFoundError, ValueError) as e:
        return _render_form(f'<p class="error">{e}</p>')
    finally:
        os.unlink(tmp_path)

    if df.empty:
        return generate_empty_html_report(uploaded.filename)

    low_ctr_df = low_ctr_keywords(df)
    wasted_df = wasted_spend_keywords(df)
    suggestions = optimization_suggestions(df, low_ctr_df, wasted_df)
    return generate_html_report(uploaded.filename, df, low_ctr_df, wasted_df, suggestions)
