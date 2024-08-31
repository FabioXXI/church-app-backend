from dataclasses import dataclass
from models.dizimo_payment import DizimoPayment
from models.user import User
from dotenv import load_dotenv
from os import getenv
import requests
from typing import NoReturn

load_dotenv()

PIX_COB_URL = getenv("PIX_COB_URL")
header = {"Authorization": getenv("APP_ID"), "type": "application/json"}
PAID = "COMPLETED"
ACTIVE = "ACTIVE"
EXPIRED = "EXPIRED"

@dataclass
class PixPayment:
    value: int
    customer: dict
    correlationID: str
    expiresIn: int = (30 * 60)
    type: str = "DYNAMIC"

    def __dict__(self) -> dict:
        return {
            "value": self.value,
            "customer": self.customer,
            "expireIn": self.expiresIn,
            "type": self.type,
            "correlationID": self.correlationID
        }

def create_customer(user: User) -> dict:
    return {
        "name": user.name,
        "cpf": user.cpf,
        "phone": user.phone
    }

def make_post_pix_request(pix: PixPayment) -> dict:
    result = requests.post(url=PIX_COB_URL, headers=header, json=pix.__dict__())
    return result.json()

def get_pix_no_sensitive_data(pix: dict) -> dict:
    return {
        "value": pix['charge']['value'],
        "status": pix['charge']['status'],
        "expiresDate": pix['charge']['expiresDate'],
        "expiresIn": pix['charge']['expiresIn'],
        "createdAt": pix['charge']['createdAt'],
        "brCode": pix['charge']['brCode'],
        "qrCodeImage": pix['charge']['qrCodeImage']
    }

def get_pix_payment_from_correlation_id(correlation_id: str) -> dict:
    URL = PIX_COB_URL + "/" + correlation_id
    return requests.get(URL, headers=header).json()

def delete_pix_by_correlation_id(correlation_id: str) -> NoReturn:
    URL = PIX_COB_URL + "/" + correlation_id
    return requests.delete(URL, headers=header)

def is_pix_active(pix: dict) -> bool:
    return pix['charge']['status'] == ACTIVE

def is_pix_expired(pix: dict) -> bool:
    return pix['charge']['status'] == EXPIRED

def is_pix_paid(pix: dict) -> bool:
    return pix['charge']['status'] == PAID

def get_pix_value(pix: dict) -> int:
    return pix['charge']['value']