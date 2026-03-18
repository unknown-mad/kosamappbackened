from sqlalchemy import Column, Integer, String
from .database import Base

class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String)