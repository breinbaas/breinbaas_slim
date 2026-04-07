import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..bro.bro import CPTCharacteristics, BROAPI
from ..objects.cpt import Cpt
from ..objects.borehole import Borehole
from ..objects.soil_profile import SoilProfile
from ..conversions.cpt_interpretor import CptInterpretor, CptInterpretationMethod
from ..constants import (
    DEFAULT_CPT_INTERPRETATION_MIN_LAYERHEIGHT,
    DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO,
)
from .security import get_current_client

router = APIRouter()


class BROCptByPolyLineRequest(BaseModel):
    points: list[tuple[float, float]]
    offset: float = 10


class BROCptMetadataResponse(BaseModel):
    bro_id: str
    x: float
    y: float
    lat: float
    lon: float

    def to_dict(self):
        return {
            "bro_id": self.bro_id,
            "x": self.x,
            "y": self.y,
            "lat": self.lat,
            "lon": self.lon,
        }


@router.post("/bro/cpt_metadata/by_polyline")
async def cpt_metadata_by_polyline(
    request: BROCptByPolyLineRequest,
    client_name: str = Depends(get_current_client),
):
    """Get CPTs by bounds"""
    try:
        bro_api = BROAPI()
        cpt_characteristics = bro_api.get_cpt_metadata_by_polyline(
            points=request.points, offset=request.offset
        )

        cpt_metadata_response = []
        for cpt_characteristic in cpt_characteristics:
            cpt_metadata_response.append(
                BROCptMetadataResponse(
                    bro_id=cpt_characteristic.bro_id,
                    x=cpt_characteristic.delivered_location.x,
                    y=cpt_characteristic.delivered_location.y,
                    lat=cpt_characteristic.wgs84_coordinate.lat,
                    lon=cpt_characteristic.wgs84_coordinate.lon,
                ).to_dict()
            )

        return JSONResponse(content={"cpt_characteristics": cpt_metadata_response})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cpt/from_xml", response_model=Cpt)
async def cpt_from_xml(
    file: UploadFile = File(...), client_name: str = Depends(get_current_client)
):
    """Parse a CPT from an XML file"""
    if not file.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="File must be an XML")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cpt = Cpt.from_xml(tmp_path)
    except Exception as e:
        os.remove(tmp_path)
        raise HTTPException(status_code=400, detail=str(e))

    os.remove(tmp_path)
    return cpt


@router.get("/cpt/from_bro_id/{bro_id}", response_model=Cpt)
async def cpt_from_bro_id(bro_id: str, client_name: str = Depends(get_current_client)):
    """Parse a CPT from a BRO ID"""
    try:
        return Cpt.from_bro_id(bro_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/borehole/from_xml", response_model=Borehole)
async def borehole_from_xml(
    file: UploadFile = File(...), client_name: str = Depends(get_current_client)
):
    """Parse a Borehole from an XML file"""
    if not file.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="File must be an XML")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        borehole = Borehole.from_xml(tmp_path)
    except Exception as e:
        os.remove(tmp_path)
        raise HTTPException(status_code=400, detail=str(e))

    os.remove(tmp_path)
    return borehole


@router.get("/borehole/from_bro_id/{bro_id}", response_model=Borehole)
async def borehole_from_bro_id(
    bro_id: str, client_name: str = Depends(get_current_client)
):
    """Parse a Borehole from a BRO ID"""
    try:
        return Borehole.from_bro_id(bro_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CptInterpretationRequest(BaseModel):
    cpt: Cpt
    method: CptInterpretationMethod = CptInterpretationMethod.ROBERTSON
    minimum_layerheight: float = DEFAULT_CPT_INTERPRETATION_MIN_LAYERHEIGHT
    peat_friction_ratio: float = DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO


@router.post("/cpt_interpretor/to_soil_profile", response_model=SoilProfile)
async def interpret_cpt(
    request: CptInterpretationRequest, client_name: str = Depends(get_current_client)
):
    """Interpret a CPT to a Soil Profile"""
    try:
        interpretor = CptInterpretor(request.cpt)
        profile = interpretor.to_soil_profile(
            method=request.method,
            minimum_layerheight=request.minimum_layerheight,
            peat_friction_ratio=request.peat_friction_ratio,
        )
        return profile
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
