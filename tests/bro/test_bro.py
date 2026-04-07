from breinbaas_slim.bro.bro import BROAPI


class TestBRO:
    def setup_method(self):
        self.bro_api = BROAPI()

    def test_cpt_metadata_by_polyline(self):
        cpt_characteristics = self.bro_api.get_cpt_metadata_by_polyline(
            points=[(118471, 469367), (118800, 469281)], offset=10
        )
        assert len(cpt_characteristics) > 0
