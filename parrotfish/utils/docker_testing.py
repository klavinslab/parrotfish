import json as j
import os
import subprocess
from pydent import AqSession


def get_records(session, name, records, record_names):
    record_dict = {}

    for model_string in record_names:
        for record_info in records[model_string]:
            data = record_info['data']
            new_data = format_data(data, record_dict)
            new_record = make_record(
                session, name, model_string, new_data, record_dict)

            record_dict[record_info['tag']] = new_record

    return record_dict


def format_data(data, record_dict):
    new_data = {}
    for attr in data:
        tag = data[attr]
        if type(tag) is str and tag in record_dict:
            record_id = record_dict[tag].id
            new_data[attr + '_id'] = record_id
        else:
            new_data[attr] = data[attr]

    return new_data


def make_record(session, name, model_string, data, record_dict):
    model_name = model_string[:-1]
    record = None

    if model_name == "sample":
        try:
            record = session.Sample.load(data)
            record.save()
        except Exception:
            record = session.Sample.find_by_name(data['name'])
    elif model_name == "item":
        record = session.Item.load(data)
        record.make()
    elif model_name == "operation":
        ot = session.OperationType.find_by_name(name)
        record = ot.instance()
        record.x = record.y = record.parent_id = record.parent = 0

        for in_data in data['inputs']:
            name = in_data['name']
            sample = record_dict[in_data['sample']]
            item = record_dict[in_data['item']]
            record.set_input(name, sample=sample, item=item)

        for out_data in data['outputs']:
            name = out_data['name']
            sample = record_dict[out_data['sample']]
            record.set_output(name, sample=sample)
    else:
        raise Exception(
            'Malformed data: {} is not a valid model name'.format(model_name))

    return record


def submit_plan(session, protocol, test_data):
    # GET THOSE RECORDS
    record_names = ['samples', 'items', 'operations']
    record_dict = get_records(
        session, protocol.name, test_data['records'], record_names)

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
    plan.show()

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
    print('JOB STATUS: {}'.format(op.status))

    return {
            'success': op.status == 'done',
            'errors': []
        }


def start_container(reset):
    # RUN THIS DOCKER CONTAINER
    command = 'sudo docker ps -aqf ancestor=aq'
    check_running = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = check_running.communicate()
    running = len(output) > 0

    if reset or not running:
        here = os.path.abspath(os.path.dirname(__file__))
        subprocess.call(['bash', '{}/docker_container.sh'.format(here), 'run'])
        return True

    return False


def stop_container():
    # KILL THIS DOCKER CONTAINER
    here = os.path.abspath(os.path.dirname(__file__))
    subprocess.call(['bash', '{}/docker_container.sh'.format(here), 'kill'])


def test_protocol(protocol):
    # OPEN A SESSION
    session = AqSession('neptune', 'aquarium', 'http://localhost:3001/')

    # READ THAT JSON
    test_data = None
    with protocol.open_file('test_data.json', mode='r') as f:
        test_data = j.load(f)

    # SUBMIT THAT PLAN
    result = submit_plan(session, protocol, test_data)

    return result
