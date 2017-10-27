import pytest
from parrotfish import *
from pathlib import *

CATEGORY = "ParrotFishTest"

def test_checkout(register, config):

    for session_name, session_config in config.items():
        call_command("checkout", session_name)
        assert Session.session_name == session_name

def test_reset(config):
    assert Environment.env.exists()
    assert Environment.master_dir.exists()

    call_command("reset", force=True)

    assert Session.empty()
    assert Session.session is None
    assert not Environment.env.exists()
    assert not list(list(Environment.master_dir.glob("*"))) == 0


def test_fetch(register):
    call_command("checkout", "nursery")
    call_command("set_category", CATEGORY)
    call_command("fetch")
    assert ParrotFish.catdir.is_dir()
    assert len(list(ParrotFish.catdir.iterdir())) > 1

def test_set_remote(register, session_environments):
    # initialize session with protocols
    call_command("checkout", "nursery")
    call_command("set_category", CATEGORY)
    call_command("fetch")

    # save old_bin and old_files
    old_bin = Environment.root
    old_files = list(Environment.root.glob("*"))

    # copy bin to new location and update .session/state.pkl
    new_bin_parent = session_environments[1]
    new_bin_name = "temp_bin"
    call_command("set_remote", new_bin_parent, root_name=new_bin_name)
    new_bin = Environment.root

    # check to make sure bin path is as expected
    assert Environment.root == new_bin

    # check to make sure files transferred
    old_files = [p.relative_to(old_bin) for p in old_files]
    new_files = [p.relative_to(Environment.root) for p in list(Environment.root.glob("*"))]
    assert old_files == new_files

    # return bin to defaults
    call_command("set_remote", old_bin.parent)
    new_files = [p.relative_to(Environment.root) for p in list(Environment.root.glob("*"))]
    assert old_files == new_files
    assert Environment.root == old_bin

# def test_pull():
#     raise NotImplementedError()

def test_push_no_changes():
    call_command("push")

def test_push_changes():
    call_command("push")

