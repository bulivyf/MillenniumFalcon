import pytest
from millennium_falcon import MillenniumFalcon

@pytest.fixture
def setup_falcon():
    return MillenniumFalcon("data/millennium-falcon.json")

def test_calculate_odds_041(setup_falcon):
    falcon = setup_falcon
    odds = falcon.calculate_odds("data/empire041.json")
    assert odds == 0.0

def test_calculate_odds_042(setup_falcon):
    falcon = setup_falcon
    odds = falcon.calculate_odds("data/empire042.json")
    assert odds == 72.90

def test_calculate_odds_043(setup_falcon):
    falcon = setup_falcon
    odds = falcon.calculate_odds("data/empire043.json")
    assert odds == 90.00

def test_calculate_odds_044(setup_falcon):
    falcon = setup_falcon
    odds = falcon.calculate_odds("data/empire044.json")
    assert odds == 90.0
    