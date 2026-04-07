from typing import List, Tuple
from pyproj import CRS
from pydantic import BaseModel
from pyproj.transformer import Transformer
import requests
import xmltodict
from shapely.geometry import Point as SHPPoint, LineString

BRO_CPT_CHARACTERISTICS_URL = (
    "https://publiek.broservices.nl/sr/cpt/v1/characteristics/searches"
)


def _str2bool(s) -> bool:
    """
    converts a value to bool based on certain
    :param s: int, str, float
    :return: bool
    """
    return str(s).lower() in ("ja", "yes", "true", "t", "1")


class Point(BaseModel):
    lat: float
    lon: float

    def from_wgs84_to_rd(self) -> "RDPoint":
        transformer = Transformer.from_crs(4326, 28992)
        rd_x, rd_y = transformer.transform(self.lat, self.lon)
        return RDPoint(x=rd_x, y=rd_y)


class RDPoint(BaseModel):
    x: float
    y: float

    def from_rd_to_wgs84(self) -> "Point":
        transformer = Transformer.from_crs(28992, 4326)
        lat, lon = transformer.transform(self.x, self.y)
        return Point(lat=lat, lon=lon)


class Envelope(BaseModel):
    lower_corner: Point
    upper_corner: Point

    @property
    def bro_json(self):
        return {
            "boundingBox": {
                "lowerCorner": {
                    "lat": self.lower_corner.lat,
                    "lon": self.lower_corner.lon,
                },
                "upperCorner": {
                    "lat": self.upper_corner.lat,
                    "lon": self.upper_corner.lon,
                },
            }
        }


def xy_to_latlon(x: float, y: float, epsg: int = 28992) -> Tuple[float, float]:
    """Convert coordinates from the given epsg to latitude longitude coordinate

    Arguments:
        x (float): x coordinate
        y (float): y coordinate
        epsg (int): EPSG according to https://epsg.io/, defaults to 28992 (Rijksdriehoek coordinaten)

    Returns:
         Tuple[float, float]: latitude, longitude rounded to 6 decimals
    """
    if epsg == 4326:
        return x, y

    try:
        transformer = Transformer.from_crs(epsg, 4326)
        lat, lon = transformer.transform(x, y)
    except Exception as e:
        raise e

    return (round(lat, 7), round(lon, 7))


class CPTCharacteristics:
    """
    Class to save all Characteristics of a CPT object, resulting from a characteristics search on the API
    """

    def __init__(self, parsed_dispatch_document: dict):
        self.gml_id: str = parsed_dispatch_document["gml:id"]
        self.bro_id: str = parsed_dispatch_document["brocom:broId"]
        self.deregistered: bool = _str2bool(
            parsed_dispatch_document["brocom:deregistered"]
        )
        self.accountable_party: int = parsed_dispatch_document[
            "brocom:deliveryAccountableParty"
        ]
        self.quality_regime: str = parsed_dispatch_document["brocom:qualityRegime"]
        self.object_registration_time: str = parsed_dispatch_document[
            "brocom:objectRegistrationTime"
        ]
        self.under_review: bool = _str2bool(
            parsed_dispatch_document["brocom:underReview"]
        )
        xy = parsed_dispatch_document["brocom:standardizedLocation"]["gml:pos"].split(
            " "
        )
        self.standardized_location: Point = Point(lat=float(xy[0]), lon=float(xy[1]))
        # xy = parsed_dispatch_document["brocom:standardizedLocation"]["gml:pos"].split(
        #     " "
        # )
        rd_point = self.standardized_location.from_wgs84_to_rd()
        self.delivered_location: RDPoint = rd_point
        self.local_vertical_reference_point: Optional[str] = (
            parsed_dispatch_document["localVerticalReferencePoint"]["value"]
            if parsed_dispatch_document.get("localVerticalReferencePoint")
            else None
        )
        self.vertical_datum: Optional[str] = (
            parsed_dispatch_document["verticalDatum"]["value"]
            if parsed_dispatch_document.get("verticalDatum")
            else None
        )
        self.cpt_standard: Optional[str] = (
            parsed_dispatch_document["cptStandard"]["value"]
            if parsed_dispatch_document.get("cptStandard")
            else None
        )
        self.offset: Optional[float] = (
            float(parsed_dispatch_document["offset"]["value"])
            if parsed_dispatch_document.get("offset")
            else None
        )
        self.quality_class: Optional[str] = (
            parsed_dispatch_document["qualityClass"]["value"]
            if parsed_dispatch_document.get("qualityClass")
            else None
        )
        self.research_report_date: Optional[str] = (
            parsed_dispatch_document["researchReportDate"]["brocom:date"]
            if parsed_dispatch_document.get("researchReportDate")
            else None
        )
        self.start_time: Optional[str] = parsed_dispatch_document.get("startTime")
        self.predrilled_depth: Optional[float] = (
            float(parsed_dispatch_document["predrilledDepth"]["value"])
            if parsed_dispatch_document.get("predrilledDepth")
            else None
        )
        self.final_depth: Optional[float] = (
            float(parsed_dispatch_document["finalDepth"]["value"])
            if parsed_dispatch_document.get("finalDepth")
            else None
        )
        self.survey_purpose: Optional[str] = (
            parsed_dispatch_document["surveyPurpose"]["value"]
            if parsed_dispatch_document.get("surveyPurpose")
            else None
        )
        self.dissipation_test_performed: Optional[bool] = (
            _str2bool(parsed_dispatch_document["dissipationTestPerformed"])
            if parsed_dispatch_document.get("dissipationTestPerformed")
            else None
        )
        self.stop_criterion: Optional[str] = (
            parsed_dispatch_document["stopCriterion"]["value"]
            if parsed_dispatch_document.get("stopCriterion")
            else None
        )

    @property
    def rd_coordinate(self) -> RDPoint:
        return self.delivered_location

    @property
    def wgs84_coordinate(self) -> Point:
        return self.standardized_location


