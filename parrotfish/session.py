from pydent import AqSession
import pickle


class SessionsHook(type):
    """Necessary hook for sharing states between SessionManager instances"""
    def __init__(cls, name, bases, clsdict):
        cls._shared_state = {}
        super(SessionsHook, cls).__init__(name, bases, clsdict)


class SessionManager(object, metaclass=SessionsHook):
    """Creates and stores all created sessions"""

    def __init__(self):
        """Instantiates a SessionManager with a shared state (Borg-idiom)"""
        shared_state = self.__class__._shared_state
        self.__dict__ = shared_state
        if shared_state == {}:
            self.sessions = {}
            self.session_name = None

    def __setstate__(self, state):
        """Override magic method for pickling the SessionManager + sharedstates"""
        self.__class__._shared_state.update(state)
        self.__dict__ = self.__class__._shared_state

    def __getitem__(self, name):
        """Magic method for accessing sessions by name
            e.g. SessionManager()["MySession"]
        """
        return self.get_session(name)

    def get_session(self, name):
        """Returns the AqSession by name"""
        return self.sessions[name]

    @property
    def current(self):
        """Returns the current AqSession"""
        if self.session_name:
            return self.sessions[self.session_name]

    def set_current(self, name):
        """Sets the current session by name"""
        self.session_name = name

    def remove_session(self, name):
        """Removes the session by name from the dict of sessions"""
        if name in self.sessions:
            del self.sessions[name]

    def register_session(self, login, password, aquarium_url, name):
        """Creates and registers a new AqSession"""
        new_session = AqSession(login, password, aquarium_url, name=name)
        self.sessions[name] = new_session
        self.set_current(name)

    def save(self, filepath):
        """Saves the sessions as a pickled file"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

    def load(self, filepath):
        """This requires a bit of explanation. Since this is a Borg-like class with a shared,
        state, loading the pickled instance will automatically update the shared state
        of all SessionManager instances. No need to return anything after unpickling."""
        with open(filepath, 'rb') as f:
            pickle.load(f)

    def create_from_json(self, config):
        for session_name, session_config in config.items():
            self.register_session(name=session_name, **session_config)