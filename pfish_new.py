from pydent import *


class ProtocolCode(object):

    def __init__(self):
        pass



class SessionManager(object):



    def __init__(self):
        self.session = None


    def pull(self, **kwargs):
        Session.set(self.session)
        ots = []
        print("Pulling OperationTypes...")
        if kwargs is None or kwargs == {}:
            ots = OperationType.all()
        else:
            ots = OperationType.where(kwargs)
        for ot in ots:
            codes = ot.codes
            for code in ot.codes:
                pass
                # TODO: pull down all library, protocol, etc. code
                # TODO: for each session create a folder in your dir folder

    def push(self, **kwargs):
        pass

    def pull_request(self, other):
        pass
        # TODO: or this can be done through github

    # TODO: auto-push upon git push...

class FishSchool(object):

    pass
    # TODO: pair of parrotfish?

config = None
with open("config.json", 'rU') as f:
    config = json.load(f)

Session.create_from_json(config["sessions"])
Session.Nursery
p = ParrotFish()
p.pull(category="Justin")