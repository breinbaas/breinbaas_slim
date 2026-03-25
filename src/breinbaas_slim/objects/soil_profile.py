from typing import List
from pydantic import BaseModel
from enum import Enum

from .soil_layer import SoilLayer


class GeoprofileLocation(Enum):
    CREST = "crest"
    TOE = "toe"


class SoilProfile(BaseModel):
    soil_layers: List[SoilLayer] = []
    c: float = 0.0
    x: float = 0.0
    y: float = 0.0
    location: GeoprofileLocation = GeoprofileLocation.CREST

    @property
    def top(self):
        return self.soil_layers[0].top

    @property
    def bottom(self):
        return self.soil_layers[-1].bottom

    def merge(self):
        """Merge the soillayers if two or more consecutive soillayers are of the same type"""
        result = []
        for i in range(len(self.soil_layers)):
            if i == 0:
                result.append(self.soil_layers[i])
            else:
                if self.soil_layers[i].soil_code == result[-1].soil_code:
                    result[-1].bottom = self.soil_layers[i].bottom
                else:
                    result.append(self.soil_layers[i])
        self.soil_layers = result
