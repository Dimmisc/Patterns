from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated, Optional, Any, List, Dict

# auth
class RegisterRequest(BaseModel):
    name: Annotated[str, Field(min_length=2)]
    surname: Annotated[str, Field(min_length=2)]
    email: str
    patronymic: Optional[str] = None
    password: Annotated[str, Field(min_length=6)]


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

# validation
class ErrorResponse(BaseModel):
    status_code: int
    detail: Any = None
    headers: dict[str, str] | None = None

    model_config = ConfigDict(from_attributes=True)

class ValidationError(BaseModel):
    detail: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)