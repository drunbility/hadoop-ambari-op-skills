# Ambari REST API 参考

## 基础信息

- **API 版本**: v1
- **内容类型**: `application/json`
- **默认端口**: 8080
- **认证方式**: HTTP Basic Auth

## 常用端点

### 集群管理

#### 获取集群列表
```http
GET /api/v1/clusters
```

#### 获取集群信息
```http
GET /api/v1/clusters/{cluster_name}
```

### 服务管理

#### 列出所有服务
```http
GET /api/v1/clusters/{cluster_name}/services
```

#### 获取服务状态
```http
GET /api/v1/clusters/{cluster_name}/services/{service_name}
```

#### 启动/停止服务
```http
PUT /api/v1/clusters/{cluster_name}/services/{service_name}
Content-Type: application/json

{
  "RequestInfo": {
    "context": "Start/Stop service",
    "operation_level": "service"
  },
  "Body": {
    "ServiceInfo": {
      "state": "STARTED" | "INSTALLED"
    }
  }
}
```

### 组件管理

#### 列出服务组件
```http
GET /api/v1/clusters/{cluster_name}/services/{service_name}/components
```

#### 获取组件实例
```http
GET /api/v1/clusters/{cluster_name}/services/{service_name}/components/{component_name}
```

#### 重启组件（异步）
```http
POST /api/v1/clusters/{cluster_name}/requests
Content-Type: application/json

{
  "RequestInfo": {
    "command": "RESTART",
    "context": "Restart component",
    "operation_level": "host_component"
  },
  "Requests/resource_filters": [{
    "service_name": "HIVE",
    "component_name": "HIVE_METASTORE",
    "hosts": "host1.example.com"
  }]
}
```

### 请求管理

#### 获取请求状态
```http
GET /api/v1/clusters/{cluster_name}/requests/{request_id}
```

#### 取消请求
```http
PUT /api/v1/clusters/{cluster_name}/requests/{request_id}
Content-Type: application/json

{
  "Requests": {
    "request_status": "ABORTED"
  }
}
```

### 主机管理

#### 列出所有主机
```http
GET /api/v1/clusters/{cluster_name}/hosts
```

#### 获取主机组件
```http
GET /api/v1/clusters/{cluster_name}/hosts/{host_name}/host_components
```

## 请求状态

| 状态 | 说明 |
|-----|------|
| PENDING | 等待执行 |
| QUEUED | 已入队 |
| IN_PROGRESS | 执行中 |
| COMPLETED | 完成 |
| FAILED | 失败 |
| ABORTED | 已中止 |
| TIMEDOUT | 超时 |
| REJECTED | 被拒绝 |

## 服务状态

| 状态 | 说明 |
|-----|------|
| INIT | 初始状态 |
| INSTALLING | 安装中 |
| INSTALL_FAILED | 安装失败 |
| INSTALLED | 已安装（已停止） |
| STARTING | 启动中 |
| STARTED | 运行中 |
| STOPPING | 停止中 |
| UNINSTALLING | 卸载中 |
| UNINSTALLED | 已卸载 |
| WIPING_OUT | 清理中 |

## 常用 curl 示例

### 基础认证请求
```bash
curl -u "admin:password" \
  -H "X-Requested-By: ambari" \
  "http://ambari-server:8080/api/v1/clusters"
```

### 批量重启多个组件
```bash
curl -u "admin:password" \
  -H "X-Requested-By: ambari" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "RequestInfo": {
      "command": "RESTART",
      "context": "Batch restart"
    },
    "Requests/resource_filters": [
      {"service_name": "HIVE", "component_name": "HIVE_METASTORE"},
      {"service_name": "HIVE", "component_name": "HIVE_SERVER"}
    ]
  }' \
  "http://ambari-server:8080/api/v1/clusters/HDPCluster/requests"
```

### 维护模式
```bash
# 开启维护模式
curl -u "admin:password" \
  -H "X-Requested-By: ambari" \
  -X PUT \
  -d '{"ServiceInfo": {"maintenance_state": "ON"}}' \
  "http://ambari-server:8080/api/v1/clusters/HDPCluster/services/HIVE"

# 关闭维护模式
curl -u "admin:password" \
  -H "X-Requested-By: ambari" \
  -X PUT \
  -d '{"ServiceInfo": {"maintenance_state": "OFF"}}' \
  "http://ambari-server:8080/api/v1/clusters/HDPCluster/services/HIVE"
```

### 组件信息查询
```bash
# 获取组件状态
curl -u "admin:password" \
  -H "X-Requested-By: ambari" \
  "http://ambari-server:8080/api/v1/clusters/HDPCluster/services/HIVE/components/HIVE_METASTORE"

# 获取主机上的组件
curl -u "admin:password" \
  -H "X-Requested-By: ambari" \
  "http://ambari-server:8080/api/v1/clusters/HDPCluster/hosts/host1.example.com/host_components/HIVE_METASTORE"
```

## 错误代码

| HTTP 状态 | 说明 |
|----------|------|
| 200 OK | 成功 |
| 201 Created | 创建成功 |
| 202 Accepted | 已接受（异步操作） |
| 400 Bad Request | 请求参数错误 |
| 401 Unauthorized | 认证失败 |
| 403 Forbidden | 权限不足 |
| 404 Not Found | 资源不存在 |
| 409 Conflict | 资源冲突（如服务已在操作中） |
| 500 Internal Server Error | 服务器内部错误 |

## 响应格式

### 成功响应示例
```json
{
  "href": "http://ambari-server:8080/api/v1/clusters/HDPCluster/requests/100",
  "Requests": {
    "id": 100,
    "cluster_name": "HDPCluster",
    "request_status": "IN_PROGRESS",
    "progress_percent": 45.5,
    "context": "Restart component"
  }
}
```

### 错误响应示例
```json
{
  "status": 400,
  "message": "Invalid request: Service HIVE not found"
}
```
