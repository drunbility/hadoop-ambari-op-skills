# hadoop-ambari-op-skills
claude code ambari ops skills 集锦

先是手写了特定的 restart-hive skill

然后使用 kimi code ，命令写更通用的 skill, kimi 自动参照手写的直出了完整的通用skill ，非常惊艳！



 ✅ Ambari 服务管理 Skill 已创建完成！



📁 文件结构

  /root/.claude/skills/ambari-service-restart/
  ├── SKILL.md                          # 主说明文档
  ├── scripts/
  │   └── ambari_manager.py             # Python 管理脚本
  └── references/
      └── ambari_api.md                 # API 参考文档

  📦 打包文件

  /root/.claude/skills/ambari-service-restart.skill  (12KB)

  🚀 快速使用

  方式一：Python 脚本（推荐）

  # 设置密码环境变量（安全）

  export AMBARI_PASSWORD="your_password"

  # 重启 Hive Metastore

  python3 /root/.claude/skills/ambari-service-restart/scripts/ambari_manager.py restart HIVE HIVE_METASTORE

  # 重启整个 HDFS 服务

  python3 /root/.claude/skills/ambari-service-restart/scripts/ambari_manager.py restart HDFS

  # 停止特定主机的 YARN NodeManager

  python3 /root/.claude/skills/ambari-service-restart/scripts/ambari_manager.py stop YARN NODEMANAGER hdp-node1.example.com

  # 查看帮助

  python3 /root/.claude/skills/ambari-service-restart/scripts/ambari_manager.py --help

  方式二：环境变量配置

  export AMBARI_URL="http://172.17.236.249:8080"
  export AMBARI_CLUSTER="HDPCluster"
  export AMBARI_USER="admin"
  export AMBARI_PASSWORD="your_password"

  python3 /root/.claude/skills/ambari-service-restart/scripts/ambari_manager.py restart HIVE

  方式三：Claude Code 触发

  由于技能已安装在 ~/.claude/skills/，你可以直接通过自然语言让 Claude Code 使用：

  帮我重启 Hive 的 Metastore 组件

  或指定参数：

  /ambari-service-restart restart HIVE HIVE_METASTORE hdp-host1.example.com

  ✅ 功能特性

   功能       说明
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   操作类型   RESTART / START / STOP
   粒度控制   服务级、组件级、主机级
   自动轮询   5秒间隔，最多60次（5分钟）
   密码脱敏   输出中自动隐藏密码
   超时处理   超时后输出最后状态
   环境变量   支持通过环境变量配置

  🔧 支持的服务

  • HDFS: NAMENODE, DATANODE, SECONDARY_NAMENODE, JOURNALNODE, ZKFC
  • YARN: RESOURCEMANAGER, NODEMANAGER, APP_TIMELINE_SERVER
  • Hive: HIVE_METASTORE, HIVE_SERVER, HIVE_CLIENT, WEBHCAT_SERVER
  • HBase: HBASE_MASTER, HBASE_REGIONSERVER, PHOENIX_QUERY_SERVER
  • MapReduce: HISTORY_SERVER, CLIENT
  • ZooKeeper: ZOOKEEPER_SERVER, ZOOKEEPER_CLIENT
  • Spark2: SPARK2_THRIFT_SERVER, SPARK2_JOB_HISTORY_SERVER, LIVY2_SERVER
  • Druid: DRUID_BROKER, DRUID_COORDINATOR, DRUID_HISTORICAL 等
  • 其他: KAFKA, OOZIE, RANGER, STORM 等

  📦 分发安装

  如果你想在其他机器上使用这个 skill：

  # 复制打包文件

  scp /root/.claude/skills/ambari-service-restart.skill user@target:/tmp/

  # 在目标机器解压到 Claude Code skills 目录

  cd ~/.claude/skills && unzip /tmp/ambari-service-restart.skill
