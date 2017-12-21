import os
import shutil
import uuid

from parrotfish import ParrotFish


def test_load(pfish):
    pfish.load()


def test_save(pfish):
    pfish.load()
    pfish.save()


def test_register(pfish):
    pfish.register("vrana", "Mountain5", "http://52.27.43.242:81/", "nursery")
    print(pfish.sessions())


def test_get_categories(pfish):
    pfish.register("vrana", "Mountain5", "http://52.27.43.242:81/", "nursery")
    pfish.set_session("nursery")
    cats = pfish.get_categories()
    print(cats)

def test_categories(pfish):
    pfish.register("vrana", "Mountain5", "http://52.27.43.242:81/", "nursery")
    pfish.set_session("nursery")
    cats = pfish.categories()
    print(cats)


def test_fetch(pfish):
    pfish.register("vrana", "Mountain5", "http://52.27.43.242:81/", "nursery")
    pfish.set_session("nursery")
    pfish.fetch("ParrotFishTest")

def test_ls(pfish):
    pass

def test_protocols(pfish):
    pfish.register("vrana", "Mountain5", "http://52.27.43.242:81/", "nursery")
    pfish.set_session("nursery")
    pfish.protocols()
#
# def test_fetch(sessions):
#     pfish.set_category("pfishTest")
#     pfish.fetch()
#     library = Environment().get_category("pfishTest").get("Library1.rb")
#     assert library.exists()
#
#
# def test_push(sessions):
#     pfish.set_category("pfishTest")
#
#     library = Environment().get_category("pfishTest").get("Library1.rb")
#     content = library.read('r')
#     tag = str(uuid.uuid4())
#     library.write('w', tag + '/n/n/n/n\n\n\n\n' + content)
#     new_content = library.read('r')
#     ss = library.abspath.stat().st_mtime
#     assert tag in library.read('r')
#     pfish.push()
#     pfish.fetch()
#     print(tag)
#     print()
#     print(library.read('r'))
#     assert tag in library.read('r')
#
# def test_push_after_load():
#     pfish.set_category("pfishTest")
#
#
# def test_mv(sessions, testing_environments):
#     env1, env2 = testing_environments
#     if env2.is_dir():
#         shutil.rmtree(env2)
#         os.mkdir(env2)
#     assert Environment().repo.dir.name == "env1"
#     pfish.move_repo(env2)
#     assert Environment().repo.dir.name == "env2"
#     assert Environment().get_category("pfishTest").get("Library1.rb").exists()
