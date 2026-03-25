from typing import List, Optional
from pydantic import BaseModel
import brodata

from .soil_profile import SoilProfile
from .soil_layer import SoilLayer


class Borehole(BaseModel):
    name: str = ""
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    soil_profile: SoilProfile = SoilProfile()
    date: Optional[str] = None

    @classmethod
    def from_gef(cls, gef_file: str) -> "Borehole":
        borehole = cls()
        reading_header = True
        column_separator = ";"

        column_info = {}
        column_voids = {}
        max_col = 0

        with open(gef_file, "r") as f:
            lines = f.readlines()

        for line in lines:
            if line.startswith("#EOH"):
                reading_header = False
                continue

            if reading_header:
                keyword, line_args = line.split("=")
                keyword = keyword.strip()
                args = [a.strip() for a in line_args.split(",")]
                if keyword == "#COLUMNINFO":
                    col = int(args[-1])
                    column_info[args[0]] = col - 1
                    max_col = max(max_col, col)
                elif keyword == "#COLUMNSEPARATOR":
                    column_separator = args[0]
                elif keyword == "#COLUMNVOID":
                    column_voids[args[0]] = args[-1]
                elif keyword == "#XYID":
                    borehole.x = float(args[1])
                    borehole.y = float(args[2])
                    borehole.soil_profile.x = borehole.x
                    borehole.soil_profile.y = borehole.y
                elif keyword == "#TESTID":
                    borehole.name = args[0]
                elif keyword == "#ZID":
                    borehole.z = float(args[1])
            else:  # reading data
                args = [a.strip() for a in line.split(column_separator)]

                if borehole.z is None:
                    raise ValueError("No ZID found in gef file")

                top = borehole.z - float(args[column_info["1"]])
                bottom = borehole.z - float(args[column_info["2"]])
                soil_code = "_".join([a.replace("'", "") for a in args[max_col:]])

                sl = SoilLayer(top=top, bottom=bottom, soil_code=soil_code)
                if len(borehole.soil_profile.soil_layers) == 0:
                    borehole.soil_profile.soil_layers.append(sl)
                else:
                    if borehole.soil_profile.soil_layers[-1].soil_code == sl.soil_code:
                        borehole.soil_profile.soil_layers[-1].bottom = sl.bottom
                    else:
                        borehole.soil_profile.soil_layers.append(sl)

        return borehole

    @classmethod
    def from_xml(cls, xml_file: str) -> "Borehole":
        bro_borehole = brodata.bhr.GeotechnicalBoreholeResearch(xml_file)
        return cls.from_bro_borehole(bro_borehole)

    @classmethod
    def from_bro_id(cls, bro_id: str, to_path: Optional[str] = None) -> "Borehole":
        if to_path:
            to_path = f"{to_path}/{bro_id}.xml"
            bro_borehole = brodata.bhr.GeotechnicalBoreholeResearch.from_bro_id(
                bro_id, to_file=to_path
            )
        else:
            bro_borehole = brodata.bhr.GeotechnicalBoreholeResearch.from_bro_id(bro_id)

        return cls.from_bro_borehole(bro_borehole)

    @classmethod
    def from_bro_borehole(
        cls, bro_borehole: brodata.bhr.GeotechnicalBoreholeResearch
    ) -> "Borehole":
        borehole = cls()
        borehole.name = bro_borehole.broId
        borehole.x = bro_borehole.deliveredLocation.x
        borehole.y = bro_borehole.deliveredLocation.y

        dt = bro_borehole.boringStartDate
        borehole.date = dt.strftime("%Y-%m-%d")

        borehole.z = bro_borehole.offset

        layers = bro_borehole.descriptiveBoreholeLog[0]["layer"]

        for _, layer in layers.iterrows():
            top = borehole.z - layer.upperBoundary
            bottom = borehole.z - layer.lowerBoundary
            soil_code = layer.geotechnicalSoilName
            soil_layer = SoilLayer(top=top, bottom=bottom, soil_code=soil_code)
            borehole.soil_profile.soil_layers.append(soil_layer)

        borehole.soil_profile.merge()

        return borehole
