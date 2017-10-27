# import sys, os
# PACKAGE_PARENT = '..'
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
from .env_mng import *
from .code_mng import *
import hug
from .log import *

logger = CustomLog.get_logger(__name__)
API = hug.API('parrotfish')

# TODO: default dictionary gets deleted upon reset when environment is not found.
# TODO: propery setup.py packaging
# TODO: throw warning if root folders get moved or renamed (if root need to be rebuilt, log WARNING)
# TODO: save session information in session_dir
# TODO: add file in root folder to 'reconnect' with pfish whereever it is...

class ParrotFishHook(type):

    def __getattr__(cls, item):
        if item in Session.sessions:
            getattr(Session, item)
            return cls
        else:
            object.__getattribute__(cls, item)

    @property
    def session_name(cls):
        return Session.session_name

    @property
    def session(cls):
        return Session.session

    @property
    def sessions(cls):
        return Session.sessions

    @property
    def catdir(cls):
        if not cls.category is None:
            return Environment.category_dir(cls.category)

@hug.object(name='parrotfish', version='1.0.0', api=API)
class ParrotFish(object, metaclass=ParrotFishHook):
    category = None

    @classmethod
    @hug.object.cli
    def set_verbose(cls, v):
        """ Turns verbose mode on or off """
        if v:
            CustomLog.set_level(logging.VERBOSE)
            logger.cli("verbose ON")
        else:
            CustomLog.set_level(logging.CLI)
            logger.cli("verbose OFF")


    @classmethod
    @hug.object.cli
    def register(cls, login: hug.types.text,
                 password: hug.types.text,
                 aquarium_url: hug.types.text,
                 session_name: hug.types.text):
        """ Registers a new session. """
        Session.create(login, password, aquarium_url, session_name=session_name)
        logger.cli("registering session: {}".format(cls.get_session))
        cls.save()
        return cls

    @classmethod
    @hug.object.cli
    def checkout(cls, session_name: hug.types.text):
        """ Opens a session by name """
        logger.cli("checking out session \"{}\"".format(session_name))
        try:
            Session.set(session_name)
        except PillowtalkSessionError as e:
            available_sessions = ', '.join(list(Session.sessions.keys()))
            logging.error("Cannot checkout session \"{}\". Available sessions: {}".format(session_name,
                                                                                          available_sessions))
            raise e
        cls.save()
        return cls

    @classmethod
    @hug.object.cli
    def get_sessions(cls):
        sessions = list(Session.sessions.keys())
        logger.cli("sessions: {}".format(', '.join(sessions)))
        return sessions

    @classmethod
    @hug.object.cli
    def set_category(cls, name: hug.types.text):
        """ Sets the category for fetch, pull, push, etc. """
        cls.category = name
        cls.save()
        logger.cli("category set to {}".format(name))
        return cls

    @classmethod
    @hug.object.cli
    def set_remote(cls, parent_dst, root_name=None, remove_old=True):
        """ Sets the remote folder to the folder 'parent_dst/root_name' folder. By default, current root contents
        will by copied to the new location. You can keep the old contents by setting remove_old=True """

        if root_name is None:
            root_name = DN.ROOT
        parent_dst = Path(parent_dst).resolve()
        if not parent_dst.is_dir():
            raise Exception("Cannot set_remote. Directory \"{}\" does not exist.".format(parent_dst))
        new_path = Path(parent_dst, root_name).resolve()
        logger.cli("setting remote to {}".format(str(new_path)))
        if new_path != Environment._root_location:
            Environment.copy_root(new_path)
            if remove_old:
                shutil.rmtree(Environment.root)
            Environment.set_root(new_path)
            cls.save()

    @classmethod
    @hug.object.cli
    def get_session(cls):
        """ Get the current session json """
        session_json = {
            "login": Session.session.login,
            "password": "*"*10,
            "aquarium_url": Session.session.aquarium_url,
            "session_name": Session.session_name
        }
        logger.cli("session info: {}".format(session_json))
        return session_json

    @classmethod
    @hug.object.cli
    def get_category(cls):
        cat = cls.category
        logger.cli("category: {}".format(cat))
        return cat

    @classmethod
    @hug.object.cli
    def get_categories(cls):
        cm = CodeManager()
        cats = cm.categories
        logger.cli("categories: {}".format(", ".join(cats)))
        return cats

    @classmethod
    @hug.object.cli
    def get_remote(cls):
        """ Return path of the root folder """
        root = str(Environment.root)
        logger.cli("remote path: {}".format(str(root)))
        return root

    @classmethod
    @hug.object.cli
    def fetch(cls):
        """ Retrieves protocols from Aquarium """
        logger.cli("fetching code from {}".format(Session.session.aquarium_url))
        cm = CodeManager(cls.category)
        cm.collect_code()
        cm.save()
        return cls

    @classmethod
    @hug.object.cli
    def push(cls):
        """ Pushes code to Aquarium """
        cm = CodeManager()
        cm.push_code()
        logger.cli("code pushed to {}".format(Session.session.aquarium_url))
        return cls

    @classmethod
    @hug.object.cli
    def pushfetch(cls):
        """ Pushes code and then fetches """
        cls.push()
        cls.fetch()

    @classmethod
    @hug.object.cli
    def clear_category(cls, force: hug.types.smart_boolean = False):
        """ Clear local files for the current session and category """
        ok = True
        if not force:
            res = input("Are you sure you would like to clear category \"{0}\" in session {1}? (y/n): ".format(
                    cls.category, Session.session_name)).lower()
            if not res.startswith('y'):
                logger.cli("clear canceled")
                ok = False
        if ok:
            shutil.rmtree(cls.catdir)
            logger.cli("category \"{}\" deleted".format(cls.catdir))
        return cls

    @classmethod
    @hug.object.cli
    def reset(cls, force: hug.types.smart_boolean = False):
        """ Removes all saved sessions and removes all protocols files """
        ok = True
        if not force:
            res = input("Are you sure you would like to reset/clear all sessions? (y/n): ".format(
                    cls.category, Session.session_name)).lower()
            if not res.startswith('y'):
                ok = False
                logger.cli("reset canceled")
        if ok:
            e = Environment.env
            if Environment.env.is_file():
                Environment.env.unlink()
            else:
                logger.cli("No environment file found. Reset canceled.")
                return cls
            p = Environment.env
            m = Environment.master_dir
            r = Environment.root
            shutil.rmtree(str(Environment.root))
            Session.reset()
            logger.cli("protocol root ({})".format(m))
            logger.cli("session environment deleted ({})".format(p))
        return cls

    @classmethod
    def set_env(cls, name):
        Environment.set_env(name)
        cls.load()

    @staticmethod
    def default_env(cls):
        Environment.default_env()

    @classmethod
    @hug.object.cli
    def get_env(cls):
        """ Gets the current environment of the session """
        return {
            "sessions"    : Session.sessions,
            "session_name": Session.session_name,
            "root"         : Environment._root_location,
            "category"    : ParrotFish.category
        }

    @classmethod
    def save(cls):
        """ Pickes the session environment for next CLI """
        env = cls.get_env()
        with open(Environment.env, 'wb') as f:
            dill.dump(env, f)
            assert Environment.env.is_file()
            logger.verbose("environment dumped to {}".format(str(f)))

    @classmethod
    def load(cls):
        """ Opens pickled session environment for CLI """
        try:
            env = dill.load(open(Environment.env, 'rb'))
            Session.sessions = env["sessions"]
            Session.set(env["session_name"])
            ParrotFish.set_category(env["category"])
            Environment.set_root(env["root"])
            logger.verbose("environment loaded from {}".format(Environment.root))
        except KeyError:
            logger.warning("could not import session state from {}".format(Environment.env))
        except FileNotFoundError:
            pass
        except PillowtalkSessionError:
            pass


def call_command(command, *args, **kwargs):
    """ simulates running command line for testing purposes """
    Session.reset()
    ParrotFish.load()
    fxn = getattr(ParrotFish, command)
    return fxn(*args, **kwargs)
