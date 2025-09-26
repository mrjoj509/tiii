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
        self.proxy = "proxy.infiniteproxies.com:1111:infproxy_checkemail509:IgtVZEgqhJVSPQDz3YSv"
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
# MailTM disposable email
# ============================================
class MailTM:
    def __init__(self):
        self.url = "https://api.mail.tm"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    async def gen(self):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(f"{self.url}/domains") as resp:
                    data = await resp.json()
                    domain = data["hydra:member"][0]["domain"]
                local = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(12))
                mail = f"{local}@{domain}"
                payload = {"address": mail, "password": local}
                async with session.post(f"{self.url}/accounts", json=payload) as resp:
                    await resp.json()
                async with session.post(f"{self.url}/token", json=payload) as resp:
                    token = await resp.json()
                    return mail, token.get("token")
            except Exception as e:
                print("mail.tm gen error:", e)
                return None, None

    async def mailbox(self, token: str, timeout: int = 120):
        async with aiohttp.ClientSession(headers={**self.headers, "Authorization": f"Bearer {token}"}) as session:
            total = 0
            while total < timeout:
                await asyncio.sleep(3)
                total += 3
                try:
                    async with session.get(f"{self.url}/messages") as resp:
                        inbox = await resp.json()
                        messages = inbox.get("hydra:member", [])
                        if messages:
                            id = messages[0]["id"]
                            async with session.get(f"{self.url}/messages/{id}") as r:
                                msg = await r.json()
                                return msg.get("text", "")
                except Exception as e:
                    await asyncio.sleep(3)
            print(f"[LOG] Mailbox timeout ({timeout}s)")
            return None

# ============================================
# MobileFlowFlexible
# ============================================
class MobileFlowFlexible:
    def __init__(self, account_param: str):
        self.input = account_param.strip()
        self.session = requests.Session()
        self.net = Network()
        if self.net.proxy:
            self.session.proxies = {"http": self.net.proxy, "https": self.net.proxy}
        self.base_params = self.net.params.copy()
        # generate random device_id for international numbers
        self.base_params['device_id'] = random.randint(100000000000000, 999999999999999)
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
        v = [self.input]
        if self.input.isdigit():
            try:
                v.append(self.input.encode().hex())
            except Exception:
                pass
        v.append(self.input.strip().lower())
        return list(dict.fromkeys(v))

    async def find_passport_ticket(self, timeout_per_host: int = 10):
        variants = self._variants()
        print("Trying variants:", variants)
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
                    print(f"[LOG] SignerPy.sign failed for host {host}: {e}")
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
                url = f"https://{host}/passport/account_lookup/mobile/"
                try:
                    resp = await asyncio.to_thread(self.session.post, url, params=params, headers=headers, timeout=timeout_per_host)
                    try:
                        j = resp.json()
                    except ValueError:
                        print(f"[{host}] non-json response: {resp.text[:300]}")
                        continue
                    print(f"[{host}] FULL RESPONSE (mobile): {json.dumps(j, ensure_ascii=False, indent=2)}")
                    if resp.status_code != 200 or not j:
                        print(f"[{host}] status {resp.status_code} -> response text: {resp.text[:300]}")
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
                    print(f"[{host}] request error: {e}")
                    continue
        return None, None, None

    async def send_code_using_ticket(self, passport_ticket: str, timeout_mailbox: int = 120):
        mail_client = MailTM()
        mail, token = await mail_client.gen()
        if not mail or not token:
            print("[LOG] Failed to create mail.tm account.")
            return None, None
        print("[LOG] Created disposable mail:", mail)
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
            print("[LOG] SignerPy.sign failed for send_code:", e)
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
            for attempt in range(3):  # retry 3 مرات
                try:
                    resp = await asyncio.to_thread(self.session.post, url=f"https://{host}/passport/email/send_code", params=params, headers=headers, timeout=10)
                    try:
                        j = resp.json()
                    except ValueError:
                        print(f"[send_code {host}] non-json response: {resp.text[:300]}")
                        continue
                    print(f"[send_code {host}] FULL RESPONSE: {json.dumps(j, ensure_ascii=False, indent=2)}")
                    if j.get("message") == "success" or j.get("status") == "success":
                        body = await mail_client.mailbox(token, timeout=timeout_mailbox)
                        if not body:
                            print(f"[LOG] No email arrived in mailbox (timeout {timeout_mailbox}s)")
                            continue
                        print("[LOG] Full email body:")
                        print(body)
                        ree = re.search(r'تم إنشاء هذا البريد الإلكتروني من أجل\s+(.+)\.', body)
                        if ree:
                            return ree.group(1).strip(), mail
                        ree2 = re.search(r'username[:\s]+([A-Za-z0-9_\.]+)', body, re.IGNORECASE)
                        if ree2:
                            return ree2.group(1).strip(), mail
                        return None, mail
                    else:
                        print(f"[LOG] send_code not success, attempt {attempt+1}")
                        time.sleep(2)
                        continue
                except requests.RequestException as e:
                    print(f"[LOG] send_code request error for host {host}: {e}")
                    time.sleep(2)
                    continue
        return None, mail

# ============================================
# Flask API
# ============================================
app = Flask(__name__)

@app.route("/extract", methods=["GET"])
def extract():
    raw_phone = request.args.get("phone", "")
    timeout_mailbox = int(request.args.get("timeout_mailbox", "120"))
    phone = unquote(raw_phone).replace(" ", "").strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    print(f"[LOG] استعلام جديد برقم: {phone}")
    flow = MobileFlowFlexible(account_param=phone)
    async def run_flow():
        try:
            ticket, used_variant, resp_json = await flow.find_passport_ticket()
        except Exception as e:
            return {"status": "error", "message": str(e)}
        if not ticket:
            return {"status": "not_found", "used_variant": used_variant, "raw_response": resp_json}
        username, mail_used = await flow.send_code_using_ticket(passport_ticket=ticket, timeout_mailbox=timeout_mailbox)
        return {"status": "success" if username else "no_username", "username": username, "passport_ticket": ticket, "mail_used": mail_used, "raw_response": resp_json}
    result = asyncio.run(run_flow())
    return jsonify(result)

# ============================================
# Run Flask
# ============================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
