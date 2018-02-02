import json as j
from pydent import AqSession


json = None
with open('./data.json') as f:
    json = j.loads(f.read())


def get_records(session, json):
    record_dict = {}
    tag_dict = {}

    for model_string in json:
        new_records = []
        for record_info in json[model_string]:
            data = record_info['data']
            new_data = format_data(data, tag_dict)
            new_record = make_record(session, model_string, new_data)

            new_records.append(new_record)
            tag_dict[record_info['tag']] = new_record.id

        record_dict[model_string] = new_records

    return record_dict


def format_data(data, tag_dict):
    new_data = {}
    for attr in data:
        tag = data[attr]
        if tag in tag_dict:
            record_id = tag_dict[tag]
            new_data[attr + '_id'] = record_id
        else:
            new_data[attr] = data[attr]

    return new_data


def make_record(session, model_string, data):
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
    else:
        raise Exception(
            'Malformed data: {} is not a valid model name'.format(model_name))

    return record


# OPEN A SESSION
session = AqSession('neptune', 'aquarium', 'http://34.216.130.134:3000/')

# GET THOSE RECORDS
record_dict = get_records(session, json)
