from parrotfish.log import *
from pydent import *

logger = CustomLogging.get_logger(__name__)

class

#
# class CodeData(object):
#     """ Container for code and its parent (OperationType, Library, etc.) """
#
#     controller_dict = {
#         Library.__name__      : "source",
#         OperationType.__name__: "protocol"
#     }
#
#     def __init__(self, code_parent, save=False):
#         self.parent = code_parent
#         self.code = code_parent.code(self.accessor)
#         self.created_at = None
#         if save:
#             try:
#                 self.save()
#             except:
#                 logger.error("could not save code content for {}/{}".format(self.category, self.name))
#
#     @property
#     def accessor(self):
#         return CodeData.controller_dict[self.parent.__class__.__name__]
#
#     @property
#     def name(self):
#         return self.parent.name
#
#     @property
#     def category(self):
#         return self.parent.category
#
#     def save(self):
#         """ Save to designated filepath """
#         if self.code is None:
#             logger.error("could not find code content for {}/{}".format(self.category, self.name))
#             return None
#         with open(self.filepath, 'w') as f:
#             f.write(self.code.content)
#             self.created_at = self.filepath.stat().st_mtime
#             return self.filepath
#
#     @property
#     def local_content(self):
#         with open(self.filepath, 'r') as f:
#             content = f.read()
#             print(content)
#             return content
#
#     @property
#     def rel_path(self):
#         """ Path relative to session directory """
#         return self.filepath.relative_to(Environment.session_dir)
#
#     def exists(self):
#         return self.filepath.is_file()
#
#     @property
#     def filepath(self):
#         """ Expected filepath for this code """
#         # TODO: resolve paths with incorrect separators
#         name = self.name
#         cat = self.category
#         if sep in self.name:
#             name = sanitize_filename(self.name)
#             logger.warning("system seperator \"{}\" found in protocol name \"{}\". "
#                            "Sanitizing to \"{}\".".format(sep, self.name, name))
#         if sep in self.category:
#             cat = sanitize_filename(self.name)
#             logger.warning("system seperator \"{}\" found in category \"{}\"."
#                            " Sanitizing to \"{}\".".format(sep, self.category, cat))
#         catdir = Environment.category_dir(cat)
#         return Path(catdir, '{}.rb'.format(sanitize_filename(name)))
#
#     @property
#     def last_modified(self):
#         if self.exists():
#             return self.filepath.stat().st_mtime
#
#     def fetch_parent(self):
#         iden = {"id": self.parent.id}
#         parent_class = self.parent.__class__
#         parents = parent_class.where(iden)
#
#         if parents is None or parents == []:
#             logger.warning("Could not find {} with {}".format(parent_class.__name__, iden))
#         elif len(parents) > 1:
#             logger.warning("More than one {} found with {}".format(parent_class.__name__, iden))
#         else:
#             parent = parents[0]
#             return CodeData(self.accessor, parent, save=False)
#
#     def diff_local_and_aq(self):
#         """ Difference between local file and Aquarium code """
#         return compare_content(self.fetch_parent().code.content, self.local_content)
#         # self.fetch_parent.diff_local_changes()
#
#     def diff_local_changes(self):
#         """ Difference between intial fetch and current code """
#         print(self.code.content)
#         print(self.local_content)
#         print(self.filepath)
#         return compare_content(self.code.content, self.local_content)
