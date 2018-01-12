"""Tests for testing tools"""


from parrotfish.utils import testing_tools


def test_generate_random_operations(sm, credentials):
    sm.register_session(**credentials['nursery'])
    session = sm.get_session('nursery')
    ot = session.OperationType.where({"name": "Protocol3", "category": "ParrotFishTest"})[0]

    ops = testing_tools.generate_random_operations(ot, 3)
    assert len(ops) == 3
    for op in ops:
        assert 'id' in op
        assert 'status' in op
        assert op['operation_type_id'] == ot.id

    ops2 = testing_tools.generate_random_operations(ot, 5)
    assert len(ops2) == 5
    for op in ops2:
        assert 'id' in op
        assert 'status' in op
        assert op['operation_type_id'] == ot.id


def test_run_random_ops(sm, credentials):
    sm.register_session(**credentials['nursery'])
    session = sm.get_session('nursery')
    ot = session.OperationType.where({"name": "Protocol3", "category": "ParrotFishTest"})[0]

    result = testing_tools.run_operation_test_with_random(ot, 5)
    pass
