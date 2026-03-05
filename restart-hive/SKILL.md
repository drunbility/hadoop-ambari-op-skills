---
name: restart-hive
description: ambari 大数据集群管理工具，当运维操作大数据集群相关服务（比如 hive_server, hive_metastore）时使用，该操作会触发一个异步的 RESTART 请求，捕获请求 ID，轮询 request_status 直至状态变为 COMPLETED（或 FAILED/ABORTED/TIMEDOUT），并输出最终的 request_status 
disable-model-invocation: false
allowed-tools: Bash(curl *)
argument-hint: "[ambari_base_url] [cluster_name] [host_fqdn] [component_name=HIVE_METASTORE] [username] [password]"
---

你是 Apache Hadoop 集群管理运维自动化助手。你的任务是：通过 Ambari REST API 对指定 host 上的指定大数据组件发起 RESTART（异步），解析返回的请求 ID，然后轮询查询该请求的状态直到完成。

## 输入参数（来自 /restart-hive 后的参数）
- $0: ambari_base_url（默认为 http://172.17.236.249:8080，若为空则用该默认值）
- $1: cluster_name（默认为 HDPCluster，若为空则用该默认值）
- $2: host_fqdn（例如 hdp-hive-236-252.hnlshm.com，或者 172.17.236.251）
- $3: component_name（比如 HIVE_METASTORE；若为空则用该默认值）
- $4: username（默认为 admin，若为空则用该默认值）
- $5: password（从环境变量中获取，若为空则提示错误）
- $6: service_name (默认为 HIVE,若为空则用默认值)

如果取到足够参数：
1) 先停下
2) 用一句话提示缺哪些参数

## 行为规范
- 只允许使用 curl（Bash(curl *)），不要调用其他命令。
- 输出时注意脱敏：不要回显明文密码；展示时用 ****** 代替。
- 轮询间隔 6 秒，最多轮询 20 次；超时则报错并输出最后一次查询到的 JSON。
- 将所有响应都当作 JSON 处理并原样输出（必要时只做最少的字段提取：id、request_status、message/alerts）。
- 任何非 2xx 都视为失败，直接输出响应并停止。

## 具体步骤
### 1) 组装 URL
- 发起请求 URL：
  {ambari_base_url}/api/v1/clusters/{cluster_name}/requests
- 查询状态 URL：
  {ambari_base_url}/api/v1/clusters/{cluster_name}/requests/{request_id}

### 2) 发起异步 RESTART（POST）
使用如下 JSON（component_name 与 hosts 必须来自参数）：
- service_name 固定为 HIVE
- component_name 使用 $3（默认 HIVE_METASTORE）
- hosts 使用 $2

执行（注意：不要把 password 打印到输出里）：

`curl  -u "$4:$5" \
  -H "X-Requested-By: ambari" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "RequestInfo": {
      "command": "RESTART",
      "context": "Restart Hive via skill",
      "operation_level": "host_component"
    },
    "Requests/resource_filters": [
      {
        "service_name": "'"$6"'",
        "component_name": "'"${3:-HIVE_METASTORE}"'",
        "hosts": "'"$2"'"
      }
    ]
  }' \
  "$0/api/v1/clusters/$1/requests"`

### 3) 从响应中获取 request_id
- 从响应的 JSON 的路径 `Requests.id` 提取（Ambari 常见格式）。

### 4) 轮询查询状态（GET）
循环调用：

`curl -u "$4:$5" "$0/api/v1/clusters/$1/requests/$REQUEST_ID"`

从响应的 JSON 的路径 `Requests.request_status` 取得请求状态

判定：
- 若 `request_status` 为 COMPLETED：输出重启成功，结束，返回成功说明。
- 若为 FAILED / ABORTED / TIMEDOUT：输出最终 JSON，结束，返回失败说明。
- 否则继续轮询，最多 20 次，每次间隔 6 秒。（间隔的实现：如果不能 sleep，就改为提示用户“再次运行本 skill 并带上 request_id”来继续轮询。）

## 示例
用户调用示例：
/restart-hive http://172.17.236.249:8080 HDPCluster hdp-hive-236-252.hnlshm.com HIVE_METASTORE admin "xxxujm*Uxx"