import sys
import os
import asyncio
import time
import json
from curl_cffi.requests import AsyncSession
import phonenumbers
from phonenumbers import geocoder, carrier
from fake_headers import Headers
# from babel import Locale # Babel might be overkill if we just want language codes, but let's stick to user request if installed successfully.
# For now, let's implement the logic with phonenumbers first as it is the critical part for region. 
# Actually, the user code used Babel for locale. I will import it.
try:
    from babel import Locale
except ImportError:
    pass # Handle if not installed yet, but we are installing it.

# Add GeekedTest to path
current_dir = os.path.dirname(os.path.abspath(__file__))
geeked_path = os.path.join(current_dir, "GeekedTest")
sys.path.append(geeked_path)

try:
    from geeked.geeked import Geeked
except ImportError as e:
    print(f"Error importing Geeked: {e}")
    sys.exit(1)

# Constants
CAPTCHA_ID = "1c488faccae4bf4b71a363a0da1e979f"
CAMSCANNER_REFERER = "https://www.camscanner.com/"
SALT = "3rnx1qy239"

import hashlib
import random
import string

def parse_phone_info(phone_input):
    """
    Parses a raw phone input to extract country code and national number.
    Tries with and without '+' prefix.
    """
    try:
        # 1. Try parsing as-is (e.g. +1234567890)
        parsed = phonenumbers.parse(phone_input, None)
    except:
        try:
            # 2. Try prepending '+' (e.g. 1234567890 -> +1234567890)
            parsed = phonenumbers.parse(f"+{phone_input}", None)
        except:
            print("[-] Could not parse phone number. Please include country code.")
            return None, None

    if not phonenumbers.is_valid_number(parsed):
        print("[-] Invalid phone number format.")
        return None, None

    country_code = str(parsed.country_code)
    national_number = str(parsed.national_number)
    
    print(f"[*] Parsed Phone: +{country_code} {national_number}")
    return country_code, national_number

