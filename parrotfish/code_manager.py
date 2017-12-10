from parrotfish.utils import sanitize_filename
from pydent import AqSession
import json


class ContentController(object):

    def __init__(self, code_model, dir, filename):
        self.code_model = code_model
        self.file = dir.add_file(filename, push_up=False, make_attr=False)

    def write_content(self):
        self.file.write('w', self.code_model.content)

    @property
    def parent(self):
        session = self.code_model.session
        parent_class = self.code_model.parent_class
        parent_id = self.code_model.parent_id
        interface = session.model_interface(parent_class)
        parent = interface.find(parent_id)
        return parent

    def server_content(self):
        return self.parent.code(self.code_model.name)

    def local_content(self):
        return self.file.read('r')

    def fetched_content(self):
        return self.code_model.content

    def update(self):
        pass

    @property
    def meta(self):
        return self.code_model.dump()


class CodeTypeController(object):

    def __init__(self, code_type_model, dir):
        self.code_type = code_type_model
        self.codes = {}

    @property
    def meta(self):
        return self.code_type.dump()

    def add_code(self, accessor, dir, filename):
        self.codes[accessor] = ContentController(self.code_type.code(accessor),dir, filename)

    def write(self):
        for code in self.codes.values():
            code.write_content()


class OperationTypeController(CodeTypeController):

    def __init__(self, model, bin):

        basename = sanitize_filename(model.name)
        dir = bin.add(basename, push_up=False, make_attr=False)

        super().__init__(model, dir)

        self.basename = basename
        self.filename = '{}.json'.format(basename)
        self.file = dir.add_file(self.filename, push_up=False, make_attr=False)
        self.add_code("protocol", dir, "{}.rb".format(basename))
        self.add_code("precondition", dir, "{}__precondition.rb".format(basename))
        self.add_code("cost_model", dir, "{}__cost_model.rb".format(basename))
        self.add_code("documentation", dir, "{}__documentation.md".format(basename))

    @property
    def meta(self):
        return self.code_type.dump(include={"field_types": "allowable_field_types"})

    def write(self):
        super().write()
        with self.file.open('w') as f:
            json.dump(self.meta, f, indent=4)

#
# class CodeController(object):
#
#     def __init__(self, code_model, content_accessors, dir):
#         self.meta = code_model.dump()
#         self.session = code_model.session
#         self.type = code_model.__class__.__name__
#         self.accessors = content_accessors
#
#         self.content_files = {}
#         self.code_meta = {}
#         for accessor in content_accessors:
#             code = self.code(accessor)
#             filename = sanitize_filename(code.name + "__" + accessor + ".rb")
#             code_metadata = code.dump()
#             code_metadata['filename'] = filename
#             self.code_meta[accessor] = code_metadata
#
#
#
#
#         self.code_meta = {acc: self.code(acc).dump() for acc in content_accessors}
#
#     def interface(self):
#         return self.session.model_interface(self.type)
#
#     def live_model(self):
#         return self.interface().find(self.meta['id'])
#
#     def file_content(self, accessor):
#         """Return the code content contained in the file"""
#         return self.code_file.read('r')
#
#     def fetched_content(self, accessor):
#         """Return the code content that was last fetched"""
#         return self.code_meta[accessor]
#
#     def server_content(self, accessor):
#         """Return the code content that is located on the server"""
#         return self.live_model().code(self.accessor).content





