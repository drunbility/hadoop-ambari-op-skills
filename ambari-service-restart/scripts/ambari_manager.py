#!/usr/bin/env python3
"""
Ambari Service Manager - 通过 Ambari REST API 管理 Hadoop 服务

支持操作：RESTART, START, STOP
支持级别：单个组件、服务级别、主机级别
"""

import argparse
import json
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin


# 默认配置
DEFAULT_CONFIG = {
    "url": "http://172.17.236.249:8080",
    "cluster": "HDPCluster",
    "user": "admin",
    "password": os.environ.get("AMBARI_PASSWORD", ""),
}

# 服务到组件的映射（常用）
SERVICE_COMPONENTS = {
    "HDFS": ["NAMENODE", "DATANODE", "SECONDARY_NAMENODE", "JOURNALNODE", "ZKFC"],
    "YARN": ["RESOURCEMANAGER", "NODEMANAGER", "APP_TIMELINE_SERVER", "TIMELINE_READER"],
    "MAPREDUCE2": ["HISTORY_SERVER", "CLIENT"],
    "HIVE": ["HIVE_METASTORE", "HIVE_SERVER", "HIVE_CLIENT", "WEBHCAT_SERVER"],
    "HBASE": ["HBASE_MASTER", "HBASE_REGIONSERVER", "PHOENIX_QUERY_SERVER"],
    "ZOOKEEPER": ["ZOOKEEPER_SERVER", "ZOOKEEPER_CLIENT"],
    "OOZIE": ["OOZIE_SERVER", "OOZIE_CLIENT"],
    "SPARK2": ["SPARK2_THRIFT_SERVER", "SPARK2_JOB_HISTORY_SERVER", "LIVY2_SERVER"],
    "DRUID": ["DRUID_BROKER", "DRUID_COORDINATOR", "DRUID_HISTORICAL", 
              "DRUID_OVERLORD", "DRUID_ROUTER", "DRUID_MIDDLE_MANAGER"],
    "RANGER": ["RANGER_ADMIN", "RANGER_USERSYNC", "RANGER_TAGSYNC"],
    "KAFKA": ["KAFKA_BROKER"],
    "STORM": ["STORM_UI_SERVER", "STORM_NIMBUS", "STORM_SUPERVISOR", "STORM_DRPC_SERVER"],
}


