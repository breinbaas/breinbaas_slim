from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import router


app = FastAPI(
    title="Breinbaas Slim API",
    description="API for parsing CPT and Borehole data, and interpreting Soil Profiles.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://breinbaas.nl",
        "https://api.breinbaas.nl",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
