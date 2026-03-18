from fastapi import FastAPI
from .database import engine, Base
from .routers import contacts

app = FastAPI(title="Kosa Contacts API")

Base.metadata.create_all(bind=engine)

app.include_router(contacts.router)

@app.get("/")
def root():
    return {"message": "FastAPI with PostgreSQL (kosa_uat schema) running"}