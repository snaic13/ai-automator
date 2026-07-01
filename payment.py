import os
import hashlib
import urllib.parse

ROBOKASSA_SHOP_ID = os.environ.get("ROBOKASSA_SHOP_ID", "")
ROBOKASSA_PASSWORD1 = os.environ.get("ROBOKASSA_PASSWORD1", "")
ROBOKASSA_PASSWORD2 = os.environ.get("ROBOKASSA_PASSWORD2", "")
ROBOKASSA_TEST = os.environ.get("ROBOKASSA_TEST", "0") == "1"

PLANS = {
    "starter": {"name": "Стартовый", "price": 490, "currency": "RUB", "requests_limit": 100, "days": 30},
    "pro": {"name": "Про", "price": 1490, "currency": "RUB", "requests_limit": 500, "days": 30},
    "business": {"name": "Бизнес", "price": 4990, "currency": "RUB", "requests_limit": 9999, "days": 30},
}


def robokassa_init_url(inv_id: str, amount: float, description: str, email: str, success_url: str, fail_url: str) -> str:
    if not ROBOKASSA_SHOP_ID or not ROBOKASSA_PASSWORD1:
        return ""

    out_sum = f"{amount:.2f}"
    crc_str = f"{ROBOKASSA_SHOP_ID}:{out_sum}:{inv_id}:{ROBOKASSA_PASSWORD1}"
    if ROBOKASSA_TEST:
        crc_str += ":test"

    signature = hashlib.md5(crc_str.encode()).hexdigest()

    params = {
        "OutSum": out_sum,
        "InvId": inv_id,
        "Desc": description,
        "Email": email,
        "SignatureValue": signature,
        "Shp_Email": email,
        "Shp_plan": "",
    }
    if ROBOKASSA_TEST:
        params["IsTest"] = "1"

    return "https://auth.robokassa.ru/Merchant/Payment.aspx?" + urllib.parse.urlencode(params)


def robokassa_verify(inv_id: str, out_sum: str, signature_value: str) -> bool:
    if not ROBOKASSA_PASSWORD2:
        return False
    crc_str = f"{ROBOKASSA_SHOP_ID}:{out_sum}:{inv_id}:{ROBOKASSA_PASSWORD2}"
    expected = hashlib.md5(crc_str.encode()).hexdigest()
    return signature_value.lower() == expected.lower()
