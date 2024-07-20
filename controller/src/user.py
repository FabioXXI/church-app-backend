from models.user import User
from models.payment import Payment
from uuid import uuid4
from datetime import datetime
from controller.auth.cpf_hash import hash_cpf
from controller.crud.community import CommunityCrud
from database.session import session

community_crud = CommunityCrud()

async def get_community_id(community_name: str) -> str:
    community = await community_crud.get_community_by_name(session, community_name)
    return community.id

async def create_user(user_data: dict) -> User:
    user = User()
    for key in user_data.keys():
        match key:
            case "name":
                user.name = user_data['name']
            case "cpf":
                user.cpf = hash_cpf(user_data['cpf'])
            case "position":
                user.position = user_data['position']
            case "birthday":
                user.birthday = datetime.strptime(user_data['birthday'], "%Y/%m/%d")
            case "email":
                user.email = user_data['email']
            case "image":
                user.image = user_data['image']
            case "community":
                user_data['community'] = await get_community_id(user_data['community'])
                user.community_id = user_data['community']
    user.id = str(uuid4())
    return user