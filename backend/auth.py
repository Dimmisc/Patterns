from fastapi import Depends, HTTPException, status, Body
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession

import jwt, uuid, bcrypt
from datetime import datetime, timedelta

from schemas import RegisterRequest, LoginRequest, TokenResponse, ErrorResponse, ValidationError
from enums import UserRole
from session import get_session
from crud import get_user_by_id, get_user_by_email, create_user, add_token_to_blacklist, get_tocken_by_jti

# .env
jwt_secret_key='dev-secret-key'
jwt_algorithm='HS256'
access_ttl_minutes=30
refresh_ttl_days=30


# base
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", refreshUrl="/auth/refresh_token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
    ):

    payload = decode_token(token)

    if payload["type"] != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail=f"Wrong token type. Expected 'access', got '{payload['type']}'")

    return get_user_by_id(session, int(payload["sub"]))


def require_roles(*allowed_roles: UserRole):
    async def dep(user=Depends(get_current_user)):
        role = UserRole(user.role)

        if bool(user.banned) == True:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are banned!"
                )

        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden"
            )

        return user
    return dep



# jwt
def create_access_token(user_id: int, role: str):
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=access_ttl_minutes)
    }
    return jwt.encode(payload, jwt_secret_key, algorithm=jwt_algorithm)


def create_refresh_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": datetime.utcnow() + timedelta(days=refresh_ttl_days)
    }
    return jwt.encode(payload, jwt_secret_key, algorithm=jwt_algorithm)


def decode_token(token: str):
    try:
        return jwt.decode(token, jwt_secret_key, algorithms=[jwt_algorithm])
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )


# hashing
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode()) 


# endpoints
auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post("/register", summary="Регистрация нового пользователя", description="Регистрация нового ученика в системе",
                response_model=TokenResponse, 
                responses={
                    200: {'model': TokenResponse,'description': 'Пользователь успешно зарегистрирован'},
                    400: {'model': ErrorResponse, 'description': 'Некорректный запрос'},
                    409: {'model': ErrorResponse, 'description': 'Пользователь уже существует'},
                    422: {'model': ValidationError, 'description': 'Ошибка валидации'},
                })
async def register_user(
                    form: RegisterRequest,
                    session: AsyncSession = Depends(get_session) 
                ):
    try:
        user = get_user_by_email(session, form.email)
        # user already exists
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists") 
        
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            # user not found, proceed to create
            user = create_user(session, form)
            return TokenResponse(
                access_token=create_access_token(user.id, user.role),
                refresh_token=create_refresh_token(user.id),
                token_type='bearer'
            )
        else:
            raise e


@auth_router.post("/login", summary="Авторизация пользователя", description="Вход в систему с получением JWT токена",
                response_model=TokenResponse, 
                responses={
                    200: {'model': TokenResponse,'description': 'Успешная авторизация'},
                    400: {'model': ErrorResponse, 'description': 'Некорректный запрос'},
                    401: {'model': ErrorResponse, 'description': 'Не авторизован'},
                    422: {'model': ValidationError, 'description': 'Ошибка валидации'},
                })
async def login_user(
                    form: LoginRequest,
                    session: AsyncSession = Depends(get_session)
                ):
    
    try:
        user = await get_user_by_email(session, form.email)
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid email or password" 
            )
        raise e 

    if not verify_password(form.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
        token_type='bearer'
    )    


@auth_router.post("/refresh_token", summary="Обновление access токена", description="Получение нового access токена по refresh токену",
                response_model=TokenResponse, 
                responses={
                    200: {'model': TokenResponse,'description': 'Успешная авторизация'},
                    400: {'model': ErrorResponse, 'description': 'Некорректный запрос'},
                    401: {'model': ErrorResponse, 'description': 'Не авторизован'},
                    422: {'model': ValidationError, 'description': 'Ошибка валидации'},
                })
async def refresh_token(
                    refresh_token: str = Body(embed=True),
                    session: AsyncSession = Depends(get_session)
                ):

    payload = decode_token(refresh_token)

    if payload["type"] != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Wrong token type. Expected 'refresh', got '{payload['type']}'"
        )

    try:
        await get_tocken_by_jti(session, payload["jti"])
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    except HTTPException as e:
        if e.status_code != status.HTTP_404_NOT_FOUND:
            raise e

    user = get_user_by_id(session, int(payload["sub"]))

    old_jti = payload["jti"]
    old_exp = datetime.fromtimestamp(payload["exp"])
    add_token_to_blacklist(session, old_jti, old_exp)

    new_refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=new_refresh_token,
        token_type='bearer'
    )


@auth_router.post("/logout", summary="Выход из системы", description="",
                responses={
                    200: {'description': 'Успешный выход'},
                    400: {'model': ErrorResponse, 'description': 'Пользователь уже вышел'},
                    401: {'model': ErrorResponse, 'description': 'Не авторизован или неверный токен'},
                })
async def logout_user(
                    refresh_token: str = Body(embed=True), 
                    session: AsyncSession = Depends(get_session)
                ):

    payload = decode_token(refresh_token)
    if payload.get('type') != 'refresh':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Неверный тип токена'
        )
    jti = payload.get('jti')
    ex = datetime.fromtimestamp(payload.get('exp'))

    #Frontend needs to delete access token to logout
    await add_token_to_blacklist(session, jti, ex)

    return {'status': 'success'}