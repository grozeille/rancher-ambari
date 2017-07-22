
JAVA_HOME={{java64_home}}
HADOOP_HOME=${HADOOP_HOME:-{{hadoop_home}}}

if [ -d "/usr/lib/tez" ]; then
  PIG_OPTS="$PIG_OPTS -Dmapreduce.framework.name=yarn"
fi