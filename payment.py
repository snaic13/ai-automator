import os
import hashlib
import urllib.parse

ROBOKASSA_SHOP_ID = os.environ.get("ROBOKASSA_SHOP_ID", "")
ROBOKASSA_PASSWORD1 = os.environ.get("ROBOKASSA_PASSWORD1", "")
ROBOKASSA_PASSWORD2 = os.environ.get("ROBOKASSA_PASSWORD2", "")
ROBOKASSA_TEST_PASSWORD1 = os.environ.get("ROBOKASSA_TEST_PASSWORD1", "")
ROBOKASSA_TEST_PASSWORD2 = os.environ.get("ROBOKASSA_TEST_PASSWORD2", "")
ROBOKASSA_TEST = os.environ.get("ROBOKASSA_TEST", "1") == "1"

PLANS = {
    "starter": {"name": "Стартовый", "price": 490, "currency": "RUB", "requests_limit": 100, "days": 30},
    "pro": {"name": "Про", "price": 1490, "currency": "RUB", "requests_limit": 500, "days": 30},
    "business": {"name": "Бизнес", "price": 4990, "currency": "RUB", "requests_limit": 9999, "days": 30},
}


def robokassa_init_url(inv_id: str, amount: float, description: str, email: str, success_url: str, fail_url: str, requests: str = "") -> str:
    pwd1 = ROBOKASSA_TEST_PASSWORD1 if ROBOKASSA_TEST and ROBOKASSA_TEST_PASSWORD1 else ROBOKASSA_PASSWORD1
    if not ROBOKASSA_SHOP_ID or not pwd1:
        return ""

    out_sum = f"{amount:.2f}"
    shp_parts = [f"Shp_Email={email}"]
    if requests:
        shp_parts.append(f"Shp_Requests={requests}")
    shp_parts.sort()
    shp_str = ":" + ":".join(shp_parts) if shp_parts else ""
    crc_str = f"{ROBOKASSA_SHOP_ID}:{out_sum}:{inv_id}:{pwd1}{shp_str}"

    signature = hashlib.md5(crc_str.encode()).hexdigest()

    clean_desc = description.replace(":", "").replace(";", "").replace("&", "")

    params = {
        "MerchantLogin": ROBOKASSA_SHOP_ID,
        "OutSum": out_sum,
        "InvId": inv_id,
        "Description": clean_desc,
        "Email": email,
        "SignatureValue": signature,
        "Shp_Email": email,
    }
    if requests:
        params["Shp_Requests"] = requests
    if ROBOKASSA_TEST:
        params["IsTest"] = "1"

    return "https://auth.robokassa.ru/Merchant/Index.aspx?" + urllib.parse.urlencode(params)


def robokassa_verify(inv_id: str, out_sum: str, signature_value: str, email: str = "", requests: str = "") -> bool:
    pwd2 = ROBOKASSA_TEST_PASSWORD2 if ROBOKASSA_TEST and ROBOKASSA_TEST_PASSWORD2 else ROBOKASSA_PASSWORD2
    if not pwd2:
        return False
    crc_str = f"{ROBOKASSA_SHOP_ID}:{out_sum}:{inv_id}:{pwd2}"
    shp_parts = []
    if email:
        shp_parts.append(f"Shp_Email={email}")
    if requests:
        shp_parts.append(f"Shp_Requests={requests}")
    shp_parts.sort()
    if shp_parts:
        crc_str += ":" + ":".join(shp_parts)
    expected = hashlib.md5(crc_str.encode()).hexdigest()
    return signature_value.lower() == expected.lower()
