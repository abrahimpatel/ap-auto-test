#!/usr/bin/env python3
import sys, datetime, os

print("Script started")
print("cwd:", os.getcwd())
print("python:", sys.executable)
print("current time:", datetime.datetime.now().isoformat())

html_path = os.path.join(os.path.dirname(__file__), "rainfall_project.html")
if os.path.exists(html_path):
    print(f"Found {html_path}: {os.path.getsize(html_path)} bytes")
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            snippet = f.read(500)
        print("Preview of rainfall_project.html (first 500 chars):")
        print(snippet)
    except Exception as e:
        print("Error reading file:", e)
else:
    print("rainfall_project.html not found in project directory.")

print("Done")
