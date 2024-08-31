from fastapi import APIRouter, Depends, status
from controller.crud.dizimo_payment import DizimoPaymentCrud
from routers.middleware.authorization import verify_user_access_token
from controller.crud.user import UserCrud
from database.session import session
from uuid import uuid4
from controller.src.dizimo_payment import dizimo_payment_is_paid, complete_dizimo_payment, dizimo_payment_is_expired
from controller.errors.http.exceptions import bad_request, not_acceptable
from controller.src.pix_payment import (PixPayment, create_customer, make_post_pix_request,
                                        get_pix_no_sensitive_data, get_pix_payment_from_correlation_id,
                                        is_pix_active)
from schemas.dizimo_payment import CreateDizimoPaymentModel
from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from controller.jobs.dizimo_payment import update_payment_db
from datetime import datetime, timedelta

router = APIRouter()
dizimo_payment_crud = DizimoPaymentCrud()
user_crud = UserCrud()
scheduler = AsyncIOScheduler()

@router.post("/dizimo_payment", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_user_access_token)])
async def create_dizimo_payment_router(pix_data: CreateDizimoPaymentModel, user: dict = Depends(verify_user_access_token)):
    user = await user_crud.get_user_by_cpf(session, user['cpf'])
    pix_data = dict(pix_data)
    month = pix_data['month']
    year = pix_data['year']
    dizimo_payment = await dizimo_payment_crud.get_payment_by_month_year_and_user_id(session, month, year, user.id)
    TIME = datetime.now() + timedelta(minutes=30)
    if dizimo_payment_is_paid(dizimo_payment):
        raise bad_request(f"Payment already paid")
    if dizimo_payment_is_expired(dizimo_payment):
        raise not_acceptable(f"Payment is expired")
    if dizimo_payment.correlation_id:
        pix_payment = get_pix_payment_from_correlation_id(dizimo_payment.correlation_id)
        if is_pix_active(pix_payment):
            return get_pix_no_sensitive_data(pix_payment)
    pix_payment = PixPayment(
        value = pix_data['value'],
        customer = create_customer(user),
        correlationID = str(uuid4())
    )
    pix_payment = make_post_pix_request(pix_payment)
    dizimo_payment = complete_dizimo_payment(dizimo_payment, pix_payment)
    await dizimo_payment_crud.complete_dizimo_payment(session, dizimo_payment)
    scheduler.add_job(update_payment_db, DateTrigger(run_date=TIME), args=[dizimo_payment.correlation_id])
    return get_pix_no_sensitive_data(pix_payment)

@router.get("/dizimo_payment/{year}", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_user_access_token)])
async def get_dizimo_payment_by_year(year: int, user: dict = Depends(verify_user_access_token)):
    user = await user_crud.get_user_by_cpf(session, user['cpf'])
    dizimo_payments = await dizimo_payment_crud.get_payments_by_year_and_user_id(session, year, user.id)
    return [get_pix_no_sensitive_data(get_pix_payment_from_correlation_id(payment.correlation_id)) for payment in dizimo_payments]

@router.get("/dizimo_payment/{year}/{month}", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_user_access_token)])
async def get_dizimo_payment_by_year_and_month(year: int, month: str, user: dict = Depends(verify_user_access_token)):
    user = await user_crud.get_user_by_cpf(session, user['cpf'])
    dizimo_payment = await dizimo_payment_crud.get_payment_by_month_year_and_user_id(session, month, year, user.id)
    payment = get_pix_payment_from_correlation_id(dizimo_payment.correlation_id)
    return get_pix_no_sensitive_data(payment)