class AmbariClient:
    """Ambari REST API 客户端"""
    
    def __init__(self, base_url, username, password, cluster_name):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.cluster_name = cluster_name
        
    def _make_request(self, endpoint, method="GET", data=None):
        """发送 HTTP 请求"""
        url = f"{self.base_url}/api/v1/clusters/{self.cluster_name}/{endpoint}"
        
        # 添加认证头
        import base64
        credentials = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {credentials}",
            "X-Requested-By": "ambari",
            "Content-Type": "application/json",
        }
        
        if data:
            data = json.dumps(data).encode("utf-8")
        
        req = Request(url, data=data, headers=headers, method=method)
        
        try:
            with urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"HTTP {e.code}: {error_body}")
        except URLError as e:
            raise Exception(f"Connection error: {e.reason}")
    
    def restart_component(self, service_name, component_name, host_name=None):
        """
        重启指定组件
        
        Args:
            service_name: 服务名（如 HIVE）
            component_name: 组件名（如 HIVE_METASTORE）
            host_name: 主机名（可选，不指定则操作所有实例）
        """
        resource_filter = {
            "service_name": service_name,
            "component_name": component_name,
        }
        if host_name:
            resource_filter["hosts"] = host_name
        
        payload = {
            "RequestInfo": {
                "command": "RESTART",
                "context": f"Restart {component_name} via Ambari API",
                "operation_level": "host_component"
            },
            "Requests/resource_filters": [resource_filter]
        }
        
        return self._make_request("requests", method="POST", data=payload)
    
    def start_stop_component(self, service_name, component_name, action, host_name=None):
        """
        启动或停止指定组件
        
        Args:
            service_name: 服务名
            component_name: 组件名
            action: START 或 STOP
            host_name: 主机名（可选）
        """
        state = "STARTED" if action == "START" else "INSTALLED"
        
        resource_filter = {
            "service_name": service_name,
            "component_name": component_name,
        }
        if host_name:
            resource_filter["hosts"] = host_name
        
        payload = {
            "RequestInfo": {
                "context": f"{action} {component_name} via Ambari API",
                "operation_level": "host_component"
            },
            "Body": {
                "HostRoles": {
                    "state": state
                }
            },
            "Requests/resource_filters": [resource_filter]
        }
        
        # 使用 PUT 方法更新组件状态
        endpoint = f"services/{service_name}/components/{component_name}"
        return self._make_request(endpoint, method="PUT", data=payload)
    
    def restart_service(self, service_name):
        """重启整个服务的所有组件"""
        # 先停止服务
        print(f"停止服务 {service_name}...")
        self._change_service_state(service_name, "INSTALLED")
        
        # 再启动服务
        print(f"启动服务 {service_name}...")
        return self._change_service_state(service_name, "STARTED")
    
    def _change_service_state(self, service_name, state):
        """更改服务状态"""
        payload = {
            "RequestInfo": {
                "context": f"Change {service_name} state to {state}",
                "operation_level": "service"
            },
            "Body": {
                "ServiceInfo": {
                    "state": state
                }
            }
        }
        
        return self._make_request(f"services/{service_name}", method="PUT", data=payload)
    
    def get_request_status(self, request_id):
        """获取请求状态"""
        return self._make_request(f"requests/{request_id}")
    
    def wait_for_request(self, request_id, interval=5, max_attempts=60):
        """
        轮询等待请求完成
        
        Returns:
            tuple: (success: bool, final_status: dict)
        """
        print(f"等待请求 {request_id} 完成...")
        
        for attempt in range(1, max_attempts + 1):
            try:
                response = self.get_request_status(request_id)
                request_info = response.get("Requests", {})
                status = request_info.get("request_status", "UNKNOWN")
                
                progress = request_info.get("progress_percent", 0)
                print(f"  尝试 {attempt}/{max_attempts}: 状态={status}, 进度={progress}%")
                
                if status == "COMPLETED":
                    print(f"\n✅ 操作成功完成！")
                    return True, request_info
                elif status in ["FAILED", "ABORTED", "TIMEDOUT"]:
                    print(f"\n❌ 操作失败！状态: {status}")
                    return False, request_info
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"  查询状态时出错: {e}")
                time.sleep(interval)
        
        print(f"\n⏱️ 轮询超时！请求仍在进行中...")
        return False, {"request_status": "POLLING_TIMEOUT"}
    
    def list_services(self):
        """列出集群中的所有服务"""
        return self._make_request("services")
    
    def list_components(self, service_name):
        """列出服务中的所有组件"""
        return self._make_request(f"services/{service_name}/components")


def mask_password(password):
    """密码脱敏"""
    if not password:
        return ""
    return "*" * min(len(password), 8)


