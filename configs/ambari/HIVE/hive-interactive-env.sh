
      if [ "$SERVICE" = "cli" ]; then
      if [ -z "$DEBUG" ]; then
      export HADOOP_OPTS="$HADOOP_OPTS -XX:NewRatio=12 -XX:MaxHeapFreeRatio=40 -XX:MinHeapFreeRatio=15 -XX:+UseParNewGC -XX:-UseGCOverheadLimit"
      else
      export HADOOP_OPTS="$HADOOP_OPTS -XX:NewRatio=12 -XX:MaxHeapFreeRatio=40 -XX:MinHeapFreeRatio=15 -XX:-UseGCOverheadLimit"
      fi
      fi

      # The heap size of the jvm stared by hive shell script can be controlled via:

      if [ "$SERVICE" = "metastore" ]; then
      export HADOOP_HEAPSIZE={{hive_metastore_heapsize}} # Setting for HiveMetastore
      else
      export HADOOP_HEAPSIZE={{hive_interactive_heapsize}} # Setting for HiveServer2 and Client
      fi

      export HADOOP_CLIENT_OPTS="$HADOOP_CLIENT_OPTS  -Xmx${HADOOP_HEAPSIZE}m"
      export HADOOP_CLIENT_OPTS="$HADOOP_CLIENT_OPTS{{heap_dump_opts}}"

      # Larger heap size may be required when running queries over large number of files or partitions.
      # By default hive shell scripts use a heap size of 256 (MB).  Larger heap size would also be
      # appropriate for hive server (hwi etc).


      # Set HADOOP_HOME to point to a specific hadoop install directory
      HADOOP_HOME=${HADOOP_HOME:-{{hadoop_home}}}

      # Hive Configuration Directory can be controlled by:
      export HIVE_CONF_DIR={{hive_server_interactive_conf_dir}}

      # Add additional hcatalog jars
      if [ "${HIVE_AUX_JARS_PATH}" != "" ]; then
        export HIVE_AUX_JARS_PATH=${HIVE_AUX_JARS_PATH}
      else
        export HIVE_AUX_JARS_PATH=/usr/hdp/current/hive-server2-hive2/lib/hive-hcatalog-core.jar
      fi

      export METASTORE_PORT={{hive_metastore_port}}

      # Spark assembly contains a conflicting copy of HiveConf from hive-1.2
      export HIVE_SKIP_SPARK_ASSEMBLY=true