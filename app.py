import aiohttp
import asyncio
import uuid
import random
import os
import secrets
import re
import requests
import time
import json
from flask import Flask, request, jsonify
from urllib.parse import unquote

try:
    import SignerPy
except ImportError:
    os.system("pip install --upgrade pip")
    os.system("pip install SignerPy")
    import SignerPy

# ============================================
# Network & Configuration
# ============================================
class Network:
    def __init__(self):
        proxy = "infproxy_checkemail509:NLI8oq4ZQC2fJ3yJDcSv@proxy.infiniteproxies.com:1111"

        if proxy:
            self.proxy_dict = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
            self.proxy_str = f"http://{proxy}"
        else:
            self.proxy_dict = None
            self.proxy_str = None

        self.hosts = [
            "api31-normal-useast2a.tiktokv.com",
            "api22-normal-c-alisg.tiktokv.com",
            "api2.musical.ly",
            "api16-normal-useast5.tiktokv.us",
            "api16-normal-no1a.tiktokv.eu",
            "rc-verification-sg.tiktokv.com",
            "api31-normal-alisg.tiktokv.com",
            "api16-normal-c-useast1a.tiktokv.com",
            "api22-normal-c-useast1a.tiktokv.com",
            "api16-normal-c-useast1a.musical.ly",
            "api19-normal-c-useast1a.musical.ly",
            "api.tiktokv.com",
        ]

        self.send_hosts = [
            "api22-normal-c-alisg.tiktokv.com",
            "api31-normal-alisg.tiktokv.com",
            "api22-normal-probe-useast2a.tiktokv.com",
            "api16-normal-probe-useast2a.tiktokv.com",
            "rc-verification-sg.tiktokv.com"
        ]

        self.params = {
            'device_platform': 'android',
            'ssmix': 'a',
            'channel': 'googleplay',
            'aid': '1233',
            'app_name': 'musical_ly',
            'version_code': '360505',
            'version_name': '36.5.5',
            'manifest_version_code': '2023605050',
            'update_version_code': '2023605050',
            'ab_version': '36.5.5',
            'os_version': '10',
            "device_id": 0,
            'app_version': '30.1.2',
            "request_from": "profile_card_v2",
            "request_from_scene": '1',
            "scene": "1",
            "mix_mode": "1",
            "os_api": "34",
            "ac": "wifi",
            "request_tag_from": "h5",
        }

        self.headers = {
            'User-Agent': f'com.zhiliaoapp.musically/2022703020 (Linux; U; Android 7.1.2; en; SM-N975F; Build/N2G48H;tt-ok/{str(random.randint(1, 10**19))})'
        }

# ============================================
# 1SecMail disposable email
# ============================================
class OneSecMail:
    def __init__(self):
        self.api_base = "https://www.1secmail.com/api/v1/"

    async def gen(self):
        login = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(10))
        domain = "1secmail.com"
        email = f"{login}@{domain}"
        return email, login, domain

    async def mailbox(self, login, domain, timeout: int = 120):
        total = 0
        while total < timeout:
            await asyncio.sleep(3)
            total += 3
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.api_base}?action=getMessages&login={login}&domain={domain}"
                    async with session.get(url) as resp:
                        messages = await resp.json()
                        if messages:
                            message_id = messages[0]["id"]
                            url2 = f"{self.api_base}?action=readMessage&login={login}&domain={domain}&id={message_id}"
                            async with session.get(url2) as r:
                                msg = await r.json()
                                return msg.get("body", "")
            except Exception as e:
                await asyncio.sleep(3)
        return None

