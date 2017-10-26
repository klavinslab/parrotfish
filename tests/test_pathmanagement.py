from parrotfish import *
import pytest

def test_paths():

    ParrotFishSession.category = "Justin"
    print(ParrotFishSession.catdir)