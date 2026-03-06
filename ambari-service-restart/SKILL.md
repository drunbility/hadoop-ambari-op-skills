---
name: ambari-service-restart
description: Ambari 大数据集群服务管理工具，用于通过 Ambari REST API 管理 Hadoop 生态组件（如 HDFS、YARN、MapReduce、Hive、HBase、ZooKeeper 等）的重启、启动、停止操作。支持单个组件或批量服务操作，自动轮询任务状态直至完成。当用户需要重启 Ambari 管理的任何大数据服务时使用此 skill。
argument-hint: "[action=RESTART] [service_name] [component_name] [host_fqdn] [cluster_name] [username] [password]"
---

# Ambari Service Restart Skill

通过 Ambari REST API 管理 Hadoop 生态服务的生命周期操作。

## 支持的组件

| 服务 | 常用组件名 |
|------|-----------|
| HDFS | NAMENODE, DATANODE, SECONDARY_NAMENODE, JOURNALNODE, ZKFC |
| YARN | RESOURCEMANAGER, NODEMANAGER, APP_TIMELINE_SERVER, TIMELINE_READER |
| MapReduce | HISTORY_SERVER, CLIENT |
| Hive | HIVE_METASTORE, HIVE_SERVER, HIVE_CLIENT, WEBHCAT_SERVER |
| HBase | HBASE_MASTER, HBASE_REGIONSERVER, PHOENIX_QUERY_SERVER |
| ZooKeeper | ZOOKEEPER_SERVER, ZOOKEEPER_CLIENT |
| Oozie | OOZIE_SERVER, OOZIE_CLIENT |
| Spark2 | SPARK2_THRIFT_SERVER, SPARK2_JOB_HISTORY_SERVER, LIVY2_SERVER |
| Druid | DRUID_BROKER, DRUID_COORDINATOR, DRUID_HISTORICAL, DRUID_OVERLORD, DRUID_ROUTER, DRUID_MIDDLE_MANAGER |
| Ranger | RANGER_ADMIN, RANGER_USERSYNC, RANGER_TAGSYNC |
| 其他 | KAFKA_BROKER, STORM_UI_SERVER, STORM_NIMBUS 等 |

## 参数说明

所有参数均可通过位置参数或环境变量传递：

| 位置 | 环境变量 | 说明 | 默认值 |
|-----|---------|------|-------|
| $1 | AMBARI_ACTION | 操作类型：RESTART/START/STOP | RESTART |
| $2 | AMBARI_SERVICE | 服务名称（如 HIVE, HDFS） | 必填 |
| $3 | AMBARI_COMPONENT | 组件名称（如 HIVE_METASTORE） | 可选 |
| $4 | AMBARI_HOST | 目标主机 FQDN | 可选（不指定则操作所有主机） |
| $5 | AMBARI_URL | Ambari Server URL | http://172.17.236.249:8080 |
| $6 | AMBARI_CLUSTER | 集群名称 | HDPCluster |
| $7 | AMBARI_USER | 用户名 | admin |
| $8 | AMBARI_PASSWORD | 密码 | 从 AMBARI_PASSWORD 环境变量读取 |

## 使用方式

### 方式一：使用 Python 脚本（推荐）

```bash
# 重启 HDFS 的 DataNode
python3 /root/.claude/skills/ambari-service-restart/scripts/ambari_manager.py restart HDFS DATANODE

# 重启整个 HIVE 服务的所有组件
python3 /root/.claude/skills/ambari-service-restart/scripts/ambari_manager.py restart HIVE

# 停止特定主机上的 YARN NodeManager
python3 /root/.claude/skills/ambari-service-restart/scripts/ambari_manager.py stop YARN NODEMANAGER hdp-node1.example.com

# 使用自定义 Ambari 地址
AMBARI_URL=http://ambari-server:8080 python3 /root/.claude/skills/ambari-service-restart/scripts/ambari_manager.py restart HBASE
```

### 方式二：使用 curl 直接调用

**重启单个组件：**

```bash
curl -u "admin:password" \
  -H "X-Requested-By: ambari" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "RequestInfo": {
      "command": "RESTART",
      "context": "Restart component via API",
      "operation_level": "host_component"
    },
    "Requests/resource_filters": [{
      "service_name": "HIVE",
      "component_name": "HIVE_METASTORE",
      "hosts": "host1.example.com"
    }]
  }' \
  "http://172.17.236.249:8080/api/v1/clusters/HDPCluster/requests"
```

**重启整个服务的所有组件：**

```bash
curl -u "admin:password" \
  -H "X-Requested-By: ambari" \
  -H "Content-Type: application/json" \
  -X PUT \
  -d '{
    "RequestInfo": {
      "context": "Restart service via API",
      "operation_level": "service"
    },
    "Body": {
      "ServiceInfo": {
        "state": "INSTALLED"
      }
    }
  }' \
  "http://172.17.236.249:8080/api/v1/clusters/HDPCluster/services/HIVE"
```

## 工作流程

1. **验证参数**：检查必填参数（service_name）和密码
2. **构造请求**：根据操作类型构建 REST API 请求
3. **发送请求**：POST 到 `/api/v1/clusters/{cluster}/requests`
4. **获取 request_id**：从响应中提取任务 ID
5. **轮询状态**：循环查询 `/api/v1/clusters/{cluster}/requests/{request_id}`
6. **输出结果**：
   - COMPLETED → 操作成功
   - FAILED/ABORTED/TIMEDOUT → 操作失败，输出详细错误

## 状态轮询

- 轮询间隔：5 秒
- 最大轮询次数：60 次（约 5 分钟）
- 超时处理：输出最后状态并标记为超时

## 错误处理

- **401 Unauthorized**：检查用户名/密码
- **404 Not Found**：检查集群名称、服务名称或主机名
- **500 Server Error**：Ambari Server 内部错误，查看 Ambari 日志
- **Connection Refused**：检查 Ambari Server 地址和端口

## 安全提示

- 密码通过环境变量传递，避免在命令行中暴露
- 脚本输出中对密码进行脱敏处理（显示为 ******）
- 建议使用只具有服务操作权限的专用账号

## 参考文档

- 完整 API 文档：`references/ambari_api.md`
- Python 脚本源码：`scripts/ambari_manager.py`