def main():
    parser = argparse.ArgumentParser(
        description="Ambari 服务管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 重启 HIVE 的 HIVE_METASTORE 组件
  %(prog)s restart HIVE HIVE_METASTORE
  
  # 停止特定主机上的 YARN NODEMANAGER
  %(prog)s stop YARN NODEMANAGER host1.example.com
  
  # 重启整个 HDFS 服务
  %(prog)s restart HDFS
  
  # 指定自定义 Ambari 地址
  AMBARI_URL=http://ambari:8080 %(prog)s restart HBASE

环境变量:
  AMBARI_URL      - Ambari Server URL (默认: http://172.17.236.249:8080)
  AMBARI_CLUSTER  - 集群名称 (默认: HDPCluster)
  AMBARI_USER     - 用户名 (默认: admin)
  AMBARI_PASSWORD - 密码 (建议通过环境变量设置)
        """
    )
    
    parser.add_argument(
        "action",
        choices=["restart", "start", "stop"],
        help="执行的操作类型"
    )
    parser.add_argument(
        "service",
        help="服务名称 (如 HIVE, HDFS, YARN)"
    )
    parser.add_argument(
        "component",
        nargs="?",
        help="组件名称 (如 HIVE_METASTORE, DATANODE)。不指定则操作整个服务"
    )
    parser.add_argument(
        "host",
        nargs="?",
        help="目标主机 FQDN。不指定则操作所有主机上的该组件"
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("AMBARI_URL", DEFAULT_CONFIG["url"]),
        help="Ambari Server URL"
    )
    parser.add_argument(
        "--cluster",
        default=os.environ.get("AMBARI_CLUSTER", DEFAULT_CONFIG["cluster"]),
        help="集群名称"
    )
    parser.add_argument(
        "--user",
        default=os.environ.get("AMBARI_USER", DEFAULT_CONFIG["user"]),
        help="用户名"
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("AMBARI_PASSWORD", DEFAULT_CONFIG["password"]),
        help="密码 (建议通过环境变量 AMBARI_PASSWORD 设置)"
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="不等待操作完成，立即返回"
    )
    
    args = parser.parse_args()
    
    # 验证必要参数
    if not args.service:
        print("❌ 错误: 必须指定服务名称")
        parser.print_help()
        sys.exit(1)
    
    if not args.password:
        print("❌ 错误: 未设置密码。请通过 --password 参数或 AMBARI_PASSWORD 环境变量设置")
        parser.print_help()
        sys.exit(1)
    
    # 打印配置信息（脱敏）
    print("=" * 60)
    print("Ambari 服务管理")
    print("=" * 60)
    print(f"操作:      {args.action.upper()}")
    print(f"服务:      {args.service}")
    print(f"组件:      {args.component or '(全部)'}")
    print(f"主机:      {args.host or '(全部)'}")
    print(f"Ambari:    {args.url}")
    print(f"集群:      {args.cluster}")
    print(f"用户:      {args.user}")
    print(f"密码:      {mask_password(args.password)}")
    print("=" * 60)
    
    # 创建客户端
    client = AmbariClient(args.url, args.user, args.password, args.cluster)
    
    try:
        # 执行操作
        if args.component:
            # 组件级别操作
            if args.action == "restart":
                print(f"\n🔄 正在重启 {args.service}.{args.component}...")
                response = client.restart_component(
                    args.service, args.component, args.host
                )
            else:
                print(f"\n🔄 正在{args.action} {args.service}.{args.component}...")
                response = client.start_stop_component(
                    args.service, args.component, args.action.upper(), args.host
                )
        else:
            # 服务级别操作
            if args.action == "restart":
                print(f"\n🔄 正在重启服务 {args.service}...")
                response = client.restart_service(args.service)
            else:
                state = "STARTED" if args.action == "start" else "INSTALLED"
                print(f"\n🔄 正在将服务 {args.service} 状态改为 {state}...")
                response = client._change_service_state(args.service, state)
        
        # 获取请求 ID
        request_info = response.get("Requests", {})
        request_id = request_info.get("id")
        
        if not request_id:
            print("\n⚠️ 未获取到请求 ID，响应内容:")
            print(json.dumps(response, indent=2))
            sys.exit(1)
        
        print(f"✅ 请求已提交，ID: {request_id}")
        
        # 等待完成
        if not args.no_wait:
            success, final_status = client.wait_for_request(request_id)
            
            print("\n" + "=" * 60)
            print("最终状态:")
            print("=" * 60)
            print(json.dumps(final_status, indent=2))
            
            sys.exit(0 if success else 1)
        else:
            print(f"\n请求已提交，不等待结果。可通过以下命令查询状态:")
            print(f"  curl -u '{args.user}:******' '{args.url}/api/v1/clusters/{args.cluster}/requests/{request_id}'")
            
    except Exception as e:
        print(f"\n❌ 操作失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
