"""
Functions for running Aquarium specific server-side tests
"""

import json

from parrotfish.utils import sanitize_filename


def generate_test_data(ot_dict):
    """
    Builds JSON-formatted string for testing data

    :param ot_dict: an :class:`ObjectType` as a dictionary
    :type ot_dict: dict
    :return: testing data
    :rtype: str
    """
    num_ops = 3

    # Link to Sample Types and Object Types
    sample_types = _get_types('sample_type', ot_dict)
    object_types = _get_types('object_type', ot_dict)

    # Generate records from Field Types of op type
    samples = []
    items = []
    operations = []
    for idx in range(num_ops):
        # Determine routing for operation
        fts_by_route = {}
        for ft in ot_dict['field_types']:
            route = ft['routing']
            fts_by_route.setdefault(route, []).append(ft)

        # Build Field Types by route
        op_inputs = []
        op_outputs = []
        for route in fts_by_route:
            # Sample Type
            st_names = _names_from_fts('sample_type', ot_dict['field_types'])
            st_tag = ('{}_st'.format(st_names[0].lower())
                      if len(st_names) > 0 else None)

            # Sample
            s_tag = '{}_samp{}'.format(route, idx)
            s_name = 'Test {} {}'.format(route, idx)
            s = {
                'tag': s_tag,
                'data': {
                    'name': s_name,
                    'project': 'trident',
                    'sample_type': st_tag,
                    'user_id': 1
                }
            }
            samples.append(s)

            # Field Types
            for ft in fts_by_route[route]:
                ft_name = ft['name']
                role = ft['role']

                # Object Type
                ot_names = _names_from_fts(
                    'object_type', ot_dict['field_types'])
                ot_tag = ('{}_ot'.format(ot_names[0].lower())
                          if len(ot_names) > 0 else None)

                # Items
                if role == 'input':
                    i_tag = '{}_item{}'.format(ft_name, idx)
                    i = {
                        'tag': i_tag,
                        'data': {
                            'sample': s_tag,
                            'object_type': ot_tag
                        }
                    }
                    items.append(i)

                # Op inputs and outputs
                if role == 'input':
                    op_inputs.append({
                        'name': ft_name,
                        'sample': s_tag,
                        'item': i_tag
                    })
                else:
                    op_outputs.append({
                        'name': ft_name,
                        'sample': s_tag
                    })

        # Operations
        o_tag = 'op{}'.format(idx)
        o = {
            'tag': o_tag,
            'data': {
                'inputs': op_inputs,
                'outputs': op_outputs
            }
        }

        operations.append(o)

    data = {
        'records': {
            'object_types': object_types,
            'sample_types': sample_types,
            'samples': samples,
            'items': items,
            'operations': operations
        },
        'plan': {
            'operations': [op['tag'] for op in operations]
        }
    }
    return json.dumps(data, indent=2)


def _get_types(record_type, ot_dict):
    records = []
    names = _names_from_fts(record_type, ot_dict['field_types'])
    for name in names:
        suff = 'st' if 'sample' in record_type else 'ot'
        tag = '{}_{}'.format(name.lower(), suff)

        if tag not in [record['tag'] for record in records]:
            records.append({
                'tag': tag,
                'source': '{}s/{}.json'.format(record_type, name)
            })

    return records


def _names_from_fts(record_type, fts):
    return [sanitize_filename(aft[record_type]['name'])
            for ft in fts
            for aft in ft['allowable_field_types']
            if aft[record_type]]


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
    test_ops_data = session.utils.aqhttp.get(
        'operation_types/{}/random/{}'.format(ot.id, num_ops))
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

    parsed_result['passed'] = \
        parsed_result['job'].state[-1]['operation'] == 'complete'

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
