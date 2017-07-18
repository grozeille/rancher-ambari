from requests import Request, Session
import sys
import time
import json
import logging

class AmbariClient:
    def __init__(self):
        pass

    def connect(self, ambari_ip, stack_name):
        self.ambari_url = 'http://{0}:8081'.format(ambari_ip)
        self.session = Session()
        self.session.auth = ("admin", "admin")
        self.session.headers.update({
            'X-Requested-By': 'admin'
        })
        self.stack_name = stack_name

    def createCluster(self, blueprint_file, cluster_size):

        # wait for ambari to be ready
        while True:
            ready = self.checkForAmbari()
            time.sleep(5)
            if ready:
                break

        logging.info("Ambari Ready")

        with open(blueprint_file, 'r', encoding='UTF8') as file:
            blueprint_json = json.load(file)

        blueprint_name = 'blueprint'

        r = self.session.post(self.ambari_url + '/api/v1/blueprints/' + blueprint_name, data=json.dumps(blueprint_json))
        r.raise_for_status()
        logging.info("Blueprint uploaded")

        host_groups = [
            { "name": "namenode", "size": 1 },
            { "name": "secondarynamenode", "size": 1 },
            { "name": "resourcemanager", "size": 1 },
            { "name": "zookeeper", "size":1 },
            { "name": "datanode", "size": cluster_size },
        ]

        cluster = {
            'blueprint': blueprint_name,
            'default_password': 'admin',
            'host_groups': []
        }

        for host_group_name in host_groups:
            host_group = {
                'name': 'host_group_'+host_group_name['name'],
                'hosts': []
            }

            for cpt in range(1, host_group_name['size']+1):
                host_group['hosts'].append({'fqdn': '{0}-ambari-agent-{1}-{2}'.format(self.stack_name, host_group_name['name'], cpt)})

            cluster['host_groups'].append(host_group)


        r = self.session.post(self.ambari_url + '/api/v1/clusters/' + self.stack_name, data=json.dumps(cluster))
        r.raise_for_status()
        logging.info("Cluster creation submited")

        clusterRequest = r.json()

        if clusterRequest['Requests']['status'] != 'Accepted':
            logging.error(clusterRequest['Requests']['status'])
            sys.exit(1)

        time.sleep(20)

        while True:
            ready = self.checkForClusterRequest(clusterRequest['Requests']['id'])
            time.sleep(10)
            if ready:
                break

        logging.info("Cluster Ready")

        pass

    def checkForAmbari(self):
        "wait for ambari to be ready"
        logging.info("Wait for ambari to be ready")
        try:
            r = self.session.get(self.ambari_url + '/api/v1/clusters')
            if r.status_code != 200:
                logging.info("Status code" + str(r.status_code))
                return False
            else:
                return True
        except:
            logging.error("Unexpected error:", sys.exc_info()[1])
            return False

    def checkForClusterRequest(self, requestId):
        "wait for cluster to be ready"
        logging.info("Wait for cluster to be ready")
        r = self.session.get(self.ambari_url + '/api/v1/clusters/' + self.stack_name + '/requests/' + str(requestId))
        r.raise_for_status()
        requestDetail = r.json()
        if requestDetail['Requests']['request_status'] == 'IN_PROGRESS' or requestDetail['Requests']['task_count'] == 0:
            return False
        else:
            return True