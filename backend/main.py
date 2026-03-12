import uvicorn as uv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import auth_router
from endpoints import route
# from session import Base

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(route)

if __name__ == "__main__":
    uv.run("main:app", reload=True)
