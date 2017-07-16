from requests import Request, Session
import time
import yaml
import sys
import os

RANCHER_URL=os.environ['RANCHER_URL']
RANCHER_ACCESS_KEY=os.environ['RANCHER_ACCESS_KEY']
RANCHER_SECRET_KEY=os.environ['RANCHER_SECRET_KEY']

stack_name = 'hdp2'

s = Session()
s.auth = (RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY)
s.headers.update({'Content-Type': 'application/json'})

# get the project id (environment)
project_id = ''
r = s.get(RANCHER_URL+'/v2-beta/projects')
r.raise_for_status()
for item in r.json()['data']:
    if item['name'] == 'default':
        project_id = item['id']


# create the new stack
new_stack_request_data = {}
new_stack_request_data['name'] = stack_name

with open('docker-compose.yml', 'r') as file:
    #docker_compose_yml = yaml.load(file)
    #docker_compose = yaml.dump(docker_compose_yml)
    docker_compose = file.read()
    new_stack_request_data['dockerCompose'] = docker_compose

with open('rancher-compose.yml', 'r') as file:
    rancher_compose = file.read()
    new_stack_request_data['rancherCompose'] = rancher_compose

new_stack_request_data['startOnCreate'] = True

r = s.post(RANCHER_URL+'/v2-beta/projects/{0}/stacks'.format(project_id), json = new_stack_request_data)

r.raise_for_status()
json_result = r.json()
stack_id = json_result['id']

# wait for the healthy state
stack_health_state = ''
time.sleep( 15 )
while stack_health_state != 'healthy':
    time.sleep( 5 )
    r = s.get(RANCHER_URL+'/v2-beta/projects/{0}/stacks/{1}'.format(project_id, stack_id))

    r.raise_for_status()
    json_result = r.json()
    stack_health_state = json_result['healthState']
    print "Stack state: {0}".format(stack_health_state)

# get the ambari-server public IP
r = s.get(RANCHER_URL+'/v2-beta/projects/{0}/stacks/{1}/services'.format(project_id, stack_id))
r.raise_for_status()
json_result = r.json()

ambari_public_ip = ''
for service in r.json()['data']:
    if service['name'] == 'ambari-server':
        ambari_public_ip = service['publicEndpoints'][0]['ipAddress']

print "Creating new Hortonworks cluster with Ambari Master : {0}".format(ambari_public_ip)