# ============================================
# MobileFlowFlexible
# ============================================
class MobileFlowFlexible:
    def __init__(self, account_param: str):
        self.input = account_param.strip()
        self.session = requests.Session()
        self.net = Network()

        if hasattr(self.net, 'proxy_str') and self.net.proxy_str:
            proxy_url = self.net.proxy_str
            if not proxy_url.startswith("http://") and not proxy_url.startswith("https://"):
                proxy_url = "http://" + proxy_url
            self.session.proxies = {"http": proxy_url, "https": proxy_url}

        self.base_params = self.net.params.copy()
        try:
            self.base_params = SignerPy.get(params=self.base_params)
        except Exception as e:
            print("Warning: SignerPy.get failed:", e)

        self.base_params.update({
            'device_type': f'rk{random.randint(3000, 4000)}s_{uuid.uuid4().hex[:4]}',
            'language': 'AR'
        })

        self.headers = self.net.headers.copy()

    def _variants(self):
        v = []
        raw = self.input
        v.append(raw)
        v.append(raw.strip().lower())
        seen = set()
        out = []
        for item in v:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    async def find_passport_ticket(self, timeout_per_host: int = 5):
        variants = self._variants()
        for acct in variants:
            for host in self.net.hosts:
                params = self.base_params.copy()
                ts = int(time.time())
                params['ts'] = ts
                params['_rticket'] = int(ts * 1000)
                params['account_param'] = acct
                try:
                    signature = SignerPy.sign(params=params)
                except Exception as e:
                    continue

                headers = self.headers.copy()
                headers.update({
                    'x-tt-passport-csrf-token': secrets.token_hex(16),
                    'x-ss-req-ticket': signature.get('x-ss-req-ticket', ''),
                    'x-ss-stub': signature.get('x-ss-stub', ''),
                    'x-argus': signature.get('x-argus', ''),
                    'x-gorgon': signature.get('x-gorgon', ''),
                    'x-khronos': signature.get('x-khronos', ''),
                    'x-ladon': signature.get('x-ladon', ''),
                })

                url = f"https://{host}/passport/account_lookup/email/"
                try:
                    resp = await asyncio.to_thread(self.session.post, url, params=params, headers=headers, timeout=timeout_per_host)
                    try:
                        j = resp.json()
                    except ValueError:
                        continue

                    if resp.status_code != 200:
                        continue

                    accounts = j.get('data', {}).get('accounts', [])
                    if not accounts:
                        continue

                    first = accounts[0]
                    ticket = first.get('passport_ticket') or first.get('not_login_ticket') or None
                    username = first.get('user_name') or first.get('username') or None
                    if ticket:
                        return ticket, acct, j
                    if username and not ticket:
                        return None, acct, j

                except requests.RequestException as e:
                    continue
        return None, None, None

    async def send_code_using_ticket(self, passport_ticket: str, timeout_mailbox: int = 60):
        mail_client = OneSecMail()
        mail, login, domain = await mail_client.gen()
        if not mail:
            return None, None

        params = self.base_params.copy()
        ts = int(time.time())
        params['ts'] = ts
        params['_rticket'] = int(ts * 1000)
        params['not_login_ticket'] = passport_ticket
        params['email'] = mail
        params['type'] = "3737"
        params.pop('fixed_mix_mode', None)
        params.pop('account_param', None)

        try:
            signature = SignerPy.sign(params=params)
        except Exception as e:
            return None, None

        headers = self.headers.copy()
        headers.update({
            'x-ss-req-ticket': signature.get('x-ss-req-ticket', ''),
            'x-ss-stub': signature.get('x-ss-stub', ''),
            'x-argus': signature.get('x-argus', ''),
            'x-gorgon': signature.get('x-gorgon', ''),
            'x-khronos': signature.get('x-khronos', ''),
            'x-ladon': signature.get('x-ladon', ''),
        })

        for host in self.net.send_hosts:
            url = f"https://{host}/passport/email/send_code"
            try:
                resp = await asyncio.to_thread(self.session.post, url, params=params, headers=headers, timeout=10)
                try:
                    j = resp.json()
                except ValueError:
                    continue

                if j.get("message") == "success" or j.get("status") == "success":
                    body = await mail_client.mailbox(login, domain, timeout=timeout_mailbox)
                    if not body:
                        return None, mail
                    # البحث عن اليوزر في الرسالة
                    ree = re.search(r'username[:\s]+([A-Za-z0-9_\.]+)', body, re.IGNORECASE)
                    if ree:
                        return ree.group(1).strip(), mail
                    return None, mail
            except requests.RequestException as e:
                continue
        return None, mail

# ============================================
# Flask API
# ============================================
app = Flask(__name__)

@app.route("/extract", methods=["GET"])
def extract():
    raw_email = request.args.get("email", "")
    timeout_mailbox = int(request.args.get("timeout_mailbox", "60"))

    email = unquote(raw_email).replace(" ", "").strip()
    flow = MobileFlowFlexible(account_param=email)

    async def run_flow():
        ticket, used_variant, resp_json = await flow.find_passport_ticket()
        if not ticket:
            return {"input": email, "status": "not_found"}

        username, mail_used = await flow.send_code_using_ticket(passport_ticket=ticket, timeout_mailbox=timeout_mailbox)
        status_final = "success" if username else "no_username"

        return {
            "input": email,
            "status": status_final,
            "username": username,
            "passport_ticket": ticket,
            "mail_used": mail_used,
            "used_variant": used_variant
        }

    result = asyncio.run(run_flow())
    return jsonify(result)

# ============================================
# Run Flask
# ============================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
