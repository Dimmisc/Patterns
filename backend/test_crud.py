import pytest
from unittest.mock import Mock, patch, call
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException, status
from datetime import datetime, timezone


from db import User, BlacklistedToken
from auth import hash_password
from enums import UserRole

from crud import (
    get_user_by_id, 
    get_user_by_email, 
    create_user, 
    add_token_to_blacklist
)

@pytest.fixture
def mock_session():
    session = Mock(spec=Session)
    session.query = Mock()
    return session

@pytest.fixture
def user_data_fixture():
    user_data = Mock()
    user_data.name = 'Ваня'
    user_data.surname = "Иванов"
    user_data.patronumic = "Иванович"
    user_data.email = "vana@mail.ru"
    user_data.password = "password123"
    user_data.role = UserRole.USER
    return user_data

@pytest.fixture
def sample_user():
    user = Mock(spec=User)
    user.id = 1
    user.name = "Иван"
    user.surname = "Иванов"
    user.patronymic = "Иванович"
    user.email = "ivan@example.com"
    user.password = "hashed_password"
    user.registered_at = datetime.now(timezone.utc)
    user.role = UserRole.USER
    user.banned = False
    return user

@pytest.fixture
def create_test_user(test_session, sample_user_data):
    user = User(**sample_user_data)
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user

def test_get_user_by_id_sucs(test_session: Session, create):
    pass
    