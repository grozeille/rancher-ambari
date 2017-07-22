
# Set Slider-specific environment variables here.

# The only required environment variable is JAVA_HOME.  All others are
# optional.  When running a distributed configuration it is best to
# set JAVA_HOME in this file, so that it is correctly defined on
# remote nodes.

# The java implementation to use.  Required.
export JAVA_HOME={{java64_home}}
# The hadoop conf directory.  Optional as slider-client.xml can be edited to add properties.
export HADOOP_CONF_DIR={{hadoop_conf_dir}}