from fastapi.routing import APIRouter
from fastapi import Depends

from auth import require_roles, UserRole


route = APIRouter(prefix='pref', tags=['tag'])

@route.get('/', response_model=...)
async def get_sth(user=Depends(require_roles(UserRole.USER, UserRole.ADMIN))):
    pass