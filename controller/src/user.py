from models.user import User
from models.payment import Payment
from uuid import uuid4
from datetime import datetime
from controller.crud.community import CommunityCrud
from database.session import session
from models.login import Login
from controller.src.login import upgrade_login_position
from typing import NamedTuple
from controller.validators.date import DateValidator
from controller.validators.cpf import CPFValidator
from controller.validators.name import NameValidator
from controller.validators.email import EmailValidator
from controller.validators.password import PasswordValidator
from controller.crud.login import LoginCrud
from controller.auth.password import hash_pasword

community_crud = CommunityCrud()
login_crud = LoginCrud()

async def get_community_id(community_patron: str) -> str:
    community = await community_crud.get_community_by_patron(session, community_patron)
    return community.id

async def create_user(user_data: dict) -> User:
    user = User()
    for key in user_data.keys():
        match key:
            case "name":
                user.name = user_data['name']
            case "cpf":
                user.cpf = user_data['cpf']
            case "position":
                user.position = user_data['position']
            case "birthday":
                user.birthday = datetime.strptime(user_data['birthday'], "%Y-%m-%d")
            case "email":
                user.email = user_data['email']
            case "image":
                user.image = user_data['image']
            case "community":
                user_data['community'] = await get_community_id(user_data['community'])
                user.community_id = user_data['community']
    user.id = str(uuid4())
    return user

async def get_community_patron(community_id: str) -> str:
    community = await community_crud.get_community_by_id(session, community_id)
    return community.patron

async def get_user_client_data(user: User) -> dict:
    user_data = {}
    user_data['name'] = user.name
    user_data['birthday'] = user.birthday
    user_data['position'] = user.position
    user_data['image'] = user.image
    user_data['community'] = await get_community_patron(user.community_id)
    user_data['email'] = user.email
    user_data['cpf'] = user.cpf

    return user_data

async def is_council_member(position: str) -> bool:
    return position == "council member"

async def is_parish_leader(position: str) -> bool:
    return position == "parish leader"

def convert_user_to_dict(user: User) -> dict:
    new_user = {'id': user.id, 'name': user.name, 'image': user.image, 'position': user.position,
                'community_id': user.community_id, 'birthday': user.birthday, 'cpf': user.cpf, 'email': user.email,
                'active': user.active}
    return new_user

def upgrade_user_position(user: User, login: Login, position: str):
    class Data(NamedTuple):
        user: dict
        login: dict

    user = convert_user_to_dict(user)
    user['position'] = position
    login = upgrade_login_position(login, position)

    return Data(user=user, login=login)

async def get_update_data(user: User, update_data: dict) -> dict:
    if update_data.get('email'):
        EmailValidator(update_data['email'])
        user.email = update_data['email']
    if update_data.get('name'):
        NameValidator(update_data['name'])
        user.name = update_data['name']
    if update_data.get('image'):
        user.image = update_data['image'].encode('utf-8')
    if update_data.get('birthday'):
        DateValidator(update_data['birthday'])
        user.birthday = datetime.strptime(update_data['birthday'], "%Y-%m-%d")
    if update_data.get('community_patron'):
        community = await community_crud.get_community_by_patron(session, update_data['community_patron'])
        user.community_id = community.id
    if update_data.get('password'):
        PasswordValidator(update_data['password'])
        login = await login_crud.get_login_by_cpf(session, user.cpf)
        login.password = hash_pasword(update_data['password'])
        login = {"id": login.id, "position": login.position, "password": login.password, "cpf": login.cpf}
        await login_crud.update_login(session, login)
    if update_data.get('cpf'):
        CPFValidator(update_data['cpf'])
        user.cpf = update_data['cpf']
    return convert_user_to_dict(user)