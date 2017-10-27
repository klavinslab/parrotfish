from parrotfish import *

if __name__ == '__main__':
    ParrotFish.load()
    CustomLog.set_level(logging.VERBOSE)
    API.cli()