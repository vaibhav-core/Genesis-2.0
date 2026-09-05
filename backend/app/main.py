from fastapi import FastAPI

from .database import Base, engine
from . import models
from .routers.pass_router import router as pass_router
from .routers.voting_router import router as voting_router
from .routers.admin_router import router as admin_router
from .routers.events_router import router as events_router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Freshers Backend")

app.include_router(pass_router)
app.include_router(voting_router)
app.include_router(admin_router)
app.include_router(events_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}