import warnings
from pathlib import *
import dill
import hug
from pydent import *
import shutil

# TODO: better paths for protocols
# TODO: better path for state
# TODO: better handling of categories

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

    @classmethod
    def fetch_helper(cls, parent_class_name):
        controller_dict = {
            Library.__name__      : "source",
            OperationType.__name__: "protocol"
        }

        # get codes
        code_containers = []
        parent_class = AqBase.models[parent_class_name]
        attr = controller_dict[parent_class_name]
        if cls.category is None:
            code_containers = parent_class.all()
        else:
            code_containers = parent_class.where({"category": str(cls.category)})

        # save code containers
        cls.save_code_containers(code_containers, parent_class_name)
        print("Pulling {} ({}) to {}".format(inflection.pluralize(parent_class_name), cls.category, cls.master))
        print("\t{} {} found".format(inflection.pluralize(parent_class_name), len(code_containers)))

        # save code
        for c in code_containers:
            code = c.code(attr)
            filename = "{}.rb".format(c.name)
            filepath = Path.joinpath(cls.catdir, filename)
            with open(filepath, 'w') as f:
                f.write(code.content)

    @classmethod
    def save_code_containers(cls, code_containers, parent_class_name):
        d = {}
        d.update(cls.load_code_containers())
        d.update({parent_class_name: code_containers})
        with open(cls.code_pickle, 'wb') as f:
            dill.dump(d, f)

    @classmethod
    def load_code_containers(cls):
        cpp = cls.code_pickle
        if cpp.is_file():
            with open(cpp, 'rb') as f:
                return dill.load(f)
        return {}

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
        cls.fetch_helper(OperationType.__name__)
        cls.fetch_helper(Library.__name__)
        return cls

    @classmethod
    @hug.object.cli
    def push(cls):
        """ Pushes code to Aquarium """
        categories = cls.category
        if cls.category is None:
            categories = "all"
        print(
                "Pushing protocols ({}) to {}: {}".format(categories, Session.session_name,
                                                          Session.session.aquarium_url))
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
            print("category deleted: {}".format(cls.catdir))

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
            print("> protocol bin ({})".format(m))
            print("> session state deleted ({})".format(p))

    @classmethod
    @hug.object.cli
    def get_state(cls):
        """ Gets the current state of the session """
        return {
            "sessions"    : Session.sessions,
            "session_name": Session.session_name,
            "category"    : cls.category,
            "bin": cls._bin_location
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
        print("Setting remote to {}".format(str(new_path)))
        if new_path != cls.bin:
            cls.copy_bin(new_path)
            if remove_old:
                shutil.rmtree(cls.bin)
            cls.set_bin(new_path)
            cls.save()


# TODO: move code to testing dir exclusively
def pseudo_cli(command, *args, **kwargs):
    """ simulates running command line for testing purposes """
    Session.reset()
    ParrotFishSession.load()
    fxn = getattr(ParrotFishSession, command)
    return fxn(*args, **kwargs)


if __name__ == '__main__':
    ParrotFishSession.load()
    API.cli()