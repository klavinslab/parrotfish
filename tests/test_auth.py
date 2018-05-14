"""Tests authentication process"""
import sys
from pydent import pprint
def test_main(cli, credentials):
    cli.register(**credentials['nursery'])
    cats = cli._get_categories()
    pprint(cli._session_manager.__dict__)
    pass