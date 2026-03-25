from breinbaas_slim.objects.cpt import Cpt
from breinbaas_slim.conversions.cpt_interpretor import (
    CptInterpretor,
    CptInterpretationMethod,
)


class TestCptInterpretor:
    def setup_method(self):
        self.cpt = Cpt.from_xml("tests/testdata/cpts/CPT000000074504.xml")
        self.cpt_interpretor = CptInterpretor(self.cpt)

    def test_cpt_interpretor_three_type_rule(self):
        soil_profile = self.cpt_interpretor.to_soil_profile(
            CptInterpretationMethod.THREE_TYPE_RULE
        )
        assert soil_profile.soil_layers[0].soil_code == "sand"

    def test_cpt_interpretor_nl_rf(self):
        soil_profile = self.cpt_interpretor.to_soil_profile(
            CptInterpretationMethod.NL_RF
        )
        assert soil_profile.soil_layers[0].soil_code == "nl_grof_zand"

    def test_cpt_interpretor_robertson(self):
        soil_profile = self.cpt_interpretor.to_soil_profile(
            CptInterpretationMethod.ROBERTSON
        )
        assert soil_profile.soil_layers[0].soil_code == "dense_sand"
