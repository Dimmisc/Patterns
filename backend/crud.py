from fastapi import HTTPException, status
from sqlalchemy import select  
from sqlalchemy.orm import selectinload 
from db import User
from auth import hash_password

def get_user_by_id(session, id) -> User:
    result = session.query(User).options(
        # selectinload()
    ).filter(User.id==id).one()
    if not result   :
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return result   
    
def get_user_by_email(session, email):
    result = session.query(User).options(
        # selectinload()
    ).filter(User.email==email).one()
    if not result   :
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return result
    
def create_user(session, user_data):
    user = User(
        name=user_data.name,
        surname=user_data.surname,
        password=hash_password(user_data.password)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.expunge(user)
    return user

def add_token_to_blacklist(session, old_jti, old_exp):
    pass