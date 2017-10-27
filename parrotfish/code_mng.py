import warnings
from datetime import datetime
from pathlib import Path

import dill
from pydent import *

from .diff import compare_content
from .env_mng import Environment
from .log import *

logger = CustomLog.get_logger(__name__)


class CodeManager(object):
    def __init__(self, category=None):
        self.category = category
        self.codes = {}
        self.load()

    def add_code_metadata(self, code_meta):
        cat = code_meta.category
        if cat not in self.codes:
            self.codes[cat] = {}
        self.codes[cat][code_meta.name] = code_meta

    def save(self):
        with open(Environment.code_pickle, 'wb') as f:
            dill.dump(self.codes, f)

    def load(self):
        if Environment.code_pickle.is_file():
            with open(Environment.code_pickle, 'rb') as f:
                self.codes = dill.load(f)

    def collect_code(self):
        controller_dict = {
            Library.__name__      : "source",
            OperationType.__name__: "protocol"
        }

        for parent_class_name, attr in controller_dict.items():
            code_parents = []
            parent_class = AqBase.models[parent_class_name]
            attr = controller_dict[parent_class_name]
            if self.category is None:
                code_parents = parent_class.all()
            else:
                code_parents = parent_class.where({"category": str(self.category)})
            for cp in code_parents:
                self.add_code_metadata(CodeData(attr, cp, save=True))

    # TODO: tag code when pushed with stamp
    # def tag_code(self):
    #     "{time} {login} {changes}".format(
    #             time=str(datetime.now())
    #     )

    # TODO: manage new code that was never fetched...
    def push_code(self):

        for cat, codes in self.codes.items():
            for name, meta in codes.items():
                if not meta.exists():
                    logger.error("{} is missing!".format(meta.filepath))
                    continue
                if meta.last_modified == meta.created_at:
                    logger.verbose("{} has not been modified".format(meta.filepath))
                    continue
                parent = meta.fetch_parent()
                if parent is None:
                    logger.error("Could not find protocol {}/{}".format(meta.category, meta.name))
                    continue
                local_diff = meta.diff_local_changes()
                if local_diff.strip() == '':
                    logger.cli("no local changes for {}".format(meta.filepath))
                else:
                    logger.cli("Local changes:\n\n{}".format(local_diff))
                    meta.code.content = meta.local_content
                    aq_diff = meta.diff_local_and_aq()
                    logger.verbose("{} changes:\n\n{}".format(meta.filepath, aq_diff))
                    meta.code.update()
                    logger.cli("{} updated!".format(meta.name))


class CodeData(object):
    """ Container for code and its parent (OperationType, Library, etc.) """

    def __init__(self, code_accessor, code_parent, save=False):
        self.accessor = code_accessor
        self.parent = code_parent
        self.code = code_parent.code(code_accessor)
        self.name = code_parent.name
        self.parent_class_name = code_parent.__class__.__name__
        self.category = code_parent.category
        self.created_at = None
        if save:
            self.save()

    def save(self):
        """ Save to designated filepath """
        with open(self.filepath, 'w') as f:
            f.write(self.code.content)
            self.created_at = self.filepath.stat().st_mtime

    @property
    def local_content(self):
        with open(self.filepath, 'r') as f:
            content = f.read()
            print(content)
            return content

    @property
    def rel_path(self):
        """ Path relative to session directory """
        return self.filepath.relative_to(Environment.session_dir)

    def exists(self):
        return self.filepath.is_file()

    @property
    def filepath(self):
        """ Expected filepath for this code """
        catdir = Path(Environment.session_dir, self.category).resolve()
        catdir.mkdir(exist_ok=True)
        return Path(catdir, '{}.rb'.format(self.name))

    @property
    def last_modified(self):
        if self.exists():
            return self.filepath.stat().st_mtime

    def fetch_parent(self):
        iden = {"id": self.parent.id}
        parent_class = self.parent.__class__
        parents = parent_class.where(iden)

        if parents is None or parents == []:
            warnings.warn("Could not find {} with {}".format(parent_class.__name__, iden))
        elif len(parents) > 1:
            warnings.warn("More than one {} found with {}".format(parent_class.__name__, iden))
        else:
            parent = parents[0]
            return CodeData(self.accessor, parent, save=False)

    def diff_local_and_aq(self):
        """ Difference between local file and Aquarium code """
        return compare_content(self.fetch_parent().code.content, self.local_content)
        # self.fetch_parent.diff_local_changes()

    def diff_local_changes(self):
        """ Difference between intial fetch and current code """
        print(self.code.content)
        print(self.local_content)
        print(self.filepath)
        return compare_content(self.code.content, self.local_content)
