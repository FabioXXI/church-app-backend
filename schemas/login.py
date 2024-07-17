from pydantic import BaseModel, ConfigDict

class LogginModel(BaseModel):
    id: str
    cpf: str
    password: str
    position: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "uuid4",
                "cpf": "cpf of the user",
                "password": "password of the user",
                "position": "position of the user"
            }
        }
    )