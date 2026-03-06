#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import sys
import os

pages = [
    ("home", "http://localhost:3000"),
    ("login", "http://localhost:3000/login"),
    ("pricing", "http://localhost:3000/pricing"),
    ("career", "http://localhost:3000/career"),
    ("analytics", "http://localhost:3000/analytics"),
    ("reviews", "http://localhost:3000/reviews"),
    ("kanban", "http://localhost:3000/kanban"),
    ("interview", "http://localhost:3000/interview-coach"),
]

output_dir = "/home/admin/.openclaw/workspace/screenshots"
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    for name, url in pages:
        try:
            print(f"Capturing {name}...")
            page.goto(url, wait_until="networkidle", timeout=30000)
            screenshot_path = os.path.join(output_dir, f"{name}.png")
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"  ✓ Saved: {screenshot_path}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    browser.close()

print("\nAll screenshots captured!")
