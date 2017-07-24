from rancher_ambari.rancherClient import RancherClient
from rancher_ambari.ambariClient import AmbariClient
import os
import logging
import sys

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

env_name = 'Default'
stack_name = 'hdp'
cluster_size = 1

hdp_repo_url = 'http://192.168.1.63/yum/hdp/HDP/centos7/2.x/updates/2.6.1.0'
hdp_util_repo_url = 'http://192.168.1.63/yum/hdp/HDP-UTILS-1.1.0.21/repos/centos7'

rancher_client = RancherClient()
rancher_client.connect(RANCHER_URL, RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY, env_name, stack_name)

rancher_client.create_new_stack('configs/rancher', cluster_size)

ambari_public_ip = rancher_client.get_ambari_master_ip()

ambari_client = AmbariClient()

ambari_client.connect(ambari_public_ip, stack_name)

#ambari_client.create_cluster('configs/ambari', cluster_size, hdp_repo_url=hdp_repo_url, hdp_util_repo_url=hdp_util_repo_url)

ambari_client.dump_config('configs/ambari', cluster_size)

#ambari_client.update_cluster('configs/ambari', cluster_size)