import os
import uuid
from yookassa import Configuration, Payment

YOOKASSA_SHOP_ID = os.environ.get("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.environ.get("YOOKASSA_SECRET_KEY", "")

if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY:
    Configuration.account_id = YOOKASSA_SHOP_ID
    Configuration.secret_key = YOOKASSA_SECRET_KEY

PLANS = {
    "starter": {
        "name": "Стартовый",
        "price": 490,
        "currency": "RUB",
        "requests_limit": 100,
        "days": 30,
    },
    "pro": {
        "name": "Про",
        "price": 1490,
        "currency": "RUB",
        "requests_limit": 500,
        "days": 30,
    },
    "business": {
        "name": "Бизнес",
        "price": 4990,
        "currency": "RUB",
        "requests_limit": 9999,
        "days": 30,
    },
}


def create_payment(plan_id: str, email: str, return_url: str) -> dict:
    plan = PLANS.get(plan_id)
    if not plan:
        return {"error": "Неизвестный тариф"}

    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        return {"error": "YooKassa не настроена. Обратитесь к администратору."}

    idempotence_key = str(uuid.uuid4())

    payment = Payment.create({
        "amount": {
            "value": str(plan["price"]),
            "currency": plan["currency"],
        },
        "confirmation": {
            "type": "redirect",
            "return_url": return_url,
        },
        "capture": True,
        "description": f"AI-Automator: {plan['name']} ({plan['requests_limit']} запросов/день)",
        "metadata": {
            "email": email,
            "plan_id": plan_id,
        },
    }, idempotence_key)

    return {
        "payment_id": payment.id,
        "confirmation_url": payment.confirmation.confirmation_url,
        "amount": plan["price"],
        "plan_name": plan["name"],
    }


def check_payment(payment_id: str) -> dict:
    payment = Payment.find_one(payment_id)
    return {
        "status": payment.status,
        "paid": payment.paid,
    }


WEBHOOK_SECRET = os.environ.get("YOOKASSA_WEBHOOK_SECRET", "")
