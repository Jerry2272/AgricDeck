from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as api_v1_router
from app.core.config.db import Base, engine
from app.models.test_model import TestModel

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgricDeck API", version="1.0.0")

# CORS setup
origins = [
    "http://localhost",
    "http://localhost:3000",  # React frontend
    "https://frontend-domain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_v1_router, prefix="/api/v1")
