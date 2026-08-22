import os
import subprocess
import markdown

# Load markdown text
md_path = os.path.join(os.path.dirname(__file__), 'PROJECT_DOCUMENTATION.md')
html_path = os.path.join(os.path.dirname(__file__), 'PROJECT_DOCUMENTATION.html')
pdf_path = os.path.join(os.path.dirname(__file__), 'PROJECT_DOCUMENTATION.pdf')

with open(md_path, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convert markdown to html with tables extension
html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

# Format HTML with academic document CSS matching PDF guidelines
full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>BCA Mini Project Documentation Report</title>
<style>
  @page {{
    size: A4;
    margin: 1in 1in 1in 1.25in;
  }}
  body {{
    font-family: 'Times New Roman', Times, serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #000;
    margin: 0;
    padding: 0;
    text-align: justify;
  }}
  h1 {{
    font-size: 16pt;
    font-weight: bold;
    text-transform: uppercase;
    text-align: center;
    page-break-before: always;
    margin-top: 2rem;
    margin-bottom: 1.5rem;
  }}
  h1:first-of-type {{
    page-break-before: avoid;
  }}
  h2 {{
    font-size: 14pt;
    font-weight: bold;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
  }}
  h3 {{
    font-size: 12pt;
    font-weight: bold;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
    font-size: 11pt;
  }}
  table, th, td {{
    border: 1px solid #000;
  }}
  th, td {{
    padding: 6px 10px;
    text-align: left;
  }}
  th {{
    background-color: #f2f2f2;
    font-weight: bold;
  }}
  code, pre {{
    font-family: 'Courier New', Courier, monospace;
    font-size: 10pt;
    background-color: #f8f8f8;
  }}
  pre {{
    padding: 10px;
    border: 1px solid #ccc;
    white-space: pre-wrap;
    word-break: break-all;
  }}
  hr {{
    border: none;
    border-top: 1px solid #aaa;
    margin: 2rem 0;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(full_html)

print(f"[HTML] Generated: {html_path}")

# Attempt conversion to PDF via Microsoft Edge Headless CLI
edge_paths = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
]

edge_exe = None
for path in edge_paths:
    if os.path.exists(path):
        edge_exe = path
        break

if edge_exe:
    print(f"[PDF] Using Microsoft Edge at {edge_exe}")
    cmd = [
        edge_exe,
        '--headless',
        '--disable-gpu',
        f'--print-to-pdf={pdf_path}',
        html_path
    ]
    subprocess.run(cmd, check=True)
    print(f"[PDF] Successfully created: {pdf_path}")
else:
    print("[PDF] Edge executable not found. HTML generated.")
