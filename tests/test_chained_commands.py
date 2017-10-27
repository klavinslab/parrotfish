import pytest
from parrotfish import *

def test_chained_commands(sessions):
    s = Session
    ParrotFish.nursery.production.set_category("Test")
    assert ParrotFish.category == "Test"
    assert ParrotFish.session_name == "production"

def test_get_categories(sessions):
    cats = CodeManager().get_categories()
    assert len(cats) > 1

