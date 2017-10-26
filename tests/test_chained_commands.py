import pytest
from parrotfish import *

def test_chained_commands(sessions):
    ParrotFishSession.nursery.production.set_category("Test")
    assert ParrotFishSession.category == "Test"
    assert ParrotFishSession.session_name == "production"
