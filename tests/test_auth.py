"""Tests authentication process"""

def test_main(cli, credentials):
    cli.register(**credentials['nursery'])
    cats = cli._get_categories()
    pass