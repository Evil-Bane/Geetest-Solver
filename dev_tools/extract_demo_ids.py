"""Extract captcha IDs from GeeTest demo pages."""
import requests
import re

DEMO_PAGES = {
    "slide": "https://gt4.geetest.com/demov4/slide-float-en.html",
    "icon": "https://gt4.geetest.com/demov4/icon-popup-en.html",
    "ai": "https://gt4.geetest.com/demov4/ai-float-en.html",
    "gobang": "https://gt4.geetest.com/demov4/winlinze-popup-en.html",
}

for name, url in DEMO_PAGES.items():
    html = requests.get(url).text
    # Look for captcha_id in various patterns
    ids = re.findall(r'captcha_id["\s:=]+["\']([a-f0-9]{32})["\']', html)
    if not ids:
        ids = re.findall(r'["\']([a-f0-9]{32})["\']', html)
    print(f"{name}: {ids}")
    # Also check for linked JS files
    js_files = re.findall(r'src=["\']([^"\']+\.js)', html)
    for js_url in js_files:
        if not js_url.startswith('http'):
            js_url = f"https://gt4.geetest.com{js_url}" if js_url.startswith('/') else f"https://gt4.geetest.com/demov4/{js_url}"
        try:
            js = requests.get(js_url, timeout=5).text
            js_ids = re.findall(r'captcha_id["\s:=]+["\']([a-f0-9]{32})["\']', js)
            if js_ids:
                print(f"  JS {js_url}: {js_ids}")
        except:
            pass
