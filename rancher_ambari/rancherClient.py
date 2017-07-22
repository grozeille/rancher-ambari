from requests import Request, Session
import yaml
import time
import logging
import os

class RancherClient:
    def __init__(self):
        pass

    def connect(self, rancher_url, rancher_access_key, rancher_secrect_key, env_name, stack_name):
        self.session = Session()
        self.session.auth = (rancher_access_key, rancher_secrect_key)
        self.session.headers.update({'Content-Type': 'application/json'})
        self.rancher_url = rancher_url

        # get the project id (environment)
        self.project_id = ''
        r = self.session.get(self.rancher_url + '/v2-beta/projects')
        r.raise_for_status()
        for item in r.json()['data']:
            if item['name'] == env_name:
                self.project_id = item['id']

        if self.project_id == '':
            raise Exception("Environment {0} not found".format(env_name))

        self.stack_id = None
        self.stack_name = stack_name
        self.getStack()

    def close(self):
        self.session.close()
        self.stack_id = None

    def getStack(self):

        if self.stack_id != None:
            return True

        r = self.session.get(
            self.rancher_url + '/v2-beta/projects/{0}/stacks/?name={1}'.format(self.project_id, self.stack_name))

        if r.status_code == 404:
            return False

        r.raise_for_status()
        result = r.json()
        if len(result['data']) == 1:
            self.stack_id = result['data'][0]['id']
            return True
        else:
            return False

    def createNewStack(self, config_folder, cluster_size):

        if self.getStack() == True:
            logging.info("Stack already created, skip")
            return

        logging.info("Creating a new stack for Ambari")
        # create the new stack
        new_stack_request_data = {}
        new_stack_request_data['name'] = self.stack_name

        docker_compose_file = os.path.join(config_folder, 'docker-compose.yml')
        rancher_compose_file = os.path.join(config_folder, 'rancher-compose.yml')

        with open(docker_compose_file, 'r') as file:
            docker_compose = file.read()
            new_stack_request_data['dockerCompose'] = docker_compose

        with open(rancher_compose_file, 'r') as file:
            rancher_compose_yml = yaml.load(file)
            rancher_compose_yml['services']['ambari-agent-datanode']['scale'] = cluster_size
            rancher_compose = yaml.dump(rancher_compose_yml)
            new_stack_request_data['rancherCompose'] = rancher_compose

        new_stack_request_data['startOnCreate'] = True

        r = self.session.post(self.rancher_url + '/v2-beta/projects/{0}/stacks'.format(self.project_id), json=new_stack_request_data)

        r.raise_for_status()
        json_result = r.json()
        self.stack_id = json_result['id']

        logging.info("Waiting stack to be ready")
        # wait for the healthy state
        stack_health_state = ''
        time.sleep(15)
        while stack_health_state != 'healthy':
            time.sleep(10)
            r = self.session.get(self.rancher_url+ '/v2-beta/projects/{0}/stacks/{1}'.format(self.project_id, self.stack_id))

            r.raise_for_status()
            json_result = r.json()
            stack_health_state = json_result['healthState']
            logging.info("Stack state: {0}".format(stack_health_state))

    def getAmbariMasterIp(self):

        if self.getStack() == False:
            return None

        # get the ambari-server public IP
        r = self.session.get(self.rancher_url+ '/v2-beta/projects/{0}/stacks/{1}/services'.format(self.project_id, self.stack_id))
        r.raise_for_status()

        ambari_public_ip = ''
        for service in r.json()['data']:
            if service['name'] == 'ambari-server':
                ambari_public_ip = service['publicEndpoints'][0]['ipAddress']

        return ambari_public_ip
