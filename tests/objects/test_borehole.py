from breinbaas_slim.objects.borehole import Borehole


class TestBorehole:
    def test_from_bro_id(self):
        borehole = Borehole.from_bro_id("BHR000000354228")
        assert borehole.name == "BHR000000354228"
        assert len(borehole.soil_profile.soil_layers) == 3

    def test_from_xml(self):
        borehole = Borehole.from_xml("tests/testdata/boreholes/BHR000000354228.xml")
        assert borehole.name == "BHR000000354228"
        assert len(borehole.soil_profile.soil_layers) == 3

    def test_from_gef(self):
        borehole = Borehole.from_gef("tests/testdata/boreholes/B33F1451.gef")
        assert borehole.name == "B33F1451"
        assert len(borehole.soil_profile.soil_layers) == 7
