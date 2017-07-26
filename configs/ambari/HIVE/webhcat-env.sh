
# The file containing the running pid
PID_FILE={{webhcat_pid_file}}

TEMPLETON_LOG_DIR={{templeton_log_dir}}/


WEBHCAT_LOG_DIR={{templeton_log_dir}}/

# The console error log
ERROR_LOG={{templeton_log_dir}}/webhcat-console-error.log

# The console log
CONSOLE_LOG={{templeton_log_dir}}/webhcat-console.log

#TEMPLETON_JAR=templeton_jar_name

#HADOOP_PREFIX=hadoop_prefix

#HCAT_PREFIX=hive_prefix

# Set HADOOP_HOME to point to a specific hadoop install directory
export HADOOP_HOME=${HADOOP_HOME:-{{hadoop_home}}}