from fastapi import FastAPI


from .endpoints import router


app = FastAPI(
    title="Breinbaas Slim API",
    description="API for parsing CPT and Borehole data, and interpreting Soil Profiles.",
)


app.include_router(router, prefix="/api")
