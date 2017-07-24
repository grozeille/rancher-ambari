from requests import Request, Session
import sys
import time
import json
import logging
import os

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

    def create_cluster(self, config_folder, cluster_size, hdp_repo_url=None, hdp_util_repo_url=None):

        blueprint_file = os.path.join(config_folder, 'blueprint.json')

        # wait for ambari to be ready
        while True:
            ready = self.check_for_ambari()
            time.sleep(10)
            if ready:
                break

        logging.info("Ambari Ready")

        if hdp_repo_url != None:
            logging.info("Updating HDP repository")
            repositories = {
                "Repositories": {
                    "base_url": hdp_repo_url,
                    "verify_base_url": True
                }
            }
            r = self.session.put(
                self.ambari_url + '/api/v1/stacks/HDP/versions/2.6/operating_systems/redhat7/repositories/HDP-2.6',
                data=json.dumps(repositories))
            r.raise_for_status()

        if hdp_util_repo_url != None:
            logging.info("Updating HDP Util repository")
            repositories = {
                "Repositories": {
                    "base_url": hdp_util_repo_url,
                    "verify_base_url": True
                }
            }
            r = self.session.put(
                self.ambari_url + '/api/v1/stacks/HDP/versions/2.6/operating_systems/redhat7/repositories/HDP-UTILS-1.1.0.21',
                data=json.dumps(repositories))
            r.raise_for_status()

        blueprint_json = self.build_config(config_folder)

        blueprint_name = 'blueprint'

        r = self.session.get(self.ambari_url + '/api/v1/blueprints/' + blueprint_name)
        if r.status_code == 200:
            r = self.session.delete(self.ambari_url + '/api/v1/blueprints/' + blueprint_name)

        r = self.session.post(self.ambari_url + '/api/v1/blueprints/' + blueprint_name, data=json.dumps(blueprint_json))
        r.raise_for_status()
        logging.info("Blueprint uploaded")

        cluster = {
            'blueprint': blueprint_name,
            'default_password': 'admin',
            'host_groups': self.build_host_groups(cluster_size)
        }

        r = self.session.post(self.ambari_url + '/api/v1/clusters/' + self.stack_name, data=json.dumps(cluster))
        r.raise_for_status()
        logging.info("Cluster creation submited")

        clusterRequest = r.json()

        if clusterRequest['Requests']['status'] != 'Accepted':
            logging.error(clusterRequest['Requests']['status'])
            raise Exception("Cluster creation request with bad status: "+clusterRequest['Requests']['status'])

        time.sleep(20)

        while True:
            ready = self.check_for_cluster_request(clusterRequest['Requests']['id'])
            time.sleep(10)
            if ready:
                break

        logging.info("Cluster Ready")

    def build_host_groups(self, cluster_size):

        result = []

        host_groups = [
            {"name": "namenode", "size": 1},
            {"name": "secondarynamenode", "size": 1},
            {"name": "resourcemanager", "size": 1},
            {"name": "zookeeper", "size": 1},
            {"name": "datanode", "size": cluster_size},
        ]

        for host_group_name in host_groups:
            host_group = {
                'name': 'host_group_' + host_group_name['name'],
                'hosts': []
            }

            for cpt in range(1, host_group_name['size'] + 1):
                host_group['hosts'].append(
                    {'fqdn': '{0}-ambari-agent-{1}-{2}'.format(self.stack_name, host_group_name['name'], cpt)})

                result.append(host_group)

        return result

    def update_cluster(self, config_folder, cluster_size):

        r = self.session.get(self.ambari_url+"/api/v1/clusters/hdp?fields=Clusters/desired_configs,services")
        r.raise_for_status()
        desired_configs = r.json()["Clusters"]["desired_configs"]

        blueprint = self.build_config(config_folder)

        new_configs = {}
        for config_item in blueprint["configurations"]:
            config_key = list(config_item.keys())[0]
            new_configs[config_key] = config_item[config_key]

        service_configs = self.get_service_configs()

        installed_service_configs = {}
        for service in r.json()["services"]:
            service_name = service["ServiceInfo"]["service_name"]
            installed_service_configs[service_name] = service_configs[service_name]

        current_ts = int(time.time()*1000)

        for service in installed_service_configs:
            for configuration in installed_service_configs[service]:
                desired_config = desired_configs[configuration]
                tag = desired_config["tag"]
                r = self.session.get(self.ambari_url+"/api/v1/clusters/{0}/configurations?type={1}&tag={2}".format(self.stack_name, configuration, tag))
                r.raise_for_status()

                original_config = r.json()["items"][0]
                new_config = new_configs[configuration]

                diff_config = self.get_config_diff(original_config, new_config, cluster_size)

                if diff_config != None:
                    update_config = {
                        "Clusters": {
                            "desired_config": {
                                "type": configuration,
                                'tag': "version{0}".format(current_ts),
                                'service_config_version_note': "Automation script"
                            }
                        }
                    }
                    update_config["Clusters"]["desired_config"].update(diff_config)
                    logging.info("Applying new configuration for "+configuration+" : "+json.dumps(update_config))
                    r = self.session.put(self.ambari_url + "/api/v1/clusters/{0}".format(self.stack_name), data=json.dumps(update_config))
                    r.raise_for_status()

    def get_config_diff(self, original, new, cluster_size):
        contains_diff = False

        host_groups = self.build_host_groups(cluster_size)

        diff = {
            "properties": {},
            "properties_attributes": {}
        }

        if original.get("properties") == None:
            logging.info("No configuration for "+original["type"])
            return None

        for key in original["properties"]:
            original_value = original["properties"][key]
            new_value = new["properties"].get(key)
            if new_value != None:
                new_value = self.replace_group_to_host(new_value, host_groups)

                if original_value != new_value:
                    diff["properties"][key] = new_value
                    contains_diff = True

        if contains_diff:
            return diff
        else:
            return None

    def replace_group_to_host(self, value, host_groups):

        for host_group in host_groups:
            name = host_group["name"]
            hosts = list(map(lambda h: h["fqdn"], host_group["hosts"]))
            hosts_string = ','.join(hosts)
            value = value.replace("%HOSTGROUP::{0}%".format(name), hosts_string)

        return value

    def replace_host_to_group(self, value, host_groups):

        for host_group in host_groups:
            name = host_group["name"]
            hosts = list(map(lambda h: h["fqdn"], host_group["hosts"]))
            hosts_string = ','.join(hosts)
            value = value.replace(hosts_string, "%HOSTGROUP::{0}%".format(name))

        return value

    def check_for_ambari(self):
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

    def check_for_cluster_request(self, requestId):
        "wait for cluster to be ready"
        logging.info("Wait for cluster to be ready")
        r = self.session.get(self.ambari_url + '/api/v1/clusters/' + self.stack_name + '/requests/' + str(requestId))
        r.raise_for_status()
        requestDetail = r.json()
        if requestDetail['Requests']['request_status'] == 'IN_PROGRESS' or requestDetail['Requests']['task_count'] == 0:
            return False
        else:
            return True

    def build_config(self, config_folder):

        blueprint_file = os.path.join(config_folder, "blueprint.json")
        blueprint = {}

        with open(blueprint_file, 'r', encoding='UTF8') as file:
            blueprint = json.load(file)

        # get the list of components to install
        services = [ 'CLUSTER' ]
        for host_group in blueprint["host_groups"]:
            for service in host_group["components"]:
                service = self.get_service_from_component(service['name'])
                services.append(service)
        services = list(set(services))

        # get the configs for all these components and merge in the blueprint
        for service in services:
            config_json_file = os.path.join(config_folder, service, "{0}.json".format(service))

            with open(config_json_file, 'r', encoding='UTF8') as file:
                config = json.load(file)

            for config_key in config["properties"]:

                # read external files
                for property_key in config["properties"][config_key]["properties"]:
                    if property_key == "content":
                        file_name = config["properties"][config_key]["properties"][property_key]
                        file_path = os.path.join(config_folder, service, file_name)
                        with open(file_path, 'r', encoding='UTF8') as file:
                            config["properties"][config_key]["properties"][property_key] = file.read()

                blueprint["configurations"].append({
                    config_key : config["properties"][config_key]
                })

        return blueprint

    def dump_config(self, config_folder, cluster_size):
        r = self.session.get(self.ambari_url + '/api/v1/clusters/' + self.stack_name + '?fields=service_config_versions,Clusters/desired_service_config_versions')

        r.raise_for_status()

        service_json = r.json()

        # get all services with theirs configs
        service_configs = self.get_service_configs()

        host_groups = self.build_host_groups(cluster_size)

        # build a json per service with all configs
        service_config_json = {}
        for service_key in service_configs:
            service_config_json[service_key] = {
                "properties" : {}
            }
        service_config_json['CLUSTER'] = {
            "properties" : {}
        }

        # get the last version of the service configs
        service_config_version = {}
        for item in service_json["Clusters"]["desired_service_config_versions"]:
            service_config_version[item] = service_json["Clusters"]["desired_service_config_versions"][item][0]["service_config_version"]

        # create the configs json for each services
        service_configuration = service_json["service_config_versions"]
        for config_item in service_configuration:
            config_key = config_item["service_name"]

            if service_config_version[config_key] != config_item["service_config_version"]:
                continue

            for config in config_item["configurations"]:
                service_config_json[config_key]['properties'][config['type']] = {
                    "properties": {},
                    "properties_attributes": {}
                }

                for property in config["properties"]:
                    if config["properties"][property].startswith('SECRET:'):
                        logging.info("Ignoring secret property {0} - {1}".format(config['type'], property))
                    else:
                        service_config_json[config_key]['properties'][config['type']]['properties'][property] =  config["properties"][property]

                service_config_json[config_key]['properties'][config['type']]['properties_attributes'] = config["properties_attributes"]


        # dump the json per service, and replace "content" by an external file
        for service_key in service_config_json:

            os.makedirs(os.path.join(config_folder, service_key), exist_ok=True)

            service_config = service_config_json[service_key]
            for service_property in service_config["properties"]:
                config = service_config["properties"][service_property]
                for property in config["properties"]:
                    if property == "content":
                        extention = self.get_property_extension_file(service_property)

                        content_file = "{0}{1}".format(service_property, extention)
                        content_file_path = os.path.join(config_folder, service_key, content_file)

                        content = config["properties"][property]
                        config["properties"][property] = content_file
                        with open(content_file_path, 'w', encoding='UTF8') as file:
                            file.write(content)
                    else:
                        config["properties"][property] = self.replace_host_to_group(config["properties"][property], host_groups)


            config_file = os.path.join(config_folder, service_key, "{0}.json".format(service_key))
            with open(config_file, 'w', encoding='UTF8') as file:
                json.dump(service_config_json[service_key], file, sort_keys=True, indent=4, separators=(',', ': '))

    def get_property_extension_file(self, property):
        if property.endswith('-env'):
            extention = ".sh"
        elif property.endswith('-log4j'):
            extention = ".properties"
        elif property.endswith('-properties'):
            extention = ".properties"
        elif property.endswith('.properties'):
            extention = ""
        elif property.endswith('-logsearch-conf'):
            extention = ".json"
        else:
            extention = ".txt"

        return extention

    def get_service_configs(self):
        service_configs = {
            'HDFS': [
                "core-site",
                "hdfs-site",
                "hadoop-env",
                "hadoop-policy",
                "hdfs-log4j",
                "ssl-client",
                "ssl-server",
                "ranger-hdfs-plugin-properties",
                "ranger-hdfs-audit",
                "ranger-hdfs-policymgr-ssl",
                "ranger-hdfs-security"
            ],
            'YARN': [
                "yarn-env",
                "yarn-log4j",
                "yarn-site",
                "capacity-scheduler",
                "ranger-yarn-plugin-properties",
                "ranger-yarn-audit",
                "ranger-yarn-policymgr-ssl",
                "ranger-yarn-security"
            ],
            'MAPREDUCE2': [
                "mapred-site",
                "mapred-env"
            ],
            'ZOOKEEPER': [
                "zookeeper-log4j",
                "zookeeper-env",
                "zoo.cfg"
            ],
            'PIG': [
                "pig-env",
                "pig-log4j",
                "pig-properties"
            ],
            'TEZ': [
                "tez-site",
                "tez-env"
            ],
            'SLIDER': [
                "slider-log4j",
                "slider-client",
                "slider-env"
            ],
            'HIVE': [
                "hive-log4j",
                "hive-exec-log4j",
                "hive-env",
                "hivemetastore-site.xml",
                "webhcat-site",
                "webhcat-env",
                "ranger-hive-plugin-properties",
                "ranger-hive-audit",
                "ranger-hive-policymgr-ssl",
                "ranger-hive-security"
            ],
            'OOZIE': [
                "oozie-site",
                "oozie-env",
                "oozie-log4j"
            ],
            'HBASE': [
                "hbase-policy",
                "hbase-site",
                "hbase-env",
                "hbase-log4j",
                "ranger-hbase-plugin-properties",
                "ranger-hbase-audit",
                "ranger-hbase-policymgr-ssl",
                "ranger-hbase-security"
            ],
            'SPARK': [
                "spark-defaults",
                "spark-env",
                "spark-log4j-properties",
                "spark-metrics-properties",
                "spark-javaopts-properties",
                "spark-thrift-sparkconf",
                "spark-hive-site-override",
                "spark-thrift-fairscheduler"
            ],
            'KAFKA': [
                "kafka-broker",
                "kafka-env",
                "kafka-log4j",
                "ranger-kafka-plugin-properties",
                "ranger-kafka-audit",
                "ranger-kafka-policymgr-ssl",
                "ranger-kafka-security"
            ],
            'KNOX': [
                "gateway-site",
                "gateway-log4j",
                "topology",
                "admin-topology",
                "knoxsso-topology",
                "ranger-knox-plugin-properties",
                "ranger-knox-audit",
                "ranger-knox-policymgr-ssl",
                "ranger-knox-security"
            ],
            'RANGER': [
                "admin-log4j",
                "usersync-log4j",
                "ranger-admin-site",
                "ranger-ugsync-site",
            ]
        }

        return service_configs

    def get_service_from_component(self, component):
        component_services = {
            "HDFS": [
                "NAMENODE",
                "SECONDARY_NAMENODE",
                "DATANODE",
                "HDFS_CLIENT"
            ],
            "MAPREDUCE2": [
                "MAPREDUCE2_CLIENT",
                "HISTORYSERVER"
            ],
            "YARN": [
                "NODEMANAGER",
                "YARN_CLIENT",
                "RESOURCEMANAGER",
                "APP_TIMELINE_SERVER"
            ],
            "ZOOKEEPER": [
                "ZOOKEEPER_SERVER",
                "ZOOKEEPER_CLIENT"
            ],
            "PIG": [
                "PIG"
            ],
            "TEZ": [
                "TEZ_CLIENT"
            ],
            "SLIDER": [
                "SLIDER"
            ]
        }

        for service in component_services:
            if component in component_services[service]:
                return service

        raise Exception("Unknown component {0}".format(component))