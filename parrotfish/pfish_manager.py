import shutil
import warnings
from pathlib import *

import dill
import hug
from pydent import *

API = hug.API('parrotfish')


def chainable(fxn):
    def wrapped(*args, **kwargs):
        fxn(*args, **kwargs)
        return args[0]

    return wrapped


def force_mkdir(fxn):
    def wrapped(*args, **kwargs):
        p = fxn(*args, **kwargs)
        p.mkdir(exist_ok=True)
        return p

    return wrapped


class ParrotFishMeta(type):
    _bin_location = Path(__file__).parent.parent.joinpath('bin').resolve()
    _default_bin_name = 'bin'

    def __getattr__(cls, item):
        if hasattr(Session, item):
            getattr(Session, item)
            return cls
        object.__getattribute__(cls, item)

    @property
    @force_mkdir
    def bin(cls):
        return cls._bin_location

    def copy_bin(cls, new_path):
        if not new_path.exists():
            shutil.copytree(cls.bin, new_path)

    def set_bin(cls, new_path):
        cls._bin_location = Path(new_path)

    @property
    @force_mkdir
    def master(cls):
        return Path.joinpath(cls.bin, 'protocols')

    @property
    @force_mkdir
    def session_dir(cls):
        return Path.joinpath(cls.master, Session.session_name)

    @property
    @force_mkdir
    def catdir(cls):
        if cls.category is None:
            return None
        return Path.joinpath(cls.session_dir, cls.category)

    @property
    def state_pickle(cls):
        return Path(__file__).resolve().parent.parent.joinpath('.sessions', 'state.pkl')

    @property
    def code_pickle(cls):
        cat = cls.catdir
        if cat is None:
            return None
        return Path.joinpath(cls.session_dir, 'code.pkl').resolve()

    @property
    def session(cls):
        return Session.session

    @property
    def sessions(cls):
        return Session.sessions

    @property
    def session_name(cls):
        return Session.session_name


