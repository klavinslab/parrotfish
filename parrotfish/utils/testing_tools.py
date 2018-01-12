"""
Functions for running Aquarium specific server-side tests
"""

from pydent.models import OperationType
import json


def generate_random_operations(ot, num_ops):
    """
    Generates new random operations for testing purposes

    :param ot: OperationType to generate new random Operations
    :type ot: OperationType
    :param num_ops: number of operations to generate
    :type num_ops: int
    :return: list of Operation
    :rtype: list
    """
    session = ot._session
    test_ops_data = session.utils.aqhttp.get(f'operation_types/{ot.id}/random/{num_ops}')
    return test_ops_data


def run_operation_type_test(ot, testing_operations, use_precondition=False):
    """
    Runs a test of an OperationType using a list of operations

    :param ot: OperationType to test
    :type ot: OperationType
    :param testing_operations:
    :type testing_operations:
    :param use_precondition:
    :type use_precondition:
    :return: testing result
    :rtype: dict
    """

    session = ot._session

    # create data for POST
    data = ot.dump()
    data['test_operations'] = testing_operations
    data['use_precondition'] = use_precondition

    # run tests
    result = session.utils.aqhttp.post('operation_types/test', json_data=data)

    parsed_result = {
        'operations': session.Operation.load(result['operations']),
        'plans': session.Operation.load(result['plans']),
        'job': session.Operation.load(result['job'])
    }
    parsed_result['job'].state = json.loads(parsed_result['job'].state)

    parsed_result['passed'] = parsed_result['job'].state[-1]['operation'] == 'complete'

    return parsed_result


def run_operation_test_with_random(ot, num_ops, use_precondition=False):
    """
    Tests an operation type using randomly generated operations

    :param ot: OperationType to test
    :type ot:   OperationType
    :param num_ops: number of operations to generate
    :type num_ops:  int
    :param use_precondition: whether to use the precondition
    :type use_precondition: boolean
    :return: testing result
    :rtype: dict
    """
    ops = generate_random_operations(ot, num_ops)
    return run_operation_type_test(ot, ops, use_precondition=use_precondition)
