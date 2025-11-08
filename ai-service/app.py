from flask import Flask, request, jsonify
import json
import os
import time
import hashlib
import redis
from agent.network_agent import NetworkAgent
from model_scheduler import ModelScheduler
from fault_classifier import FaultClassifier
from knowledge_base import KnowledgeBase
from dotenv import load_dotenv

# 修复：补充导入
load_dotenv()
app = Flask(__name__)
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

# 初始化Agent
agent = NetworkAgent(
    ollama_url=os.getenv("OLLAMA_URL"),
    collect_service_url=os.getenv("COLLECT_SERVICE_URL")
)

# 初始化多模型调度器
model_scheduler = ModelScheduler(os.getenv("OLLAMA_URL"))

# 初始化故障分级器
fault_classifier = FaultClassifier()

# 初始化知识库
knowledge_base = KnowledgeBase()

@app.post("/api/ai/analyze")
def analyze():
    data = request.json
    device_id = data.get("device_id")
    scenario = data.get("scenario", "通用巡检")  # 巡检场景
    auto_repair = data.get("auto_repair", False)  # 是否自动修复

    if not device_id:
        return jsonify({"code": 400, "msg": "设备ID不能为空"})

    # 获取采集数据
    metrics_str = redis_client.get(f"metrics:{device_id}")
    if not metrics_str:
        return jsonify({"code": 404, "msg": "未找到设备采集数据"})
    metrics = json.loads(metrics_str)

    # 构建提示词
    prompt = f"""分析设备{device_id}的指标，输出：
    1. 健康评分（0-100）及依据（关键指标阈值对比）；
    2. 异常项（严重等级P0-P3，附日志证据）；
    3. 修复建议（厂商专用命令）；
    4. 推理链路（步骤拆解）。
    指标：{json.dumps(metrics, ensure_ascii=False)}"""

    try:
        # 使用多模型调度器选择最优模型
        model_result = model_scheduler.predict(prompt, scenario=scenario)
        report = model_result["result"]

        # 故障分级
        faults = fault_classifier.classify(report, metrics)

        # 计算健康评分
        health_score = calculate_health_score(metrics, faults)

        # 知识库联动：搜索相关解决方案
        knowledge_solutions = []
        for fault in faults[:3]:  # 只搜索前3个故障
            solutions = knowledge_base.search(fault["description"], limit=2)
            knowledge_solutions.extend(solutions)

        # 自动修复（仅保留本地agent修复，删除StackStorm逻辑）
        repair_results = []
        if auto_repair:
            for fault in faults:
                if fault.get("auto_repairable") and fault["level"] in ["P3", "P2"]:
                    fault_results = []
                    try:
                        repair_result = agent.auto_heal(device_id, fault["description"])
                        agent_success = "成功" in repair_result or "完成" in repair_result
                        fault_results.append({
                            "fault": fault["description"],
                            "result": repair_result,
                            "success": agent_success,
                            "provider": "agent"
                        })
                        if agent_success:
                            knowledge_base.add(
                                keyword=fault["description"],
                                title=f"自动修复：{fault['description']}",
                                solution=repair_result,
                                fault_level=fault["level"]
                            )
                    except Exception as e:
                        fault_results.append({
                            "fault": fault["description"],
                            "result": f"本地修复失败：{str(e)}",
                            "success": False,
                            "provider": "agent"
                        })
                    repair_results.extend(fault_results)

        # 计算报告哈希（用于日志记录）
        report_hash = hashlib.sha256(report.encode()).hexdigest()

        return jsonify({
            "code": 200,
            "data": {
                "report": report,
                "health_score": health_score,
                "faults": faults,
                "model_info": {
                    "model": model_result.get("model", "unknown"),
                    "time_cost": model_result.get("time_cost", 0),
                    "accuracy": model_result.get("accuracy", 0)
                },
                "knowledge_solutions": knowledge_solutions,
                "repair_results": repair_results,
                "evidence": extract_evidence(report),
                "log_hash": report_hash
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": f"分析失败：{str(e)}"})

def calculate_health_score(metrics: dict, faults: list) -> int:
    """计算健康评分（0-100）"""
    base_score = 100

    # 根据故障等级扣分
    fault_penalty = {"P0": 30, "P1": 20, "P2": 10, "P3": 5}
    for fault in faults:
        base_score -= fault_penalty.get(fault["level"], 0)

    # 根据指标扣分
    if metrics.get("cpu_usage", 0) > 80:
        base_score -= 10
    if metrics.get("memory_usage", 0) > 90:
        base_score -= 10

    return max(0, min(100, base_score))

def extract_evidence(report):
    """提取关键证据"""
    if not report:
        return []  # 修复：处理空报告
    evidence = []
    for line in report.split("\n"):
        if "依据：" in line or "证据：" in line or "日志：" in line:
            evidence.append(line.strip())
    return evidence

# 新增：知识库搜索接口
@app.get("/api/ai/knowledge/search")
def search_knowledge():
    keyword = request.args.get("keyword", "")
    if not keyword:
        return jsonify({"code": 400, "msg": "搜索关键词不能为空"})

    results = knowledge_base.search(keyword)
    return jsonify({"code": 200, "data": results})

# 新增：添加知识库条目接口
@app.post("/api/ai/knowledge/add")
def add_knowledge():
    data = request.json
    knowledge_id = knowledge_base.add(
        keyword=data.get("keyword"),
        title=data.get("title"),
        solution=data.get("solution"),
        device_type=data.get("device_type"),
        fault_level=data.get("fault_level")
    )
    return jsonify({"code": 200, "data": {"id": knowledge_id}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002)