def get_spoofed_headers(phone_number):
    """
    Returns simple, static headers to match original script behavior.
    Reduces complexity to avoid 'unsafe' flags from aggressive spoofing.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": CAMSCANNER_REFERER,
        "Origin": "https://www.camscanner.com",
        "Priority": "u=1, i",
        "Accept": "application/json, text/plain, */*"
    }
    return headers

def get_random_user_agent():
    # ... fallback ...
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    ]
    return random.choice(user_agents)

def generate_random_client_id(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

import hashlib

def generate_sign(params):
    # Sort keys validation: keys = sorted(k for k in params if k not in ["sign", "sign_type"])
    # Canonical string: "&".join(f"{k}={params[k]}" for k in keys)
    # Sign: md5(canonical + SALT)
    
    keys = sorted(k for k in params if k not in ["sign", "sign_type"])
    canonical = "&".join(f"{k}={params[k]}" for k in keys)
    # print(f"[*] Canonical String: {canonical}")
    raw_sign = canonical + SALT
    return hashlib.md5(raw_sign.encode()).hexdigest()

from curl_cffi import requests

def send_sms(seccode_data, mobile_number, area_code="91", headers=None):
    """
    Executes the SMS send request using the verification tokens.
    """
    url = "https://api-cs-us.intsig.net/waf/user/cs/send_sms_vcode"
    
    # Session for SMS request
    session = requests.Session(impersonate="chrome124")
    
    # Use provided headers or default
    if headers:
        session.headers = headers
    else:
        session.headers = {
            "User-Agent": get_random_user_agent(),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": CAMSCANNER_REFERER,
            "Origin": "https://www.camscanner.com",
            "Priority": "u=1, i",
            "Accept": "application/json, text/plain, */*"
        }

    params = {
        "area_code": area_code,
        "jy_captcha_id": CAPTCHA_ID,
        "jy_captcha_output": seccode_data.get('captcha_output'),
        "jy_gen_time": seccode_data.get('gen_time'),
        "jy_lot_number": seccode_data.get('lot_number'),
        "jy_pass_token": seccode_data.get('pass_token'),
        "jy_version": "4",
        "language": "en-us",
        "mobile": mobile_number,
        "reason": "register_mobile",
        "timestamp": str(int(time.time() * 1000)),
        "sign_type": "md5",
    }
    
    # Generate Signature
    params['sign'] = generate_sign(params)
    
    print(f"[*] Step 3: Sending SMS to {mobile_number}")
    print(f"    Params: {json.dumps(params, indent=2)}")
    
    try:
        response = session.get(url, params=params)
        
        print("--- SMS Response ---")
        print(f"Status: {response.status_code}")
        print("Headers:")
        print(dict(response.headers))
        print("Content:")
        print(response.content)
        print("--------------------")

        return response.text
    except Exception as e:
        print(f"[!] SMS Request Failed: {e}")
        return None

def solve_captcha():
    # print(f"[*] Initializing Geeked Solver with Captcha ID: {CAPTCHA_ID}")
    try:
        # User suggested risk_type="slide" but the response indicated 'ai' type (no slide image).
        # Switching to risk_type="ai" to handle the adaptive/click-to-verify mode.
        geeked = Geeked(CAPTCHA_ID, risk_type="icon")
        
        # print("[*] Solver starting...")
        sec_code = geeked.solve()
        
        # print("[+] Captcha Solved!")
        # print(json.dumps(sec_code, indent=2))
        return sec_code
    except Exception as e:
        print(f"[!] Solver Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def verify_otp(seccode_data, mobile_number, otp_code, area_code="91", headers=None, client_id=None):
    """
    Executes the OTP verification request.
    """
    url = "https://api-cs-us.intsig.net/waf/user/cs/verify_sms_vcode"
    
    session = requests.Session(impersonate="chrome124")
    
    if headers:
        session.headers = headers
    else:
        session.headers = {
            "User-Agent": get_random_user_agent(),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": CAMSCANNER_REFERER,
            "Origin": "https://www.camscanner.com",
            "Priority": "u=1, i",
            "Accept": "application/json, text/plain, */*"
        }

    params = {
        "area_code": area_code,
        "client": "webcs_WEB",
        "client_app": "web_camscanner@6.0.0",
        "client_id": client_id or generate_random_client_id(),
        "jy_captcha_id": CAPTCHA_ID,
        "jy_captcha_output": seccode_data.get('captcha_output'),
        "jy_gen_time": seccode_data.get('gen_time'),
        "jy_lot_number": seccode_data.get('lot_number'),
        "jy_mobile": mobile_number,
        "jy_pass_token": seccode_data.get('pass_token'),
        "jy_version": "4",
        "mobile": mobile_number,
        "reason": "register_mobile",
        "timestamp": str(int(time.time() * 1000)),
        "token_life": "2592000",
        "vcode": otp_code,
        "sign_type": "md5",
    }
    
    # Generate Signature
    params['sign'] = generate_sign(params)
    
    # print(f"[*] Step 4: Verifying OTP {otp_code} for {mobile_number}")
    # print(f"    Params: {json.dumps(params, indent=2)}")
    
    try:
        response = session.get(url, params=params)
        
        print("--- Verify OTP Response ---")
        print(f"Status: {response.status_code}")
        print("Headers:")
        print(dict(response.headers))
        print("Content:")
        print(response.content)
        print("---------------------------")
        
        return response.text
    except Exception as e:
        print(f"[!] Verify Request Failed: {e}")
        return None



def main():
    print("--- CamScanner Geetest V4 Bypass & SMS Auth (Basic Headers) ---")
    
    # 1. Inputs
    raw_number = input("Enter Phone Number (with Country Code, e.g. 918467007382): ").strip()
    
    if not raw_number:
        print("[-] Phone number required.")
        return

    # Auto-detect area code and mobile
    area_code, mobile_number = parse_phone_info(raw_number)
    if not area_code or not mobile_number:
        return

    # 2. Dynamic Values
    client_id = generate_random_client_id()
    
    # generate spoofed headers using full number
    full_number = f"+{area_code}{mobile_number}"
    spoofed_headers = get_spoofed_headers(full_number)
    
    # print(f"[*] Generated Spoofing Params:")
    # print(f"    Client ID: {client_id}")
    # print(f"    User-Agent: {spoofed_headers.get('User-Agent')[:50]}...")
    # print(f"    Language: {spoofed_headers.get('Accept-Language')}")

    # 3. Solve Captcha
    seccode = solve_captcha()
    
    if seccode:
        # 4. Send SMS
        send_sms(seccode, mobile_number, area_code, headers=spoofed_headers)
        
        # 5. Verify OTP
        otp = input("Enter OTP received: ").strip()
        if otp:
            verify_otp(seccode, mobile_number, otp, area_code, headers=spoofed_headers, client_id=client_id)
        else:
            print("[-] No OTP entered, skipping verification.")
    else:
        print("[-] Exiting due to solver failure.")

if __name__ == "__main__":
    main()
