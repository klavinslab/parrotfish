"""Tests for testing tools"""

from parrotfish.utils import testing_tools

TEST_OT_NAME = "ParrotFishTestOperation"
TEST_OT_CATEGORY = "ParrotFishTest"
TEST_PRECONDITION_OT = "ParrotFishPreconditionFail"
TEST_BATCH = "ParrotFishBatchSizeConditionalFail"


def test_generate_random_operations(sm, credentials):
    sm.register_session(**credentials['nursery'])
    session = sm.get_session('nursery')
    ot = session.OperationType.where({"name": TEST_OT_NAME, "category": TEST_OT_CATEGORY})[0]

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
    ot = session.OperationType.where({"name": TEST_OT_NAME, "category": TEST_OT_CATEGORY})[0]

    result = testing_tools.run_operation_test_with_random(ot, 5)
    assert result['passed'], "These operations should always pass"


def test_precondition_fail(sm, credentials):
    sm.register_session(**credentials['nursery'])
    session = sm.get_session('nursery')
    ot = session.OperationType.where({"name": TEST_PRECONDITION_OT, "category": TEST_OT_CATEGORY})[0]

    use_precondition = testing_tools.run_operation_test_with_random(ot, 5, use_precondition=True)
    no_use_precondition = testing_tools.run_operation_test_with_random(ot, 5, use_precondition=False)
    assert no_use_precondition[
        'passed'], "When `use_precondition` is True, this OperationType should fail, but is passing"
    assert not use_precondition[
        'passed'], "When `use_precondition` is False, this OperationType should pass, but is failing"


def test_batch_condition_fail(sm, credentials):
    """
    This test uses a protocol that should error out when batch size is greater than 4
    """

    sm.register_session(**credentials['nursery'])
    session = sm.get_session('nursery')
    ot = session.OperationType.where({"name": TEST_BATCH, "category": TEST_OT_CATEGORY})[0]

    batch4 = testing_tools.run_operation_test_with_random(ot, 4, use_precondition=True)
    batch5 = testing_tools.run_operation_test_with_random(ot, 5, use_precondition=True)

    assert all(
        [x.status == "done" for x in batch4['operations']]), "These operations should pass when batch size is <= 4"
    assert not all([x.status == "done" for x in batch5['operations']]), "These operations fail when batch size is > 4"
