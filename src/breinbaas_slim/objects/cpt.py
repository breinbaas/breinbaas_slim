from typing import List, Optional
from pydantic import BaseModel
import brodata
import numpy as np

from ..constants import (
    GEF_COLUMN_Z,
    GEF_COLUMN_QC,
    GEF_COLUMN_FS,
    GEF_COLUMN_U,
    GEF_COLUMN_Z_CORRECTED,
    CPT_FR_MAX,
)


class Cpt(BaseModel):
    name: str = ""
    x: Optional[float] = None
    y: Optional[float] = None

    z: Optional[List[float]] = None
    qc: Optional[List[float]] = None
    fs: Optional[List[float]] = None
    fr: Optional[List[float]] = None
    u2: Optional[List[float]] = None

    date: Optional[str] = None

    pre_excavated_depth: float = 0.0

    @classmethod
    def from_gef(cls, gef_file: str) -> "Cpt":
        def _parse_header_line(cpt: Cpt, line: str, metadata: dict) -> None:
            try:
                args = line.split("=")
                keyword, argline = args[0], args[1]
            except Exception as e:
                raise ValueError(f"Error reading headerline '{line}' -> error {e}")

            keyword = keyword.strip().replace("#", "")
            argline = argline.strip()
            args = argline.split(",")

            if keyword in ["PROCEDURECODE", "REPORTCODE"]:
                if args[0].upper().find("BORE") > -1:
                    raise ValueError("This is a borehole file instead of a Cpt file")
            elif keyword == "RECORDSEPARATOR":
                metadata["record_seperator"] = args[0]
            elif keyword == "COLUMNSEPARATOR":
                metadata["column_seperator"] = args[0]
            elif keyword == "COLUMNINFO":
                try:
                    column = int(args[0])
                    dtype = int(args[3].strip())
                    if dtype == GEF_COLUMN_Z_CORRECTED:
                        dtype = GEF_COLUMN_Z  # use corrected depth instead of depth
                    metadata["columninfo"][dtype] = column - 1
                except Exception as e:
                    raise ValueError(f"Error reading columninfo '{line}' -> error {e}")
            elif keyword == "XYID":
                try:
                    cpt.x = round(float(args[1].strip()), 2)
                    cpt.y = round(float(args[2].strip()), 2)
                except Exception as e:
                    raise ValueError(f"Error reading xyid '{line}' -> error {e}")
            elif keyword == "MEASUREMENTVAR":
                if args[0] == "13":
                    try:
                        cpt.pre_excavated_depth = float(args[1])
                    except Exception as e:
                        raise ValueError(
                            f"Invalid pre-excavated depth found in line '{line}'. Got error '{e}'"
                        )
            elif keyword == "COLUMNVOID":
                try:
                    col = int(args[0].strip())
                    metadata["columnvoids"][col - 1] = float(args[1].strip())
                except Exception as e:
                    raise ValueError(f"Error reading columnvoid '{line}' -> error {e}")
            elif keyword == "TESTID":
                cpt.name = args[0].strip()
            elif keyword == "FILEDATE":
                try:
                    yyyy = int(args[0].strip())
                    mm = int(args[1].strip())
                    dd = int(args[2].strip())

                    if (
                        yyyy < 1900
                        or yyyy > 2100
                        or mm < 1
                        or mm > 12
                        or dd < 1
                        or dd > 31
                    ):
                        raise ValueError(f"Invalid date {yyyy}-{mm}-{dd}")

                    cpt.date = f"{yyyy}{mm:02}{dd:02}"
                except:
                    cpt.date = ""
            elif keyword == "STARTDATE":
                try:
                    yyyy = int(args[0].strip())
                    mm = int(args[1].strip())
                    dd = int(args[2].strip())
                    cpt.date = f"{yyyy}{mm:02}{dd:02}"
                    if (
                        yyyy < 1900
                        or yyyy > 2100
                        or mm < 1
                        or mm > 12
                        or dd < 1
                        or dd > 31
                    ):
                        raise ValueError(f"Invalid date {yyyy}-{mm}-{dd}")
                except:
                    cpt.date = ""

        def _parse_data_line(cpt: Cpt, line: str, metadata: dict, top: float) -> None:
            try:
                if len(line.strip()) == 0:
                    return
                args = (
                    line.replace(metadata["record_seperator"], "")
                    .strip()
                    .split(metadata["column_seperator"])
                )
                args = [
                    float(arg.strip())
                    for arg in args
                    if len(arg.strip()) > 0
                    and arg.strip() != metadata["record_seperator"]
                ]

                # skip lines that have a columnvoid
                for col_index, voidvalue in metadata["columnvoids"].items():
                    if args[col_index] == voidvalue:
                        return

                zcolumn = metadata["columninfo"][GEF_COLUMN_Z]
                qccolumn = metadata["columninfo"][GEF_COLUMN_QC]
                fscolumn = metadata["columninfo"][GEF_COLUMN_FS]

                ucolumn = -1
                if GEF_COLUMN_U in metadata["columninfo"].keys():
                    ucolumn = metadata["columninfo"][GEF_COLUMN_U]

                dz = top - abs(args[zcolumn])
                cpt.z.append(dz)

                qc = args[qccolumn]
                if qc <= 0:
                    qc = 1e-3
                cpt.qc.append(qc)
                fs = args[fscolumn]
                if fs <= 0:
                    fs = 1e-6
                cpt.fs.append(fs)

                if ucolumn > -1:
                    cpt.u2.append(args[ucolumn])
                else:
                    cpt.u2.append(0.0)

            except Exception as e:
                raise ValueError(f"Error reading dataline '{line}' -> error {e}")

        cpt = Cpt()

        lines = open(gef_file, "r").readlines()

        reading_header = True
        metadata = {
            "record_seperator": "",
            "column_seperator": " ",
            "columnvoids": {},
            "columninfo": {},
        }
        for line in lines:
            if reading_header:
                if line.find("#ZID") < 0:
                    try:
                        top = float(args[1].strip())
                    except Exception as e:
                        raise ValueError(f"Error reading zid '{line}' -> error {e}")
                if line.find("#EOH") >= 0:
                    reading_header = False
                else:
                    _parse_header_line(cpt, line, metadata)
            else:
                _parse_data_line(cpt, line, metadata, top)

        # post processing
        cpt.fr = []

        for qc, fs in zip(cpt.qc, cpt.fs):
            if qc == 0.0:
                cpt.fr.append(CPT_FR_MAX)
            else:
                cpt.fr.append(fs / qc * 100.0)

        # remove nan lines
        zs, qcs, fss, frs, u2s = [], [], [], [], []
        for i, z in enumerate(cpt.z):
            qc = cpt.qc[i]
            fs = cpt.fs[i]
            fr = cpt.fr[i]
            u2 = cpt.u2[i]

            if np.isnan(z):
                continue
            if np.isnan(qc):
                qc = 0.0
            if np.isnan(fs):
                fs = 0.0
            if np.isnan(fr):
                fr = 0.0
            if np.isnan(u2):
                u2 = 0
            zs.append(z)
            qcs.append(qc)
            fss.append(fs)
            frs.append(fr)
            u2s.append(u2)

        cpt.z = zs
        cpt.qc = qcs
        cpt.fs = fss
        cpt.fr = frs
        cpt.u = u2s

        return cpt

    @classmethod
    def from_xml(cls, xml_file: str) -> "CPT":
        bro_cpt = brodata.cpt.ConePenetrationTest(xml_file)
        return cls.from_bro_cpt(bro_cpt)

    @classmethod
    def from_bro_id(cls, bro_id: str, to_path: Optional[str] = None) -> "CPT":
        """
        Create a CPT object from a BRO ID

        Args:
            bro_id (str): The BRO ID of the CPT
            to_path (Optional[str]): The path to save the XML file to

        Returns:
            CPT: The CPT object
        """
        if to_path:
            to_path = f"{to_path}/{bro_id}.xml"
            bro_cpt = brodata.cpt.ConePenetrationTest.from_bro_id(
                bro_id, to_file=to_path
            )
        else:
            bro_cpt = brodata.cpt.ConePenetrationTest.from_bro_id(bro_id)

        return cls.from_bro_cpt(bro_cpt)

    @classmethod
    def from_bro_cpt(cls, bro_cpt: brodata.cpt.ConePenetrationTest) -> "CPT":
        cpt = cls()
        cpt.name = bro_cpt.broId
        bro_cpt.conePenetrationTest.sort_index(inplace=True)
        cpt.x = bro_cpt.deliveredLocation.x
        cpt.y = bro_cpt.deliveredLocation.y
        dt = bro_cpt.conePenetrationTest_phenomenonTime
        cpt.date = dt.strftime("%Y-%m-%d")
        if bro_cpt.predrilledDepth:
            cpt.pre_excavated_depth = float(bro_cpt.predrilledDepth)

        # remove all rows where qc is NaN
        bro_cpt.conePenetrationTest.dropna(subset=["coneResistance"], inplace=True)

        if bro_cpt.parameters.depth == "ja":
            bro_cpt.conePenetrationTest.dropna(subset=["depth"], inplace=True)
            cpt.z = (float(bro_cpt.offset) - bro_cpt.conePenetrationTest.depth.values).tolist()
        else:
            cpt.z = (float(bro_cpt.offset) - bro_cpt.conePenetrationTest.index.to_numpy()).tolist()

        cpt.qc = bro_cpt.conePenetrationTest.coneResistance.fillna(0.0).values.tolist()
        cpt.fs = bro_cpt.conePenetrationTest.localFriction.fillna(0.0).values.tolist()
        cpt.fr = bro_cpt.conePenetrationTest.frictionRatio.fillna(0.0).values.tolist()
        if bro_cpt.parameters.porePressureU2 == "ja":
            cpt.u2 = bro_cpt.conePenetrationTest.porePressureU2.fillna(0.0).values.tolist()

        return cpt

    @property
    def has_u2(self) -> bool:
        return self.u2 is not None

    @property
    def top(self) -> float:
        return self.z[0]

    @property
    def bottom(self) -> float:
        return self.z[-1]

    def as_numpy(self) -> np.array:
        """
        Return the CPT data as a numpy array with;

        col     value
        0       z
        1       qc
        2       fs
        3       fr
        4       u2 (optional)

        Args:
            None

        Returns:
            np.array: the CPT data as a numpy array"""
        if self.has_u2:
            return np.transpose(
                np.array([self.z, self.qc, self.fs, self.fr, self.u2], dtype=float)
            )
        else:
            return np.transpose(
                np.array([self.z, self.qc, self.fs, self.fr], dtype=float)
            )

    def filter(
        self,
        top: float,
        minimum_layerheight: float,
    ) -> np.array:
        """Return the CPT data as a numpy array with;

        col     value
        0       ztop
        1       zbot
        2       qc
        3       fs
        4       fr
        5       u

        Args:
            top (float): the z value to start from
            minimum_layerheight (float): the minimal layerheight to use

        Returns:
            np.array: the CPT data as a numpy array"""
        a = self.as_numpy()

        ls = np.arange(
            top,
            self.z[-1] - minimum_layerheight,
            -minimum_layerheight,
        )

        result = []
        for i in range(1, len(ls)):
            ztop = ls[i - 1]
            zbot = ls[i]
            selection = a[(a[:, 0] <= ztop) & (a[:, 0] >= zbot)]
            layer = np.array([ztop, zbot])
            mean = np.mean(selection[:, 1:], axis=0)
            result.append(np.concatenate((layer, mean), axis=None))

        return np.array(result)
