"""
Methods for testing Operation Types in a Docker container
"""

import json as j
import os
import subprocess
from pydent import AqSession


def get_records(session, protocol, records, record_names):
    """
    Generates a dictionary of all new records by their tag

    :param session: session with container
    :type session: AqSession
    :param protocol: directory that manages the protocol
    :type protocol: ODir
    :return: dictionary of all records by tag
    :rtype: dict
    """
    record_dict = {}

    for model_string in record_names:
        for record_info in records[model_string]:
            if 'data' in record_info:
                data = record_info['data']
            else:
                with protocol.open_file(record_info['source'], mode='r') as f:
                    data = j.load(f)

            # Format data with tags
            new_data = format_data(data, record_dict)

            if model_string == "operation_types":
                for ft in new_data['field_types']:
                    ft['allowable_field_types'] = [
                        format_data(aft, record_dict)
                        for aft in ft['allowable_field_types']
                    ]

            # Make records with Trident
            new_record = make_record(
                session, protocol.name, model_string, new_data, record_dict)

            record_dict[record_info['tag']] = new_record

    return record_dict


def format_data(data, record_dict):
    """
    Replaces tags in given data with corresponding record ids

    :param data: raw data for a given record
    :type data: dict
    :param record_dict: dictionary of all records by tag
    :type record_dict: dict
    :return: formatted data
    :rtype: dict
    """
    new_data = {}
    for attr in data:
        tag = data[attr]
        if type(tag) is str and tag in record_dict:
            record_id = record_dict[tag].id
            new_data[attr[:-4] + '_id'] = record_id
        else:
            new_data[attr] = data[attr]

    return new_data


def make_record(session, name, model_string, data, record_dict):
    """
    Makes a new record of the given model (or loads an existing one
    if applicable)

    :param session: session with container
    :type session: AqSession
    :param name: name of the :class:`OperationType`
    :type name: str
    :param model_string: name of the model
    :type model_string: str
    :param data: formatted data for given record
    :type data: dict
    :param record_dict: dictionary of all records by tag
    :type record_dict: dict
    :return: record made from data
    :rtype: ModelBase
    """
    model_name = model_string[:-1]
    record = None

    if model_name == "sample_type":
        record = session.SampleType.load(data)
        record.save()
    elif model_name == "object_type":
        record = session.ObjectType.load(data)
        record.save()
    elif model_name == "sample":
        try:
            record = session.Sample.load(data)
            record.save()
        except Exception:
            record = session.Sample.find_by_name(data['name'])
    elif model_name == "item":
        record = session.Item.load(data)
        record.make()
    elif model_name == "operation":
        ot = record_dict['ot']
        record = ot.instance()
        record.x = record.y = record.parent_id = record.parent = 0

        for in_data in data['inputs']:
            name = in_data['name']
            sample = record_dict[in_data['sample_tag']]
            item = record_dict[in_data['item_tag']]
            record.set_input(name, sample=sample, item=item)

        for out_data in data['outputs']:
            name = out_data['name']
            sample = record_dict[out_data['sample_tag']]
            record.set_output(name, sample=sample)
    elif model_name == "operation_type":
        # data['name'] = 'hullabaloo25'
        record = session.OperationType.load(data)
        try:
            record.save()
        except Exception:
            # Trident errors even though Operation Type is successfully created
            # TODO Handle creating Operation Types (and Field Types and
            #      Allowable Field Types) more cleanly (e.g., many problems
            #      arise from the fact that we can't 'reload' the OT record
            #      upon creating it on a server; 'id's are incorrect).
            record = session.OperationType.find_by_name(record.name)

    else:
        raise Exception(
            'Malformed data: {} is not a valid model name'.format(model_name))

    return record


def test_protocol(protocol, record_dict):
    """
    Submits a plan to container given test data

    :param session: session with container
    :type session: AqSession
    :param protocol: directory that manages the protocol
    :type protocol: ODir
    :param record_dict: dictionary of all records by tag
    :type record_dict: dict
    :return: plan information (success status and errors)
    :rtype: dict
    """
    # GET THINE SESSION
    session = record_dict['ot'].session

    # READ THAT JSON
    test_data = None
    with protocol.open_file('testing/data.json', mode='r') as f:
        test_data = j.load(f)

    # SUBMIT THAT PLAN
    plan = session.Plan.load({
        'name': '{} Test'.format(protocol.name),
        'layout': {'wires': None}})
    for op_tag in test_data['plan']['operations']:
        op = record_dict[op_tag]
        plan.add_operation(op)

    plan.create()
    plan.estimate_cost()
    plan.validate()

    plan.submit(session.current_user, session.current_user.budgets[0])

    # DEBUG THAT PLAN
    session.utils.batch_operations(
            {'operation_ids': [op.id for op in plan.operations]})
    op = plan.operations[0]
    job = op.jobs[0]
    try:
        session.utils.job_debug(job.id)
    except Exception:
        pass

    # return result
    op.reload(session.Operation.find(op.id))

    return {
        'success': op.status == 'done',
        'plan_url': '{}launcher?plan_id={}'.format(session.url, plan.id)
    }


def load_data(protocol):
    """
    Open a session with running container

    :param protocol: directory that manages the protocol
    :type protocol: ODir
    :return: dictionary of all records by tag
    :rtype: dict
    """
    # OPEN A SESSION
    session = AqSession('neptune', 'aquarium', 'http://localhost:3001/')

    # READ THAT JSON
    # protocol = environment.get_protocol_dir(cat_name, prot_name)
    test_data = None
    with protocol.open_file('testing/data.json', mode='r') as f:
        test_data = j.load(f)

    # GET THOSE RECORDS
    record_names = [
        'sample_types',
        'object_types',
        'operation_types',
        'samples',
        'items',
        'operations'
    ]
    record_dict = get_records(
        session, protocol, test_data['records'], record_names)

    return record_dict


def start_container(reset, cid):
    """
    Start a Docker container

    :param reset: kill the running container if one exists
    :type reset: bool
    :return: whether a new container was started
    :rtype: bool
    """
    # CHECK IF DOCKER CONTAINER IS RUNNING ALREADY
    if cid == '':
        running = False
    else:
        command = 'sudo docker ps -aq'
        check_running = subprocess.Popen(
            command.split(), stdout=subprocess.PIPE)
        output, error = check_running.communicate()
        running_ids = [rid.decode('utf-8') for rid in output.split(b'\n')]

        running = cid in running_ids
        if not running:
            cid = ''

    if reset or not running:
        # RUN THIS DOCKER CONTAINER
        print('Starting Aquarium container...')
        here = os.path.abspath(os.path.dirname(__file__))
        start = subprocess.Popen([
            'bash',
            '{}/docker_container.sh'.format(here),
            'run',
            str(cid)
        ], stdout=subprocess.PIPE)
        output, error = start.communicate()
        cid = output.split(b'\n')[-2].decode('utf-8')

        return {
            'success': True,
            'id': cid
        }

    return {
        'success': False,
        'id': cid
    }


def stop_container(cid):
    """ Stop a Docker container """
    # KILL THIS DOCKER CONTAINER
    here = os.path.abspath(os.path.dirname(__file__))
    subprocess.call([
        'bash',
        '{}/docker_container.sh'.format(here),
        'kill',
        cid,
    ])
