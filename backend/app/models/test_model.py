from app.core.config.db import Base
from sqlalchemy import Column, Integer, String

class TestModel(Base):
    __tablename__ = "test_model"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
