import time

import httpx

base = "http://127.0.0.1:8000/api/v1"
time.sleep(1)
print("health", httpx.get("http://127.0.0.1:8000/health", timeout=15).status_code)


def login(mobile: str) -> str:
    httpx.post(f"{base}/auth/otp/request", json={"mobile": mobile}, timeout=60)
    r = httpx.post(
        f"{base}/auth/otp/verify",
        json={"mobile": mobile, "otp": "123456"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["data"]["access_token"]


token = login("+919999999999")
users = httpx.get(f"{base}/admin/users?page_size=10", headers={"Authorization": f"Bearer {token}"}, timeout=60)
print("main list", users.status_code, users.json()["data"]["pagination"]["total_count"])

t2 = login("+919888888888")
u2 = httpx.get(f"{base}/admin/users", headers={"Authorization": f"Bearer {t2}"}, timeout=60)
print("station", u2.status_code, [x["display_name"] for x in u2.json()["data"]["items"]])

t3 = login("+919111111111")
u3 = httpx.get(f"{base}/admin/users", headers={"Authorization": f"Bearer {t3}"}, timeout=60)
print("passenger forbidden", u3.status_code)
me = httpx.get(f"{base}/me", headers={"Authorization": f"Bearer {t3}"}, timeout=60)
print("me", me.status_code, me.json()["data"]["persona_label"])
