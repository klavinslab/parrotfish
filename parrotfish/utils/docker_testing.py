# TEST REHYDRATE PRIMER

from pydent import AqSession 
# OPEN A SESSION
session = AqSession('neptune', 'aquarium', 'http://34.216.130.134:3000/')

# POPULATE WITH DATA
primer_st = session.SampleType.find_by_name('Primer')

# get that primer sample
primer = None
try:
    primer_data = {
      'name': 'Test Primer',
      'project': 'trident',
      'sample_type_id': primer_st.id,
      'user_id': session.current_user.id
    }
    primer = session.Sample.load(primer_data)
    primer.save()
    print('Created new Sample "{}"'.format(primer.name))
except:
    primer = session.Sample.find_by_name('Test Primer')
    print('Loaded existing Sample "{}"'.format(primer.name))

# get that primer primer_ot
primer_ot = session.ObjectType.find_by_name('Lyophilized Primer')
primer_item = next((item for item in session.Item.where({
  'sample_id': primer.id,
  'object_type_id': primer_ot.id
}) if item.location != 'deleted'), None)

if primer_item is None:
    primer_item = session.Item.load({
      'sample_id': primer.id,
      'object_type_id': primer_ot.id
    })
    primer_item.make()
    print('Created new Item {}'.format(primer_item.id))
else:
    print('Loaded existing Item {}'.format(primer_item.id))

# submit single-operation plan
rehydrate_ot = session.OperationType.find(185)
rehydrate = rehydrate_ot.instance()
rehydrate.x = rehydrate.y = rehydrate.parent_id = rehydrate.parent = 0
rehydrate.set_input('Primer', sample=primer, item=primer_item)
rehydrate.set_output('Primer Aliquot', sample=primer)
rehydrate.set_output('Primer Stock', sample=primer)

budget = session.Budget.find_by_name('First Budget')
plan = session.Plan.load({
  'name': "Rehydrate Primer Test",
  'layout': {'wires': None}})
plan.add_operation(rehydrate)
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

# debug plan
session.utils.batch_operations({'operation_ids': [op.id for op in plan.operations]})
print('op batched')
op = plan.operations[0]
job = op.jobs[0]
print('got op and job')
try:
    session.utils.job_debug(job.id)
except:
    pass
print('job debugged')

# return result
op.reload(session.Operation.find(op.id))
print('JOB STATUS: {}'.format(op.status))

print('All done :)')
