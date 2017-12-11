import os
import dill
from magicdir import MagicDir
from parrotfish.utils.log import CustomLogging
from parrotfish.utils import sanitize_filename, sanitize_attribute
from parrotfish.session import SessionManager
from pathlib import Path
from pydent.models import OperationType, Library

logger = CustomLogging.get_logger(__name__)


class SessionEnvironment(MagicDir):

    def __init__(self, path, session_login, session_url):
        """

        :param path: The path of this session
        :type path: str
        """
        super().__init__(os.path.basename(path), push_up=False, check_attr=False)

        self.session_login = session_login
        self.session_url = session_url

        self.set_dir(os.path.dirname(path))

        # add the environment pickle
        self.add_file('.env_pkl', attr='env_pkl')

        # add protocols folder
        self.add('protocols')

    def save(self):
        with self.env_pkl.open('wb') as f:
            dill.dump(self, f)

    def load(self):
        if self.env_pkl.is_file():
            with self.env_pkl.open('rb') as f:
                loaded = dill.dump(self, f)
                vars(self).update(vars(loaded))

    @property
    def session(self):
        """
        Use self.name, self.url, and self.login to grab the session from the installation folder since
        we don't want to store that information in this folder...
        :return:
        :rtype:
        """
        pass

    # Methods for writing and reading OperationType and Library

    def operation_type_dir(self, category, operation_type_name):
        # add the category directory to the protocols directory
        cat_dirname = sanitize_filename(category)
        cat_dir = self.protocols.add(sanitize_attribute(category))

        # add a new folder using operation type name
        basename = sanitize_filename(operation_type_name)
        ot_dir = cat_dir.add(basename)

        # add operation type files
        ot_dir.add_file('{}.json'.format(basename), attr='meta')
        ot_dir.add_file('{}.rb'.format(basename), attr='protocol')
        ot_dir.add_file('{}__precondition.rb'.format(basename), attr='precondition')
        ot_dir.add_file('{}__cost_model.rb'.format(basename), attr='cost_model')
        ot_dir.add_file('{}__documentation.rb'.format(basename), attr='documentation')

        return ot_dir

    def library_type_dir(self, category, library_name):
        # add the category directory to the protocols directory
        cat_dirname = sanitize_filename(category)
        cat_dir = self.protocols.add(cat_dirname)

        # add a new folder using operation type name
        basename = sanitize_filename(library_name)
        lib_dir = cat_dir.add(basename)

        # add library source file
        lib_dir.add_file('{}.json'.format(basename), attr='meta')
        lib_dir.add_file('{}.rb'.format(basename), attr='source')

        return lib_dir

    def write_operation_type(self, operation_type):
        ot_dir = self.operation_type_dir(operation_type.category, operation_type.name)

        include = {
            'field_types': 'allowable_field_types'
        }

        # write metadata
        ot_dir.meta.dump(
            operation_type.dump(
                include={'protocol': {},
                         'documentation': {},
                         'cost_model': {},
                         'precondition': {},
                         'field_types': 'allowable_field_types'
                         }
            ),
            indent=4,
        )

        # write codes
        ot_dir.protocol.write(operation_type.code('protocol').content)
        ot_dir.precondition.write(operation_type.code('precondition').content)
        ot_dir.documentation.write(operation_type.code('documentation').content)
        ot_dir.cost_model.write(operation_type.code('cost_model').content)

    def write_library(self, library):
        lib_dir = self.library_type_dir(library.category, library.name)

        # write json
        lib_dir.meta.dump(library.dump(include={'source'}), indent=4)

        # write codes
        lib_dir.source.write(library.code('source').content)

    def read_operation_type(self, category, name):
        ot_dir = self.operation_type_dir(category, name)
        metadata = ot_dir.meta.load()
        ot = OperationType.load(metadata)

        ot.protocol.content = ot_dir.protocol.read()
        ot.precondition.content = ot_dir.precondition.read()
        ot.documentation.content = ot_dir.documentation.read()
        ot.cost_model.content = ot_dir.cost_model.read()
        return ot

    def read_library_type(self, category, name):
        lib_dir = self.library_type_dir(category, name)
        metadata = lib_dir.meta.load()
        lib = Library.load(metadata)

        lib.source.content = lib_dir.source.read()
        return lib


# class CodeController(MagicDir):
#
#     def __init__(self, category, name, accessors):
#         cat_dirname = sanitize_filename(category)
#         cat_dir = self.protocols.add(sanitize_attribute(category))
#
#         # add a new folder using operation type name
#         basename = sanitize_filename(name)
#         super().__init__(basename, push_up=False, check_attr=False)
#
#
#
#     def write(self):
#         pass
#
#     def read(self):
#         pass






