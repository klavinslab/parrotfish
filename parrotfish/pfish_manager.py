import hug
import dill
from pydent import *
import warnings
import os
import shutil

# TODO: better paths for protocols
# TODO: better path for state_pickle
# TODO: better handling of categories

def chainable(fxn):
    def wrapped(*args, **kwargs):
        fxn(*args, **kwargs)
        return args[0]

    return wrapped

class ParrotFishMeta(type):

    @chainable
    def __getattr__(cls, item):
        getattr(Session, item)

API = hug.API('parrotfish')

@hug.object(name='parrotfish', version='1.0.0', api=API)
class ParrotFishSession(object, metaclass=ParrotFishMeta):
    master_dir = "protocols"
    category = None #
    dirpath = os.path.dirname(os.path.abspath(__file__))
    binpath = os.path.abspath(os.path.join(dirpath, '..', 'bin'))
    state_pickle = os.path.join(binpath, 'session.pkl')

    @classmethod
    def check_bin(cls):
        if not os.path.isdir(cls.binpath):
            raise Exception("Bin path {} not found".format(cls.binpath))

    @classmethod
    def _getdir(cls, p):
        """
        get the absolute path of directory relative to binpath. If directory doesn't exist, create it.

        :param p:
        :type p:
        :return:
        :rtype:
        """
        cls.check_bin()
        p = os.path.join(cls.binpath, p)
        if not os.path.isdir(p):
            os.mkdir(p)
        return p

    @classmethod
    def getdir(cls):
        master_dir = cls._getdir(cls.master_dir)
        p = os.path.join(master_dir, Session.session_name())
        cls._getdir(p)
        return p

    @classmethod
    def getcategorydir(cls):
        p = os.path.join(cls.getdir(), cls.category)
        cls._getdir(p)
        return p

    @classmethod
    def fetch_helper(cls, parent_class_name):
        controller_dict = {
            Library.__name__      : "source",
            OperationType.__name__: "protocol"
        }
        code_containers = []
        parent_class = AqBase.models[parent_class_name]
        attr = controller_dict[parent_class_name]
        if cls.category is None:
            code_containers = parent_class.all()
        else:
            code_containers = parent_class.where({"category": str(cls.category)})
        print("Pulling {} ({}) to {}".format(inflection.pluralize(parent_class_name), cls.category, cls.getdir()))
        print("\t{} {} found".format(inflection.pluralize(parent_class_name), len(code_containers)))
        for c in code_containers:
            code = c.code(attr)
            filename = "{}.rb".format(c.name)
            filepath = os.path.join(cls.getcategorydir(), filename)
            with open(filepath, 'w') as f:
                f.write(code.content)

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
        print("Pushing protocols ({}) to {}: {}".format(categories, Session.session_name(), Session.session.aquarium_url))
        return cls

    @classmethod
    @hug.object.cli
    def clear(cls, force: hug.types.smart_boolean=False):
        """ Clear local files for the current session and category """
        ok = True
        if not force:
            res = input(prompt="Are you sure you would like to clear category {0} in session {1}? (y/n)".format(
                    cls.category, Session.session_name())).lower()
            if not res.startswith('y'):
                ok = False
        if ok:
            shutil.rmtree(cls.getcategorydir())
            print("category deleted: {}".format(cls.getcategorydir()))



    @classmethod
    @hug.object.cli
    def reset(cls, force: hug.types.smart_boolean=False):
        """ Removes all saved sessions and removes all protocols files """
        ok = True
        if not force:
            res = input(prompt="Are you sure you would like to reset/clear all sessions?".format(
                    cls.category, Session.session_name())).lower()
            if not res.startswith('y'):
                ok = False
        if ok:
            os.remove(cls.state_pickle)
            shutil.rmtree(cls.getdir())
            Session.reset()
            print("{} deleted".format(cls.state_pickle))


    @classmethod
    def save(cls):
        """ Pickes the session state for next CLI """
        state = {
            "sessions": Session.sessions,
            "session_name": Session.session_name(),
            "category": cls.category
        }
        dill.dump(state, open(cls.state_pickle, 'wb'))

    @classmethod
    def load(cls):
        """ Opens pickled session state for CLI """
        try:
            state = dill.load(open(cls.state_pickle, 'rb'))
            Session.sessions = state["sessions"]
            Session.set(state["session_name"])
            cls.set_category(state["category"])
        except KeyError:
            warnings.warn("could not import session state from {}".format(cls.state_pickle))
        except FileNotFoundError:
            pass

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

# PF = ParrotFishSession
# PF.register("vrana", "Mountain5", "http://52.27.43.242:81", session_name="nursery")
# PF.register("vrana", "Mountain5", "http://52.27.43.242", session_name="production")
# PF.production.fetch().push()
# PF.nursery.fetch().push()
