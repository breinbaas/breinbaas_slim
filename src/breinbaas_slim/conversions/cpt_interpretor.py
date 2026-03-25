import math
from enum import IntEnum
from typing import List
import numpy as np

from ..objects.cpt import Cpt
from ..objects.soil_profile import SoilProfile
from ..objects.soil_layer import SoilLayer
from ..constants import (
    DEFAULT_CPT_INTERPRETATION_MIN_LAYERHEIGHT,
    DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO,
    NEN5140,
    QCMAX_PEAT,
)


class CptInterpretationMethod(IntEnum):
    """Defines the interpretation methods that are available"""

    THREE_TYPE_RULE = 0
    NL_RF = 1
    ROBERTSON = 2


class CptInterpretor:
    def __init__(self, cpt: Cpt):
        self.cpt = cpt

    def to_soil_profile(
        self,
        method: CptInterpretationMethod = CptInterpretationMethod.ROBERTSON,
        minimum_layerheight: float = DEFAULT_CPT_INTERPRETATION_MIN_LAYERHEIGHT,
        peat_friction_ratio: float = DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO,
    ) -> SoilProfile:
        soil_layers = []

        # add preexcavated layer if necessary
        if self.cpt.pre_excavated_depth > 0:
            soil_layers.append(
                SoilLayer(
                    top=self.cpt.top,
                    bottom=self.cpt.top - self.cpt.pre_excavated_depth,
                    soil_code="preexcavated",
                )
            )

        # get the cpt data based on the minimum layerheight
        cptdata = self.cpt.filter(
            self.cpt.top - self.cpt.pre_excavated_depth, minimum_layerheight
        )

        # convert the cpt data based on the method
        if method == CptInterpretationMethod.THREE_TYPE_RULE:
            soil_layers = self._three_type_rule(
                soil_layers, cptdata, peat_friction_ratio
            )
        elif method == CptInterpretationMethod.NL_RF:
            soil_layers = self._nl_rf(soil_layers, cptdata, peat_friction_ratio)
        elif method == CptInterpretationMethod.ROBERTSON:
            soil_layers = self._robertson(soil_layers, cptdata, peat_friction_ratio)

        soil_profile = SoilProfile(x=self.cpt.x, y=self.cpt.y, soil_layers=soil_layers)
        soil_profile.merge()
        return soil_profile

    def _three_type_rule(
        self,
        soil_layers: List[SoilLayer],
        cptdata: np.array,
        peat_friction_ratio: float,
    ) -> List[SoilLayer]:
        for row in cptdata:
            qc = row[2]
            x = row[4]
            y = math.log(qc)

            if x < 0:
                x = 0
            if x > 10:
                x = 10
            if y < -1:
                y = -1
            if y > 2:
                y = 2

            soil_code = ""
            if y <= x * 0.4 - 2:
                if x < 4:
                    soil_code = "clay"
                else:
                    soil_code = "peat"
            elif y > x * 0.4 - 0.30103:
                soil_code = "sand"
            else:
                soil_code = "clay"

            # override if necessary
            if row[4] >= peat_friction_ratio and qc < QCMAX_PEAT:
                soil_code = "peat"

            soil_layers.append(
                SoilLayer(
                    top=round(row[0], 2), bottom=round(row[1], 2), soil_code=soil_code
                )
            )
        return soil_layers

    def _nl_rf(
        self,
        soil_layers: List[SoilLayer],
        cptdata: np.array,
        peat_friction_ratio: float,
    ) -> List[SoilLayer]:
        """
        Conversion function for the rule as found in CUR162 electric cone
        """
        for row in cptdata:
            qc = row[2]
            fr = row[4]

            if fr >= peat_friction_ratio and qc < QCMAX_PEAT:
                soil_layers.append(
                    SoilLayer(
                        top=round(row[0], 2),
                        bottom=round(row[1], 2),
                        soil_code="peat",
                    )
                )
            else:
                for soil_code, _fr in NEN5140:
                    if fr >= _fr:
                        soil_layers.append(
                            SoilLayer(
                                top=round(row[0], 2),
                                bottom=round(row[1], 2),
                                soil_code=soil_code,
                            )
                        )
                        break

        return soil_layers

    def _robertson(
        self,
        soil_layers: List[SoilLayer],
        cptdata: np.array,
        peat_friction_ratio: float,
    ) -> List[SoilLayer]:
        for row in cptdata:
            qc = row[2]
            fr = row[4]
            isbt = (3.47 - np.log10(qc * 1000 / 100)) ** 2 + (np.log10(fr + 1.22)) ** 2
            isbt = isbt**0.5

            if isbt > 3.6:
                soilcode = "organic_clay"
            elif isbt > 2.95:
                soilcode = "clay"
            elif isbt > 2.60:
                soilcode = "silty_clay"
            elif isbt > 2.05:
                soilcode = "silty_sand"
            elif isbt > 1.31:
                soilcode = "sand"
            else:
                soilcode = "dense_sand"

            if fr >= peat_friction_ratio and qc < QCMAX_PEAT:
                soilcode = "peat"

            soil_layers.append(
                SoilLayer(
                    top=round(row[0], 2), bottom=round(row[1], 2), soil_code=soilcode
                )
            )

        return soil_layers
