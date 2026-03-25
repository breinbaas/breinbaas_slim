from breinbaas_slim.objects.cpt import Cpt


class TestCpt:
    def test_from_bro_id(self):
        cpt = Cpt.from_bro_id("CPT000000005925")
        assert cpt.name == "CPT000000005925"
        assert len(cpt.z) == 179

    def test_from_xml(self):
        cpt = Cpt.from_xml("tests/testdata/cpts/CPT000000074504.xml")
        assert cpt.name == "CPT000000074504"
        assert len(cpt.z) == 773
