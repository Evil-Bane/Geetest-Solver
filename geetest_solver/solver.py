from uuid import uuid4
from curl_cffi import requests
import random, time, json
from .sign import Signer


class GeetestSolver:
    def __init__(self, captcha_id: str, risk_type: str, debug: bool = False, **kwargs):
        self.pass_token = None
        self.lot_number = None
        self.captcha_id = captcha_id
        self.challenge = str(uuid4())
        self.risk_type = risk_type
        self.debug = debug
        self.callback = GeetestSolver.random()
        self.session = requests.Session(impersonate="chrome124", **kwargs)
        self.session.headers = {
            "connection": "keep-alive",
            "sec-ch-ua-platform": "\"Windows\"",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua-mobile": "?0",
            "accept": "*/*",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-dest": "script",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9"
        }
        self.session.base_url = "https://gcaptcha4.geevisit.com"

    def _log(self, msg: str):
        if self.debug:
            print(f"[GeekedTest] {msg}")

    @staticmethod
    def random() -> str:
        return f"geetest_{int(random.random() * 10000) + int(time.time() * 1000)}"

    def format_response(self, response: str) -> dict:
        parsed = json.loads(response.split(f"{self.callback}(")[1][:-1])
        if "data" not in parsed:
            self._log(f"GeeTest error response: {json.dumps(parsed, indent=2)}")
            raise KeyError(f"'data' key missing. Status: {parsed.get('status')}, msg: {parsed.get('msg', parsed.get('desc', 'unknown'))}")
        return parsed["data"]

    def _fresh_challenge(self):
        """Reset challenge and callback for a new attempt."""
        self.challenge = str(uuid4())
        self.callback = GeetestSolver.random()

    def load_captcha(self):
        params = {
            "captcha_id": self.captcha_id,
            "challenge": self.challenge,
            "client_type": "web",
            "risk_type": self.risk_type,
            "lang": "eng",
            "callback": self.callback,
        }
        res = self.session.get("/load", params=params)
        data = self.format_response(res.text)
        self._log(f"Loaded captcha: type={data.get('captcha_type', 'N/A')}, lot={data.get('lot_number', 'N/A')[:12]}...")
        return data

    def submit_captcha(self, data: dict) -> dict:
        self.callback = GeetestSolver.random()

        params = {
            "callback": self.callback,
            "captcha_id": self.captcha_id,
            "client_type": "web",
            "lot_number": self.lot_number,
            "risk_type": self.risk_type,
            "payload": data["payload"],
            "process_token": data["process_token"],
            "payload_protocol": "1",
            "pt": "1",
            "w": Signer.generate_w(data, self.captcha_id, self.risk_type),
        }
        res = self.session.get("/verify", params=params).text
        res = self.format_response(res)

        if res.get("seccode") is None:
            # Handle 'continue' result (ai/invisible type)
            if res.get("result") == "continue":
                gen_time = res.get("gen_time") or data.get("gen_time") or data.get("datetime") or str(int(time.time()))
                return {
                    "lot_number": res.get("lot_number"),
                    "pass_token": res.get("process_token"),
                    "captcha_output": res.get("payload"),
                    "gen_time": gen_time,
                    "captcha_id": self.captcha_id
                }
            # Return the raw fail response for retry logic to handle
            return res

        return res["seccode"]

    def solve(self, max_retries: int = 5) -> dict:
        """
        Solve the captcha with retry logic.

        Args:
            max_retries: Maximum number of attempts before giving up (default: 5)

        Returns:
            dict: The seccode dict on success

        Raises:
            Exception: If all retries are exhausted
        """
        for attempt in range(1, max_retries + 1):
            try:
                self._fresh_challenge()
                data = self.load_captcha()
                self.lot_number = data["lot_number"]
                result = self.submit_captcha(data)

                # Check if it's a fail result (dict with 'result': 'fail')
                if isinstance(result, dict) and result.get("result") == "fail":
                    fail_count = result.get("fail_count", "?")
                    self._log(f"Attempt {attempt}/{max_retries}: FAIL (server fail_count={fail_count})")
                    if attempt < max_retries:
                        time.sleep(random.uniform(0.5, 1.5))
                        continue
                    raise Exception(f"Exceeded {max_retries} retries. Last result: fail (fail_count={fail_count})")

                # Success!
                self._log(f"Attempt {attempt}/{max_retries}: SUCCESS")
                return result

            except KeyError as e:
                self._log(f"Attempt {attempt}/{max_retries}: KeyError - {e}")
                if attempt < max_retries:
                    time.sleep(random.uniform(0.5, 1.5))
                    continue
                raise

            except Exception as e:
                # Don't retry on non-recoverable errors (e.g. NotImplementedError)
                if "not implemented" in str(e).lower():
                    raise
                self._log(f"Attempt {attempt}/{max_retries}: Error - {e}")
                if attempt < max_retries:
                    time.sleep(random.uniform(0.5, 1.5))
                    continue
                raise
