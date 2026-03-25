from pydantic import BaseModel


class SoilLayer(BaseModel):
    top: float
    bottom: float
    soil_code: str

    @property
    def height(self) -> float:
        """Get the height of the soillayer

        Returns:
            float: The height of the soillayer
        """
        return self.top - self.bottom
