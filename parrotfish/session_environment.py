import os
import dill
from magicdir import MagicDir
from parrotfish.utils.log import CustomLogging
from parrotfish.utils import sanitize_filename
from parrotfish.session import SessionManager
from pathlib import Path

logger = CustomLogging.get_logger(__name__)


class SessionEnvironment(MagicDir):

    def __init__(self, path):
        super().__init__(os.path.basename(path), push_up=False)
        self.set_dir(os.path.dirname(path))

        # add the environment pickle
        self.env_pkl = self.add_file('.env_pkl', attr='env_pkl')

        # add protocols folder
        self.protocols = self.add('protocols')

    def save(self):
        with self.env_pkl.open('wb') as f:
            dill.dump(self, f)

    def load(self):
        if self.env_pkl.is_file():
            with self.env_pkl.open('rb') as f:
                loaded = dill.dump(self, f)
                vars(self).update(vars(loaded))
