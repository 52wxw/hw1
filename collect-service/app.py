from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from typing import Optional

from protocols.ssh_client import SSHClient
from protocols.snmp_client import SNMPClient
from topology.lldp_parser import parse_lldp_output
import redis
import pika
from dotenv import load_dotenv

# 修复：补充导入
load_dotenv()
app = FastAPI()
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

# RabbitMQ连接（用于批量巡检任务队列）
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

# 加载厂商命令集（插件化）
def load_cmd_profile(vendor, model):
    try:
        with open(f"cmd_profiles/{vendor.lower()}_{model.lower()}.json", "r") as f:
            return json.load(f)["cmds"]
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail=f"未找到{vendor}_{model}的命令集")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="命令集配置文件格式错误")

class CollectRequest(BaseModel):
    device_id: int
    ip: str
    vendor: str
    model: str
    protocol: str
    username: str
    password: str

class TopologyRequest(BaseModel):
    device_id: int
    ip: str
    username: Optional[str] = None
    password: Optional[str] = None
    vendor: str = "华为"
    command: str = "display lldp neighbor"
    protocol: str = "ssh"
    device_name: Optional[str] = None

@app.post("/api/collect")
@app.post("/api/collect/collect")
def collect_data(req: CollectRequest):
    try:
        if req.protocol == "ssh":
            client = SSHClient(req.ip, req.username, req.password)
            cmds = load_cmd_profile(req.vendor, req.model)
            metrics = client.execute_cmds(cmds)
        elif req.protocol == "snmp":
            client = SNMPClient(req.ip, req.password, port=161)  # 修复：补充端口
            metrics = client.get_metrics(["cpu", "memory", "interface"])
        else:
            raise HTTPException(status_code=400, detail="不支持的协议（仅支持ssh/snmp）")
        
        # 缓存结果
        redis_client.set(f"metrics:{req.device_id}", json.dumps(metrics), ex=3600)
        return {"code": 200, "data": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"采集失败：{str(e)}")

# 新增：执行单条命令接口（供AI修复调用）
@app.post("/api/execute")
def execute_command(device_id: int, cmd: str, ip: str, username: str, password: str):
    try:
        client = SSHClient(ip, username, password)
        result = client.execute_single_cmd(cmd)
        return {"code": 200, "data": result}
    except Exception as e:
        return {"code": 500, "msg": f"命令执行失败：{str(e)}"}


@app.post("/api/topology/lldp")
def collect_lldp(req: TopologyRequest):
    try:
        device_name = req.device_name or req.ip
        if req.protocol.lower() == "snmp":
            if not req.password:
                raise HTTPException(status_code=400, detail="SNMP LLDP 采集需要提供community（password字段）")
            client = SNMPClient(req.ip, req.password, port=161)
            neighbors = client.get_lldp_neighbors()
            links = []
            for neighbor in neighbors:
                links.append({
                    "device_id": req.device_id,
                    "device_name": device_name,
                    "local_port": neighbor.get("local_port"),
                    "neighbor": neighbor.get("neighbor"),
                    "neighbor_port": neighbor.get("neighbor_port"),
                    "status": neighbor.get("status", "Unknown")
                })
            return {"code": 200, "data": {
                "raw": neighbors,
                "links": links
            }}
        else:
            if not req.username or not req.password:
                raise HTTPException(status_code=400, detail="SSH LLDP 采集需要提供用户名和密码")
        client = SSHClient(req.ip, req.username, req.password)
        output = client.execute_single_cmd(req.command)
        links = parse_lldp_output(req.device_id, device_name, output)
        return {"code": 200, "data": {
            "raw": output,
            "links": links
        }}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLDP 采集失败：{str(e)}")


@app.get("/api/metrics/{device_id}")
def get_cached_metrics(device_id: int):
    cache_key = f"metrics:{device_id}"
    data = redis_client.get(cache_key)
    if not data:
        raise HTTPException(status_code=404, detail="未找到指标数据")
    try:
        metrics = json.loads(data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="缓存数据格式错误")
    return {"code": 200, "data": metrics}

# 批量巡检任务消费者
def consume_batch_inspect():
    """从RabbitMQ队列消费批量巡检任务"""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # 声明队列
        channel.queue_declare(queue='batch_inspect', durable=True)
        
        def callback(ch, method, properties, body):
            """处理巡检任务"""
            try:
                task_data = json.loads(body)
                device_id = task_data.get("device_id")
                ip = task_data.get("ip")
                vendor = task_data.get("vendor")
                model = task_data.get("model")
                protocol = task_data.get("protocol")
                username = task_data.get("username")
                password = task_data.get("password")
                
                # 执行采集
                if protocol == "ssh":
                    client = SSHClient(ip, username, password)
                    cmds = load_cmd_profile(vendor, model)
                    metrics = client.execute_cmds(cmds)
                elif protocol == "snmp":
                    client = SNMPClient(ip, password, port=161)
                    metrics = client.get_metrics(["cpu", "memory", "interface"])
                else:
                    raise ValueError(f"不支持的协议：{protocol}")
                
                # 缓存结果
                redis_client.set(f"metrics:{device_id}", json.dumps(metrics), ex=3600)
                
                # 确认消息
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"设备 {device_id} 批量巡检完成")
                
            except Exception as e:
                print(f"批量巡检任务处理失败：{e}")
                # 拒绝消息并重新入队
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        # 设置消费者
        channel.basic_qos(prefetch_count=5)  # 每次最多处理5个任务
        channel.basic_consume(queue='batch_inspect', on_message_callback=callback)
        
        print("批量巡检消费者已启动，等待任务...")
        channel.start_consuming()
        
    except Exception as e:
        print(f"RabbitMQ连接失败：{e}")

# 批量巡检接口（将任务加入队列）
@app.post("/api/collect/batch")
def batch_collect(data: dict):
    """批量巡检：将任务加入RabbitMQ队列"""
    device_list = data.get("devices", [])
    
    if not device_list:
        raise HTTPException(status_code=400, detail="设备列表不能为空")
    
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue='batch_inspect', durable=True)
        
        # 将每个设备任务加入队列
        for device in device_list:
            message = json.dumps(device)
            channel.basic_publish(
                exchange='',
                routing_key='batch_inspect',
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)  # 消息持久化
            )
        
        connection.close()
        return {"code": 200, "msg": f"已加入队列 {len(device_list)} 个设备巡检任务"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加入队列失败：{str(e)}")

if __name__ == "__main__":
    import uvicorn
    import threading
    
    # 启动批量巡检消费者（后台线程）
    consumer_thread = threading.Thread(target=consume_batch_inspect, daemon=True)
    consumer_thread.start()
    
    uvicorn.run("app:app", host="0.0.0.0", port=8001)
