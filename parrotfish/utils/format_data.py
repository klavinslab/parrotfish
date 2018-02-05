import json as j
from pydent import AqSession


def get_records(session, records):
    record_dict = {}

    for model_string in records:
        for record_info in records[model_string]:
            data = record_info['data']
            new_data = format_data(data, record_dict)
            new_record = make_record(
                session, model_string, new_data, record_dict)

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


def make_record(session, model_string, data, record_dict):
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
        ot = session.OperationType.find(185)
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


# OPEN A SESSION
session = AqSession('neptune', 'aquarium', 'http://34.216.130.134:3000/')


# READ THAT JSON
json = None
with open('./data2.json') as f:
    json = j.loads(f.read())


# GET THOSE RECORDS
record_dict = get_records(session, json['records'])
print(record_dict)


# SUBMIT THAT PLAN
plan = session.Plan.load({
    'name': "Rehydrate Primer Test",
    'layout': {'wires': None}})
for op_tag in json['plan']['operations']:
    op = record_dict[op_tag]
    print(op)
    plan.add_operation(op)

print(plan.operations)
print('added operation')
plan.create()
print('created plan')
plan.estimate_cost()
print('estimated cost')
plan.validate()
print('validated plan')
plan.show()
print('showed plan')

plan.submit(session.current_user, session.current_user.budgets[0])

# DEBUG THAT PLAN
session.utils.batch_operations(
        {'operation_ids': [op.id for op in plan.operations]})
print('op batched')
op = plan.operations[0]
job = op.jobs[0]
print('got op and job')
try:
    session.utils.job_debug(job.id)
except Exception:
    pass
print('job debugged')

# return result
op.reload(session.Operation.find(op.id))
print('JOB STATUS: {}'.format(op.status))

print('All done :)')
