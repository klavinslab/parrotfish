from os import sep
import json
import inflection


def sanitize_filename(name):
    return name.replace(sep, '_')


def format_json(j):
    return json.dumps(j, indent=4, sort_keys=True)


def attributerize(word):
    return inflection.parameterize(word).replace('-', '_')


    #         if sep in self.name:
    #             name = sanitize_filename(self.name)
    #             logger.warning("system seperator \"{}\" found in protocol name \"{}\". "
    #                            "Sanitizing to \"{}\".".format(sep, self.name, name))
    #         if sep in self.category:
    #             cat = sanitize_filename(self.name)
    #             logger.warning("system seperator \"{}\" found in category \"{}\"."
    #                            " Sanitizing to \"{}\".".format(sep, self.category, cat))