@hug.object(name='parrotfish', version='1.0.0', api=API)
class ParrotFishSession(object, metaclass=ParrotFishMeta):
    category = None
    verbose = True

    @classmethod
    def log(cls, msg):
        if cls.verbose:
            print("> "+msg)

    @classmethod
    def save_code(cls, code):
        filename = "{}.rb".format(code.parent.name)
        filepath = Path(cls.catdir, filename)
        cls.set_category(code.parent.category)
        with open(filepath, 'w') as f:
            cls.log("saving {}".format(filepath))
            f.write(code.content)

    @classmethod
    def collect_code(cls):
        controller_dict = {
            Library.__name__      : "source",
            OperationType.__name__: "protocol"
        }

        # get codes

        codes = []
        for parent_class_name, attr in controller_dict.items():
            code_containers = []
            parent_class = AqBase.models[parent_class_name]
            attr = controller_dict[parent_class_name]
            if cls.category is None:
                code_containers = parent_class.all()
            else:
                code_containers = parent_class.where({"category": str(cls.category)})

            cls.log("pulling {} ({}) to {}".format(inflection.pluralize(parent_class_name), cls.category, cls.master))
            cls.log("\t{} {} found".format(inflection.pluralize(parent_class_name), len(code_containers)))

            # add the container to the code
            for c in code_containers:
                code = c.code(attr)
                code.parent = c
                codes.append(code)

        return codes

    @classmethod
    def pickle_code(cls, codes):
        d = cls.unpickle_code()
        for code in codes:
            d.update({code.parent.category: {code.parent.name: code}})
        with open(cls.code_pickle, 'wb') as f:
            dill.dump(d, f)

    @classmethod
    def unpickle_code(cls):
        if cls.code_pickle.is_file():
            with open(cls.code_pickle, 'rb') as f:
                return dill.load(f)
        return {}

    @classmethod
    @hug.object.cli
    def set_versbose(cls, v):
        """ Turns verbose mode on or off """
        cls.verbose = v
        return cls

    @classmethod
    @hug.object.cli
    def register(cls, login: hug.types.text,
                 password: hug.types.text,
                 aquarium_url: hug.types.text,
                 session_name: hug.types.text):
        """ Registers a new session. """
        Session.create(login, password, aquarium_url, session_name=session_name)
        cls.save()
        return cls

    @classmethod
    @hug.object.cli
    def checkout(cls, session_name: hug.types.text):
        """ Opens a session by name """
        Session.set(session_name)
        cls.save()
        return cls

    @classmethod
    @hug.object.cli
    def set_category(cls, name: hug.types.text):
        """ Sets the category for fetch, pull, push, etc. """
        cls.category = name
        cls.save()
        return cls

    @classmethod
    @hug.object.cli
    def fetch(cls):
        """ Retrieves protocols from Aquarium """
        codes = cls.collect_code()
        cls.pickle_code(codes)
        for code in codes:
            cls.save_code(code)
        return cls

    @classmethod
    @hug.object.cli
    def push(cls):
        """ Pushes code to Aquarium """
        categories = cls.category
        if cls.category is None:
            categories = "all"

        codes = cls.collect_code()
        old_codes = cls.unpickle_code()
        for code in codes:
            old_code = old_codes[code.category.name][code.parent.name]
            # TODO: do a comparison of last update with "code"
            # update code
            # TODO: remote_last_updated, local_last_updated
        return cls

    @classmethod
    @hug.object.cli
    def clear(cls, force: hug.types.smart_boolean = False):
        """ Clear local files for the current session and category """
        ok = True
        if not force:
            res = input(prompt="Are you sure you would like to clear category {0} in session {1}? (y/n)".format(
                    cls.category, Session.session_name)).lower()
            if not res.startswith('y'):
                ok = False
        if ok:
            shutil.rmtree(cls.catdir)
            cls.log("category deleted: {}".format(cls.catdir))

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
        if ok:
            if cls.state_pickle.is_file():
                cls.state_pickle.unlink()
            p = cls.state_pickle
            m = cls.master
            shutil.rmtree(str(cls.bin))
            Session.reset()
            cls.log("protocol bin ({})".format(m))
            cls.log("session state deleted ({})".format(p))

    @classmethod
    @hug.object.cli
    def get_state(cls):
        """ Gets the current state of the session """
        return {
            "sessions"    : Session.sessions,
            "session_name": Session.session_name,
            "category"    : cls.category,
            "bin"         : cls._bin_location
        }

    @classmethod
    def save(cls):
        """ Pickes the session state for next CLI """
        state = cls.get_state()
        dill.dump(state, open(cls.state_pickle, 'wb'))

    @classmethod
    def load(cls):
        """ Opens pickled session state for CLI """
        try:
            state = dill.load(open(cls.state_pickle, 'rb'))
            Session.sessions = state["sessions"]
            Session.set(state["session_name"])
            cls.set_category(state["category"])
            cls.set_bin(state["bin"])
        except KeyError:
            warnings.warn("could not import session state from {}".format(cls.state_pickle))
        except FileNotFoundError:
            pass
        except PillowtalkSessionError:
            pass

    @classmethod
    @hug.object.cli
    def set_remote(cls, parent_dst, bin_name=None, remove_old=True):
        """ Sets the remote folder to the folder 'parent_dst/bin_name' folder. By default, current bin contents
        will by copied to the new location. You can keep the old contents by setting remove_old=True """

        if bin_name is None:
            bin_name = cls._default_bin_name
        new_path = Path(parent_dst, bin_name).resolve()
        cls.log("setting remote to {}".format(str(new_path)))
        if new_path != cls.bin:
            cls.copy_bin(new_path)
            if remove_old:
                shutil.rmtree(cls.bin)
            cls.set_bin(new_path)
            cls.save()


def call_command(command, *args, **kwargs):
    """ simulates running command line for testing purposes """
    Session.reset()
    ParrotFishSession.load()
    fxn = getattr(ParrotFishSession, command)
    return fxn(*args, **kwargs)


if __name__ == '__main__':
    ParrotFishSession.load()
    API.cli()
