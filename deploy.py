from rancher_ambari.rancherClient import RancherClient
from rancher_ambari.ambariClient import AmbariClient
import os
import logging
import argparse

env_name = 'Default'
stack_name = 'hdp'

def create(cluster_size):
    logging.info("Starting Ambari through Rancher deployment")


    hdp_repo_url = 'http://192.168.1.63/yum/hdp/HDP/centos7/2.x/updates/2.6.1.0'
    hdp_util_repo_url = 'http://192.168.1.63/yum/hdp/HDP-UTILS-1.1.0.21/repos/centos7'

    rancher_client = RancherClient()
    rancher_client.connect(RANCHER_URL, RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY, env_name, stack_name)

    rancher_client.create_new_stack('configs/rancher', cluster_size)

    ambari_public_ip = rancher_client.get_ambari_master_ip()

    ambari_client = AmbariClient()
    ambari_client.connect(ambari_public_ip, stack_name)

    ambari_client.create_cluster('configs/ambari', cluster_size, hdp_repo_url=hdp_repo_url, hdp_util_repo_url=hdp_util_repo_url)

def dump_config(cluster_size):
    rancher_client = RancherClient()
    rancher_client.connect(RANCHER_URL, RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY, env_name, stack_name)

    ambari_public_ip = rancher_client.get_ambari_master_ip()

    ambari_client = AmbariClient()

    ambari_client.connect(ambari_public_ip, stack_name)

    ambari_client.dump_config('configs/ambari', cluster_size)

def update_config(cluster_size):
    rancher_client = RancherClient()
    rancher_client.connect(RANCHER_URL, RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY, env_name, stack_name)
    ambari_public_ip = rancher_client.get_ambari_master_ip()

    ambari_client = AmbariClient()
    ambari_client.connect(ambari_public_ip, stack_name)

    ambari_client.update_cluster('configs/ambari', cluster_size)

def destroy():
    rancher_client = RancherClient()
    rancher_client.connect(RANCHER_URL, RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY, env_name, stack_name)
    ambari_public_ip = rancher_client.get_ambari_master_ip()

    ambari_client = AmbariClient()
    ambari_client.connect(ambari_public_ip, stack_name)

    ambari_client.stop_cluster()

    rancher_client.destroy_stack()

def stop():
    rancher_client = RancherClient()
    rancher_client.connect(RANCHER_URL, RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY, env_name, stack_name)
    ambari_public_ip = rancher_client.get_ambari_master_ip()

    ambari_client = AmbariClient()
    ambari_client.connect(ambari_public_ip, stack_name)

    ambari_client.stop_cluster()

if __name__ == "__main__":

    # logging configuration
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    # get credentials from Rancher
    RANCHER_URL=os.environ['RANCHER_URL']
    RANCHER_ACCESS_KEY=os.environ['RANCHER_ACCESS_KEY']
    RANCHER_SECRET_KEY=os.environ['RANCHER_SECRET_KEY']

    parser = argparse.ArgumentParser(description='Deploy a Hortonworks Hadoop cluster using Rancher')
    parser.add_argument('--action', dest='action', choices=['create', 'stop', 'destroy', 'dump-config', 'update-config'], required=True,
                        help='action to execute')
    parser.add_argument('--size', dest='cluster_size', type=int, default=1,
                        help='number of datanodes')

    args = parser.parse_args()

    if args.action == "create":
        create(args.cluster_size)
    elif args.action == "dump-config":
        dump_config(args.cluster_size)
    elif args.action == "update-config":
        update_config(args.cluster_size)
    elif args.action == "stop":
        stop()
    elif args.action == "destroy":
        destroy()



