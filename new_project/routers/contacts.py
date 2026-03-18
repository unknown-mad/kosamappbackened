from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/contacts", tags=["Contacts"])

@router.post("/", response_model=schemas.ContactResponse)
def create(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    return crud.create_contact(db, contact)

@router.get("/", response_model=list[schemas.ContactResponse])
def read_all(db: Session = Depends(get_db)):
    return crud.get_contacts(db)

@router.get("/{contact_id}", response_model=schemas.ContactResponse)
def read_one(contact_id: int, db: Session = Depends(get_db)):
    contact = crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.delete("/{contact_id}")
def delete(contact_id: int, db: Session = Depends(get_db)):
    return crud.delete_contact(db, contact_id)