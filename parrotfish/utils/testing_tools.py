"""
Functions for running Aquarium specific server-side tests
"""

import json

from parrotfish.utils import sanitize_filename


def tagify(data, session):
    data = _tagify_single(data, session)

    if ('field_types' in data and
            data['field_types'][0]['parent_class'] == 'OperationType'):
        fts = []
        for ft in data['field_types']:
            ft['allowable_field_types'] = [
                _tagify_single(aft, session)
                for aft in ft['allowable_field_types']
            ]
            fts.append(ft)
        data['field_types'] = fts

    return data


def _tagify_single(data, session):
    rec_types = [
        ('sample_type', 'st'),
        ('object_type', 'ot'),
    ]
    for rec_type in rec_types:
        id_key = '{}_id'.format(rec_type[0])
        tag_key = '{}_tag'.format(rec_type[0])
        if id_key in data and data[id_key]:
            rec = None
            if rec_type[0] == 'sample_type':
                rec = session.SampleType.find(data[id_key])
            elif rec_type[0] == 'object_type':
                rec = session.ObjectType.find(data[id_key])
            data[tag_key] = '{}_{}'.format(rec.name.lower(), rec_type[1])
            data.pop(id_key)

    return data


def generate_test_data(ot_dict):
    """
    Builds JSON-formatted string for testing data

    :param ot_dict: an :class:`OperationType` as a dictionary
    :type ot_dict: dict
    :return: testing data
    :rtype: str
    """
    num_ops = 3

    # Link to Sample Types and Object Types
    sample_types = _get_types('sample_type', ot_dict['field_types'])
    object_types = _get_types('object_type', ot_dict['field_types'])

    # Link to Operation Type
    operation_types = [
        {
            'tag': 'ot',
            'source': '{}.json'.format(ot_dict['name'])
        }
    ]

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
            try:
                afts = fts_by_route[route][0]['allowable_field_types']
                st_tag = afts[0]['sample_type_tag']
            except IndexError:
                # Parameter input
                st_tag = None
            except KeyError:
                # No Sample Type exists (like a gel box or collection)
                st_tag = None

            # Sample
            s_tag = '{}_samp{}'.format(route, idx)
            s_name = 'Test {} {} for {}'.format(route, idx, ot_dict['name'])
            s = {
                'tag': s_tag,
                'data': {
                    'name': s_name,
                    'project': 'trident',
                    'sample_type_tag': st_tag,
                    'user_id': 1
                }
            }
            samples.append(s)

            # Field Types
            for ft in fts_by_route[route]:
                ft_name = ft['name']
                role = ft['role']

                # Object Type
                try:
                    ot_tag = ft['allowable_field_types'][0]['object_type_tag']
                except IndexError:
                    # Parameter input
                    st_tag = None

                # Items
                if role == 'input':
                    i_tag = '{}_item{}'.format(ft_name, idx)
                    i = {
                        'tag': i_tag,
                        'data': {
                            'sample_tag': s_tag,
                            'object_type_tag': ot_tag
                        }
                    }
                    items.append(i)

                # Op inputs and outputs
                if role == 'input':
                    op_inputs.append({
                        'name': ft_name,
                        'sample_tag': s_tag,
                        'item_tag': i_tag
                    })
                else:
                    op_outputs.append({
                        'name': ft_name,
                        'sample_tag': s_tag
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
            'operation_types': operation_types,
            'samples': samples,
            'items': items,
            'operations': operations
        },
        'plan': {
            'operations': [op['tag'] for op in operations]
        }
    }
    return json.dumps(data, indent=2)


def _get_types(model_name, fts):
    """
    Creates a list of data for :class:`SampleType` or :class:`ObjectType`

    :param model_name: name of the desired model
    :type model_name: str
    :param fts: :class:`FieldType`s as a list of dicts
    :type fts: list
    :return: a list of record data
    :rtype: list
    """
    records = []
    names = _names_from_fts(model_name, fts)
    for name in names:
        suffix = 'st' if 'sample' in model_name else 'ot'
        tag = '{}_{}'.format(name.lower(), suffix)

        if tag not in [record['tag'] for record in records]:
            records.append({
                'tag': tag,
                'source': '{}s/{}.json'.format(model_name, name)
            })

    return records


def _names_from_fts(model_name, fts):
    """
    Creates a list of all of the names of records of a given model

    :param model_name: name of the desired model
    :type model_name: str
    :param fts: :class:`FieldType`s as a list of dicts
    :type fts: list
    :return: a list of record names in fts of model_name
    :rtype: list
    """
    return [sanitize_filename(aft[model_name]['name'])
            for ft in fts
            for aft in ft['allowable_field_types']
            if aft[model_name]]


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
