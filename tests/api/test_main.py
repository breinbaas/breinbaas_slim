import pytest
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from breinbaas_slim.api.main import app
from breinbaas_slim.objects.cpt import Cpt
from breinbaas_slim.conversions.cpt_interpretor import CptInterpretationMethod

client = TestClient(app)


class TestAPI:

    def test_cpt_metadata_by_polyline(self):
        response = client.post(
            "/api/bro/cpt_metadata/by_polyline",
            json={
                "points": [
                    (118471, 469367),
                    (118800, 469281),
                ],
                "offset": 10,
            },
            headers={"X-API-Key": "key_frontend_987654321"},
        )
        assert response.status_code == 200
        assert len(response.json()["cpt_characteristics"]) > 0

    def test_cpt_from_xml(self):
        with open("tests/testdata/cpts/CPT000000074504.xml", "rb") as f:
            response = client.post(
                "/api/cpt/from_xml",
                files={"file": ("CPT000000074504.xml", f, "text/xml")},
                headers={"X-API-Key": "key_frontend_987654321"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "CPT000000074504"

    def test_cpt_from_bro_id(self):
        response = client.get(
            "/api/cpt/from_bro_id/CPT000000074504",
            headers={"X-API-Key": "key_frontend_987654321"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "CPT000000074504"

    def test_borehole_from_xml(self):
        with open("tests/testdata/boreholes/BHR000000354228.xml", "rb") as f:
            response = client.post(
                "/api/borehole/from_xml",
                files={"file": ("BHR000000354228.xml", f, "text/xml")},
                headers={"X-API-Key": "key_frontend_987654321"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "BHR000000354228"

    def test_borehole_from_bro_id(self):
        response = client.get(
            "/api/borehole/from_bro_id/BHR000000354228",
            headers={"X-API-Key": "key_frontend_987654321"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "BHR000000354228"

    def test_cpt_interpretor_to_soil_profile(self):
        cpt = Cpt.from_xml("tests/testdata/cpts/CPT000000074504.xml")

        response = client.post(
            "/api/cpt_interpretor/to_soil_profile",
            json={
                "cpt": cpt.model_dump(),
                "method": CptInterpretationMethod.ROBERTSON.value,
                "minimum_layerheight": 0.1,
                "peat_friction_ratio": 6.0,
            },
            headers={"X-API-Key": "key_frontend_987654321"},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify it returns a SoilProfile properly
        assert "soil_layers" in data
        assert len(data["soil_layers"]) > 0
        assert data["soil_layers"][0]["soil_code"] is not None
