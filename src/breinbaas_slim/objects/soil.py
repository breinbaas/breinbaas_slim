from pydantic import BaseModel


class Soil(BaseModel):
    code: str
    yd: float = 0.0
    ys: float = 0.0
    color: str
