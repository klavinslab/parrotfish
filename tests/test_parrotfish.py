from parrotfish import *
import pytest


def test_fetch(sessions):
    ParrotFish.set_category("ParrotFishTest")
    ParrotFish.fetch()

def test_push(sessions):
    ParrotFish.set_category("ParrotFishTest")
    ParrotFish.push()