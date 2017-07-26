
      export HADOOP_USER_CLASSPATH_FIRST=true  #this prevents old metrics libs from mapreduce lib from bringing in old jar deps overriding HIVE_LIB
      if [ "$SERVICE" = "cli" ]; then
      if [ -z "$DEBUG" ]; then
      export HADOOP_OPTS="$HADOOP_OPTS -XX:NewRatio=12 -XX:MaxHeapFreeRatio=40 -XX:MinHeapFreeRatio=15 -XX:+UseNUMA -XX:+UseParallelGC -XX:-UseGCOverheadLimit"
      else
      export HADOOP_OPTS="$HADOOP_OPTS -XX:NewRatio=12 -XX:MaxHeapFreeRatio=40 -XX:MinHeapFreeRatio=15 -XX:-UseGCOverheadLimit"
      fi
      fi

      # The heap size of the jvm stared by hive shell script can be controlled via:

      if [ "$SERVICE" = "metastore" ]; then
      export HADOOP_HEAPSIZE={{hive_metastore_heapsize}} # Setting for HiveMetastore
      else
      export HADOOP_HEAPSIZE={{hive_heapsize}} # Setting for HiveServer2 and Client
      fi

      export HADOOP_CLIENT_OPTS="$HADOOP_CLIENT_OPTS  -Xmx${HADOOP_HEAPSIZE}m"
      export HADOOP_CLIENT_OPTS="$HADOOP_CLIENT_OPTS{{heap_dump_opts}}"

      # Larger heap size may be required when running queries over large number of files or partitions.
      # By default hive shell scripts use a heap size of 256 (MB).  Larger heap size would also be
      # appropriate for hive server (hwi etc).


      # Set HADOOP_HOME to point to a specific hadoop install directory
      HADOOP_HOME=${HADOOP_HOME:-{{hadoop_home}}}

      export HIVE_HOME=${HIVE_HOME:-{{hive_home_dir}}}

      # Hive Configuration Directory can be controlled by:
      export HIVE_CONF_DIR=${HIVE_CONF_DIR:-{{hive_config_dir}}}

      # Folder containing extra libraries required for hive compilation/execution can be controlled by:
      if [ "${HIVE_AUX_JARS_PATH}" != "" ]; then
        if [ -f "${HIVE_AUX_JARS_PATH}" ]; then
          export HIVE_AUX_JARS_PATH=${HIVE_AUX_JARS_PATH}
        elif [ -d "/usr/hdp/current/hive-webhcat/share/hcatalog" ]; then
          export HIVE_AUX_JARS_PATH=/usr/hdp/current/hive-webhcat/share/hcatalog/hive-hcatalog-core.jar
        fi
      elif [ -d "/usr/hdp/current/hive-webhcat/share/hcatalog" ]; then
        export HIVE_AUX_JARS_PATH=/usr/hdp/current/hive-webhcat/share/hcatalog/hive-hcatalog-core.jar
      fi

      export METASTORE_PORT={{hive_metastore_port}}

      {% if sqla_db_used or lib_dir_available %}
      export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:{{jdbc_libs_dir}}"
      export JAVA_LIBRARY_PATH="$JAVA_LIBRARY_PATH:{{jdbc_libs_dir}}"
      {% endif %}