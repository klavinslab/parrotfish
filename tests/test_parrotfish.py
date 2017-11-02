from parrotfish import *
import pytest


def test_fetch(sessions):
    ParrotFish.set_category("ParrotFishTest")
    ParrotFish.fetch()
    library = Environment().get_category("ParrotFishTest").get("Library1.rb")
    assert library.exists()

def test_push(sessions):
    ParrotFish.set_category("ParrotFishTest")
    ParrotFish.push()

def test_mv(sessions, testing_environments):
    env1, env2 = testing_environments
    if env2.is_dir():
        shutil.rmtree(env2)
        os.mkdir(env2)
    assert Environment().repo.dir.name == "env1"
    ParrotFish.move_repo(env2)
    assert Environment().repo.dir.name == "env2"
    assert Environment().get_category("ParrotFishTest").get("Library1.rb").exists()