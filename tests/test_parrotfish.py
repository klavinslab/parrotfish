import os
import shutil
import uuid

from parrotfish import ParrotFish
from parrotfish.session_environment import SessionManager



def test_load():
    ParrotFish.load()


def test_save():
    ParrotFish.load()
    ParrotFish.save()


def test_register():
    ParrotFish.register("vrana", "Mountain5", "http://52.27.43.242:81/", "nursery")
    print(ParrotFish.sessions)
#
# def test_fetch(sessions):
#     ParrotFish.set_category("ParrotFishTest")
#     ParrotFish.fetch()
#     library = Environment().get_category("ParrotFishTest").get("Library1.rb")
#     assert library.exists()
#
#
# def test_push(sessions):
#     ParrotFish.set_category("ParrotFishTest")
#
#     library = Environment().get_category("ParrotFishTest").get("Library1.rb")
#     content = library.read('r')
#     tag = str(uuid.uuid4())
#     library.write('w', tag + '/n/n/n/n\n\n\n\n' + content)
#     new_content = library.read('r')
#     ss = library.abspath.stat().st_mtime
#     assert tag in library.read('r')
#     ParrotFish.push()
#     ParrotFish.fetch()
#     print(tag)
#     print()
#     print(library.read('r'))
#     assert tag in library.read('r')
#
# def test_push_after_load():
#     ParrotFish.set_category("ParrotFishTest")
#
#
# def test_mv(sessions, testing_environments):
#     env1, env2 = testing_environments
#     if env2.is_dir():
#         shutil.rmtree(env2)
#         os.mkdir(env2)
#     assert Environment().repo.dir.name == "env1"
#     ParrotFish.move_repo(env2)
#     assert Environment().repo.dir.name == "env2"
#     assert Environment().get_category("ParrotFishTest").get("Library1.rb").exists()
