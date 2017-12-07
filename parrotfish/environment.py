import os
import dill
from magicdir import MagicDir
from parrotfish.utils.log import CustomLogging
from parrotfish.utils.utils import sanitize_filename
from parrotfish.session import SessionManager
from pathlib import Path

logger = CustomLogging.get_logger(__name__)


class Environment(object):
    """Manages the Aquarium session environment. The environment handles the following:

        - Folder and filepaths for storing protocols
        - Default filepath for the environment pickle, which saves all information from this env
        - Current session state through SessionManager

        ::

        Directory structure (handled by MagicDir)
            fishtank
            ├-session1
            │ ├-category1
            │ │ ├-protocol1.rb
            │ │ └-...
            | └-category2
            │   ├-protocol3.rb
            │   └-...
            └-session2
              ├-category1
              └-...
    """
    _shared_state = {}
    ALL = "all"
    PKGDIR = Path(__file__).parent.absolute()

    def __init__(self):
        self.__dict__ = self._shared_state
        if self._shared_state == {}:
            self.repo = MagicDir('fishtank')
            self.repo.add('protocols')
            self.category = None
            self.environment_name = 'default_env.pkl'
            self.session_manager = SessionManager()

    def session_dir(self):
        """ Location of the session directory """
        return self.repo.protocols.add(self.session_manager.session_name, push_up=False, make_attr=False)

    def get_category(self, cat):
        """Returns the category directory path for the given category"""
        if os.sep in cat:
            new_cat = sanitize_filename(cat)
            logger.warning(
                "Category {} is not a valid name. Renamed to {}".format(cat, new_cat))
            cat = new_cat
        return self.session_dir().add(cat, push_up=False, make_attr=False)

    def env_pkl(self):
        """Path to the environment pickle that holds information about this env"""
        e = Path(self.PKGDIR, '.environ')
        os.makedirs(e, exist_ok=True)
        return Path(e, self.environment_name)

    def move_repo(self, new_parent):
        """Moves the main repo folder ("fishtank") to a new location"""
        self.repo.mvdirs(new_parent)

    def save(self):
        """Saves the environment to the pickle filepath."""
        with open(self.env_pkl(), 'wb') as f:
            dill.dump(self, f)

    @property
    def environment_file(self):
        return Path(self.PKGDIR, '.environ')

    def load(self):
        """Loads the environment from the pickle filepath.

        How this loads is a little bit fancy. The pickle unloaded the pickled instance's shared
        state. The overridden magic __setstate__ updates the class's shared state dictionary which
        results in updating *all* shared_states for all environment instances. No need to return
        anything here."""
        e = self.environment_file
        os.makedirs(e, exist_ok=True)
        if self.env_pkl().is_file():
            with open(self.env_pkl(), 'rb') as f:
                dill.load(f)


    def use_all_categories(self):
        """Whether to use all protocol categories"""
        return self.category is None or \
            self.category.lower().strip() == Environment.ALL

    def __setstate__(self, state):
        """Called when the pickled environment is unpickled. Updates the shared state of all Env
        instances to the shared state found in the pickled environment."""
        self.__class__._shared_state.update(state)
        self.__dict__ = self.__class__._shared_state
