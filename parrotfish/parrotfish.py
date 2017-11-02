import hug
from pydent import *

from parrotfish.utils.utils import *
from parrotfish.utils.diff import *
from .environment import *

logger = CustomLogging.get_logger(__name__)
API = hug.API('parrotfish')


@hug.object(name='parrotfish', version='1.0.0', api=API)
class ParrotFish(object):
    """ CLI interface for managing Environment and code """

    controllers = [
        (OperationType, "protocol"),
        (Library, "source")
    ]

    @classmethod
    def check_for_session(cls):
        if Environment().session is None:
            raise Exception("You must be logged in. Register an Aquarium session.")

    @classmethod
    @hug.object.cli
    def push(cls):
        cls.check_for_session()
        code_files = cls.get_code_files()

        if not Environment().use_all_categories():
            code_files = [f for f in code_files if f.code_parent.category == Environment().category]

        for c in code_files:
            if cls.ok_to_push(c):
                c.code.content = c.read('r')
                c.code.update()
                # pass
        cls.save()

    @classmethod
    def fetch_parent_from_server(cls, code_file):
        code_parent = code_file.code_parent

        id_ = {"id": code_parent.id}
        aq_code_parents = code_parent.__class__.where(id_)
        if aq_code_parents is None or aq_code_parents == []:
            logger.warning("Could not find {} with {}".format(code_parent.__name__, id_))
        elif len(aq_code_parents) > 1:
            logger.warning("More than one {} found with {}".format(code_parent.__name__, id_))
        else:
            return aq_code_parents[0]

    @classmethod
    def fetch_content(cls, controller_instance):
        """
        Fetches code content from Aquarium model (e.g. ot.code('protocol')

        :param code_container: Model that contains code
        :type code_container: OperationType or Library
        :return:
        :rtype:
        """
        for controller, accessor in cls.controllers:
            if type(controller_instance) is controller:
                return controller_instance.code(accessor).content

    @classmethod
    def ok_to_push(cls, code_file):
        # Check last modified
        # modified_at = code_file.abspath.stat().st_mtime
        # if code_file.created_at == modified_at:
        #     logger.verbose("File has not been modified")
        #     return False
        fetched_content = code_file.code.content

        # Check local changes
        local_content = code_file.read('r')
        local_changes = compare_content(local_content, fetched_content)
        if not local_changes:
            logger.verbose("<{}/{}> there are no local changes.".format(code_file.code_parent.category,
                                                                        code_file.code_parent.name))
            return False

        # Check server changes
        server_content = cls.fetch_content(cls.fetch_parent_from_server(code_file))
        server_changes = compare_content(local_content, server_content)
        if not server_changes:
            logger.verbose("<{}/{}> there are not differences between local and server.".format(
                    code_file.code_parent.category,
                    code_file.code_parent.name))
            return False
        return True

    @classmethod
    def get_code_files(cls):
        if not Environment().session_dir().exists():
            logger.cli("There are no protocols in this repo.")
            return []
        files = Environment().session_dir().files
        code_files = [f for f in files if hasattr(f, 'code_parent')]
        return code_files

    @classmethod
    @hug.object.cli
    def protocols(cls):
        """ Get and count the number of protocols on the local machine """
        cls.check_for_session()
        files = cls.get_code_files()
        logger.cli(format_json(['/'.join([f.code_parent.category, f.code_parent.name]) for f in files]))

    @classmethod
    @hug.object.cli
    def category(cls):
        """ Get the current category of the environment. """
        logger.cli(Environment().category)
        return Environment().category

    @classmethod
    @hug.object.cli
    def set_category(cls, category: hug.types.text):
        """ Set the category of the environment. Set "all" to use all categories. Use "categories" to find all
        categories. """
        cls.check_for_session()
        logger.cli("Setting category to \"{}\"".format(category))
        Environment().category = category
        cls.save()

    @classmethod
    @hug.object.cli
    def categories(cls):
        """ Get all available categories and count """
        cls.check_for_session()
        logger.cli("Getting category counts:")
        categories = {}
        for controller, _ in cls.controllers:
            for m in controller.all():
                categories.setdefault(m.category, []).append(m)
        category_count = {k: len(v) for k, v in categories.items()}
        logger.cli(format_json(category_count))

    @classmethod
    @hug.object.cli
    def set_session(cls, session_name: hug.types.text):
        """ Set the session by name. Use "sessions" to find all available sessions. """
        cls.check_for_session()
        sessions = Environment().session.sessions
        if session_name not in sessions:
            logger.error("Session \"{}\" not in available sessions ({})".format(session_name, ', '
                                                                                              ''.join(sessions.keys())))

        logger.cli("Setting session to \"{}\"".format(session_name))
        Environment().session.set(session_name)
        cls.save()

    @classmethod
    @hug.object.cli
    def state(cls):
        logger.cli(format_json({
            "session": str(Environment().session.session),
            "sessions": ', '.join(Environment().session.sessions.keys()),
            "category": Environment().category,
            "repo": str(Environment().repo.abspath)
        }))

    # @classmethod
    # @hug.object.cli
    # def set_repo(cls, path: hug.types.text):
    #     """ Set the remote directory location for the repo folder """
    #     path = Path(path).absolute()
    #     if not path.is_dir():
    #         raise Exception("Path {} does not exist.".format(path))
    #     else:
    #         logger.cli("Setting repo to \"{}\"".format(path))

    @classmethod
    @hug.object.cli
    def repo(cls):
        """ Get the repo location for the managed protocols """
        logger.cli("Repo Location: {}".format(str(Environment().repo.abspath)))

    @classmethod
    @hug.object.cli
    def move_repo(cls, path: hug.types.text):
        """ Moves the current repo to another location. """
        path = Path(path).absolute()
        if not path.is_dir():
            raise Exception("Path {} does not exist".format(str(path)))
        logger.cli("Moving repo location from {} to {}".format(Environment().repo.abspath, path))
        Environment().repo.mvdirs(path)
        cls.save()

    @classmethod
    @hug.object.cli
    def sessions(cls):
        """ List the current avilable sessions """
        sessions = Environment().session.sessions
        logger.cli(format_json({n: str(s) for n, s in sessions.items()}))
        return sessions

    @classmethod
    @hug.object.cli
    def session(cls):
        """ Show the current session """
        logger.cli(str(Environment().session))
        return Environment().session.session_name

    # @requires_session
    @classmethod
    @hug.object.cli
    def fetch(cls):
        """ Fetch protocols from the current session & category and pull to local repo. """
        cls.check_for_session()
        for controller, accessor in cls.controllers:
            models = None
            if Environment().use_all_categories():
                models = controller.all()
                logger.cli("Fetching all categories...")
            else:
                models = controller.where({"category": Environment().category})
                logger.cli("Fetching code for category {}".format(Environment().category))
            logger.cli("\t{} {} found...".format(len(models), inflection.pluralize(controller.__name__)))
            for m in models:
                logger.cli("\t\tSaving code for {}/{}".format(m.category, m.name))
                code = m.code(accessor)
                if code is None:
                    logger.warning("\t\tCould not get code content for {}".format(m.name))
                    continue
                cat_dir = Environment().get_category(m.category)
                code_name = '{}.rb'.format(m.name)
                if sep in code_name:
                    code_name = sanitize_filename(code_name)
                code_file = cat_dir.add_file(code_name, make_attr=False, push_up=False)
                code_file.write('w', code.content)

                # add additional code_parent information to the MagicFile instance
                code_file.code = code
                code_file.code_parent = m
                code_file.created_at = code_file.abspath.stat().st_mtime
        cls.save()

    @staticmethod
    def save():
        Environment().save()

    @staticmethod
    def load():
        Environment().load()

    @classmethod
    @hug.object.cli
    def set_verbose(cls, v):
        """ Turns verbose mode on or off """
        if v:
            CustomLogging.set_level(logging.VERBOSE)
            logger.cli("verbose ON")
        else:
            CustomLogging.set_level(logging.CLI)
            logger.cli("verbose OFF")

    @classmethod
    @hug.object.cli
    def register(cls, login: hug.types.text,
                 password: hug.types.text,
                 aquarium_url: hug.types.text,
                 session_name: hug.types.text):
        """ Registers a new session. """
        Environment().session.create(login, password, aquarium_url, session_name=session_name)
        logger.cli("registering session: {}".format(session_name))
        cls.save()
        return cls

    @classmethod
    @hug.object.cli
    def unregister(cls, name):
        sessions = Environment().session.sessions
        if name in sessions:
            logger.cli("Unregistering {}: {}".format(name, str(sessions[name])))
            del sessions[name]
            Environment().session.session = None
        else:
            logger.cli("Session {} does not exist".format(name))
        cls.save()


# def call_command(command, *args, **kwargs):
#     """ simulates running command line for testing purposes """
#     Session.reset()
#     ParrotFish.load()
#     fxn = getattr(ParrotFish, command)
#     return fxn(*args, **kwargs)


def main():
    Environment().load()
    CustomLogging.set_level(logging.VERBOSE)
    API.cli()

if __name__ == '__main__':
    main()
