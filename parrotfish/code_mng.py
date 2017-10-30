import warnings
from pathlib import Path

import dill
from pydent import *

from .diff import compare_content
from .env_mng import Environment
from .log import *
from .utils import *

logger = CustomLogging.get_logger(__name__)


class CodeManager(object):
    def __init__(self, category=None):
        self.category = category
        self.codes = {}
        self.load()

    # TODO: merge with collect_code?
    def get_code_parents(self, category=None):
        parent_dict = {}
        for parent_class_name, attr in CodeData.controller_dict.items():
            code_parents = []
            parent_class = AqBase.models[parent_class_name]
            attr = CodeData.controller_dict[parent_class_name]
            if category is None:
                code_parents = parent_class.all()
            else:
                code_parents = parent_class.where({"category": str(category)})
            parent_dict[parent_class_name] = code_parents
        return parent_dict

    def get_code_parents_by_category(self):
        parent_dict = self.get_code_parents()
        by_cat = {}
        for parent_class_name, parents in parent_dict.items():
            for code_parent in parents:
                cat = code_parent.category
                if cat not in by_cat:
                    by_cat[cat] = []
                by_cat[cat].append(code_parent)
        return by_cat

    def get_category_count(self):
        by_cat = self.get_code_parents_by_category()
        return {k: len(v) for k, v in by_cat.items()}

    def get_categories(self):
        return list(self.get_code_parents_by_category().keys())

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

    def collect_code(self, category=None):
        by_cat = self.get_code_parents_by_category()
        categories = list(by_cat.keys())
        if self.category is not None:
            categories = [self.category]
        for cat in categories:
            if cat not in by_cat:
                logger.error("category \"{}\" not found! {}".format(cat, list(by_cat.keys())))
            else:
                parents = by_cat[cat]
                logger.cli("collecting category \"{}\" ({} protocols)".format(cat, len(parents)))
                for p in parents:
                    self.add_code_metadata(CodeData(p, save=True))

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

    controller_dict = {
        Library.__name__      : "source",
        OperationType.__name__: "protocol"
    }

    def __init__(self, code_parent, save=False):
        self.parent = code_parent
        self.code = code_parent.code(self.accessor)
        self.created_at = None
        if save:
            try:
                self.save()
            except:
                logger.error("could not save code content for {}/{}".format(self.category, self.name))

    @property
    def accessor(self):
        return CodeData.controller_dict[self.parent.__class__.__name__]

    @property
    def name(self):
        return self.parent.name

    @property
    def category(self):
        return self.parent.category

    def save(self):
        """ Save to designated filepath """
        if self.code is None:
            logger.error("could not find code content for {}/{}".format(self.category, self.name))
            return None
        with open(self.filepath, 'w') as f:
            f.write(self.code.content)
            self.created_at = self.filepath.stat().st_mtime
            return self.filepath

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
        # TODO: resolve paths with incorrect separators
        name = self.name
        cat = self.category
        if sep in self.name:
            name = sanitize_filename(self.name)
            logger.warning("system seperator \"{}\" found in protocol name \"{}\". "
                           "Sanitizing to \"{}\".".format(sep, self.name, name))
        if sep in self.category:
            cat = sanitize_filename(self.name)
            logger.warning("system seperator \"{}\" found in category \"{}\"."
                           " Sanitizing to \"{}\".".format(sep, self.category, cat))
        catdir = Environment.category_dir(cat)
        return Path(catdir, '{}.rb'.format(sanitize_filename(name)))

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
