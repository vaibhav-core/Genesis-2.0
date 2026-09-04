from fastapi import FastAPI

from .database import Base, engine
from . import models
from .routers.pass_router import router as pass_router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Freshers Backend")

app.include_router(pass_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}