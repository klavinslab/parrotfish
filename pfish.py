##########################################
#
# python pfish.py cmd *args **kwargs
#
##########################################


from parrotfish import *

if __name__ == '__main__':
    ParrotFish.load()
    CustomLogging.set_level(logging.VERBOSE)
    API.cli()