class BROAPI:
    def _get_cpt_metadata_by_bounds(
        self, left: float, top: float, right: float, bottom: float
    ):
        envelope = Envelope(
            lower_corner=Point(lat=left, lon=bottom),
            upper_corner=Point(lat=right, lon=top),
        )

        headers = {
            "accept": "application/xml",
            "Content-Type": "application/json",
        }

        json = {"area": envelope.bro_json}

        response = requests.post(
            BRO_CPT_CHARACTERISTICS_URL, headers=headers, json=json, timeout=10
        )

        available_cpt_objects = []

        if response.status_code == 200:
            parsed = xmltodict.parse(
                response.content, attr_prefix="", cdata_key="value"
            )
            rejection_reason = parsed["dispatchCharacteristicsResponse"].get(
                "brocom:rejectionReason"
            )
            if rejection_reason:
                raise ValueError(f"{rejection_reason}")

            nr_of_documents = int(
                parsed["dispatchCharacteristicsResponse"].get("numberOfDocuments")
            )
            if nr_of_documents is None or nr_of_documents == 0:
                raise ValueError(
                    "No available objects have been found in given date + area range. Retry with different parameters."
                )

            if nr_of_documents == 1:
                documents = [
                    parsed["dispatchCharacteristicsResponse"]["dispatchDocument"]
                ]
            else:
                documents = parsed["dispatchCharacteristicsResponse"][
                    "dispatchDocument"
                ]

            for document in documents:
                # TODO: Hard skip, this is likely to happen when it's deregistered. document will have key ["BRO_DO"]["brocom:deregistered"] = "ja"
                # TODO: Add this information to logger
                if "CPT_C" not in document.keys():
                    continue

                bro_id = f"{document['CPT_C']['brocom:broId']}"
                available_cpt_objects.append(CPTCharacteristics(document["CPT_C"]))

            return available_cpt_objects

        response.raise_for_status()

    def get_cpt_metadata_by_polyline(
        self, points: list[tuple[float, float]], offset: float = 0.0
    ):
        """
        Get CPT metadata from BRO API

        Args:
            points: List of (x, y) coordinates RD (CRS:28992)
            offset: Offset to apply to the bounding box

        Returns:
            List of CPT metadata
        """
        # create a rectangle out of the given points and offset
        min_x = min([p[0] for p in points]) - offset
        max_x = max([p[0] for p in points]) + offset
        min_y = min([p[1] for p in points]) - offset
        max_y = max([p[1] for p in points]) + offset

        lat1, lon1 = xy_to_latlon(min_x, min_y)
        lat2, lon2 = xy_to_latlon(max_x, max_y)

        cpt_characteristics = self._get_cpt_metadata_by_bounds(
            left=lat1, top=lon2, right=lat2, bottom=lon1
        )

        buffer = LineString(points).buffer(offset)

        result = []
        for cpt_md in cpt_characteristics:
            cpt_point = SHPPoint(
                cpt_md.delivered_location.x, cpt_md.delivered_location.y
            )
            if cpt_point.intersects(buffer):
                result.append(cpt_md)

        return result
