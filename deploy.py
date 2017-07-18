from rancher_ambari.rancherClient import RancherClient
from rancher_ambari.ambariClient import AmbariClient
import os
import logging
import sys

logging.getLogger().addHandler(logging.StreamHandler())
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

RANCHER_URL=os.environ['RANCHER_URL']
RANCHER_ACCESS_KEY=os.environ['RANCHER_ACCESS_KEY']
RANCHER_SECRET_KEY=os.environ['RANCHER_SECRET_KEY']

logging.info("Starting Ambari through Rancher deployment")

stack_name = 'hdp'
cluster_size = 3

rancher_client = RancherClient()
rancher_client.connect(RANCHER_URL, RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY, stack_name)

rancher_client.createNewStack('docker-compose.yml', 'rancher-compose.yml', cluster_size)

ambari_public_ip = rancher_client.getAmbariMasterIp()

ambari_client = AmbariClient()

ambari_client.connect(ambari_public_ip, stack_name)

ambari_client.createCluster('blueprint.json', cluster_size)