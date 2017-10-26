import pytest
from parrotfish import *
from pathlib import *

CATEGORY = "ParrotFishTest"

def test_checkout(register, config):

    for session_name, session_config in config.items():
        pseudo_cli("checkout", session_name)
        assert Session.session_name == session_name

def test_reset(config):
    assert ParrotFishSession.state_pickle.exists()
    assert ParrotFishSession.master.exists()

    pseudo_cli("reset", force=True)

    assert Session.empty()
    assert Session.session is None
    assert not ParrotFishSession.state_pickle.exists()
    assert not list(list(ParrotFishSession.master.glob("*"))) == 0


def test_fetch(register):
    pseudo_cli("checkout", "nursery")
    pseudo_cli("set_category", CATEGORY)
    pseudo_cli("fetch")
    assert ParrotFishSession.catdir.is_dir()
    assert len(list(ParrotFishSession.catdir.iterdir())) > 1
    print(list(ParrotFishSession.catdir.iterdir()))

def test_set_remote(register, session_environments):
    # initialize session with protocols
    pseudo_cli("checkout", "nursery")
    pseudo_cli("set_category", CATEGORY)
    pseudo_cli("fetch")

    # save old_bin and old_files
    old_bin = ParrotFishSession.bin
    old_files = list(ParrotFishSession.bin.glob("*"))

    # copy bin to new location and update .session/state.pkl
    new_bin_parent = session_environments[1]
    new_bin_name = "temp_bin"
    pseudo_cli("set_remote", new_bin_parent, bin_name=new_bin_name)
    new_bin = ParrotFishSession.bin

    # check to make sure bin path is as expected
    assert ParrotFishSession.bin == new_bin

    # check to make sure files transferred
    old_files = [p.relative_to(old_bin) for p in old_files]
    new_files = [p.relative_to(ParrotFishSession.bin) for p in list(ParrotFishSession.bin.glob("*"))]
    assert old_files == new_files

    # return bin to defaults
    pseudo_cli("set_remote", old_bin)
    new_files = [p.relative_to(ParrotFishSession.bin) for p in list(ParrotFishSession.bin.glob("*"))]
    assert old_files == new_files
    assert ParrotFishSession.bin == old_bin

def test_pull():
    raise NotImplementedError()

def test_push():
    raise NotImplementedError()

