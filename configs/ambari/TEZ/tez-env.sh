
# Tez specific configuration
export TEZ_CONF_DIR={{config_dir}}

# Set HADOOP_HOME to point to a specific hadoop install directory
export HADOOP_HOME=${HADOOP_HOME:-{{hadoop_home}}}

# The java implementation to use.
export JAVA_HOME={{java64_home}}