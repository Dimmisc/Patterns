# tests/test_auth_crud.py
import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from crud import (
    get_user_by_id,
    get_user_by_email,
    create_user,
    add_token_to_blacklist
)
from schemas import RegisterRequest


@pytest.fixture
def sample_user_data() -> dict:
    return {
        "name": "Test",
        "surname": "User",
        "email": "test@example.com",
        "password": "password123"
    }


@pytest.fixture
def sample_register_request(sample_user_data) -> RegisterRequest:
    return RegisterRequest(**sample_user_data)


def test_get_user_by_id_success(test_session: Session, create_test_user):
    user = create_test_user
    result = get_user_by_id(test_session, user.id)
    
    assert result.id == user.id
    assert result.name == user.name
    assert result.email == user.email
    assert result.role == "user"


def test_get_user_by_email_success(test_session: Session, create_test_user):
    user = create_test_user
    result = get_user_by_email(test_session, user.email)
    
    assert result.id == user.id
    assert result.email == user.email


def test_get_user_by_email_not_found(test_session: Session):
    with pytest.raises(HTTPException) as exc_info:
        get_user_by_email(test_session, "nonexistent@example.com")
    
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "User not found"


def test_create_user_success(test_session: Session, sample_register_request):
    user = create_user(test_session, sample_register_request)
    
    assert user.id is not None
    assert user.name == sample_register_request.name
    assert user.surname == sample_register_request.surname
    assert user.email == sample_register_request.email
    assert user.role == "user"
    assert user.banned is False
    assert user.balance == 0
    assert isinstance(user.registered_at, datetime)
    
    # Проверяем, что пароль захэширован
    assert user.password != sample_register_request.password
    assert len(user.password) > 0


def test_create_user_with_patronymic(test_session: Session):
    data = RegisterRequest(
        name="Test",
        surname="User",
        email="test@mail.ru",
        patronymic="HEHEHE",
        password="password123"
    )
    
    user = create_user(test_session, data)
    
    assert user.patronymic == "HEHEHE"


def test_create_user_without_patronymic(test_session: Session):
    data = RegisterRequest(
        name="Test",
        surname="User",
        email="test@mail.ru",
        password="password123"
    )
    
    user = create_user(test_session, data)
    
    assert user.patronymic is None
