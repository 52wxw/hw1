"""
定时任务调度服务：支持定时巡检和触发式巡检
使用 APScheduler 实现任务调度
"""
from flask import Flask, request, jsonify
import os
import json
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pymysql
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# 数据库配置
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "mysql"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "Root@123456"),
    "database": os.getenv("MYSQL_DATABASE", "ai_inspect"),
    "charset": "utf8mb4"
}

# 服务URL
DEVICE_SERVICE_URL = os.getenv("DEVICE_SERVICE_URL", "http://device-service:8000")

# 初始化调度器
scheduler = BackgroundScheduler()
scheduler.start()

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def execute_inspect_task(task_id: int, device_ids: list):
    """执行巡检任务"""
    print(f"[{datetime.now()}] 执行任务 {task_id}，设备：{device_ids}")

    # 获取任务配置
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT auto_repair FROM inspect_task WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    auto_repair = bool(task[0]) if task else False
    conn.close()

    # 遍历设备执行巡检
    if not device_ids:
        print(f"任务 {task_id} 未配置设备，跳过")
        return

    for device_id in device_ids:
        try:
            token = f"1:{int(datetime.now().timestamp() * 1000)}"
            inspect_resp = requests.post(
                f"{DEVICE_SERVICE_URL}/api/device/{device_id}/inspect",
                json={
                    "scenario": "定时巡检",
                    "autoRepair": auto_repair
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=120
            )

            if inspect_resp.status_code != 200:
                print(f"设备 {device_id} 巡检接口调用失败：{inspect_resp.text}")
                continue

            body = inspect_resp.json()
            if body.get("code") != 200:
                print(f"设备 {device_id} 巡检失败：{body.get('msg')}")
                continue

            data = body.get("data", {})
            analysis = data.get("analysis", {})
            if not analysis:
                print(f"设备 {device_id} 巡检结果为空")
                continue

            save_inspect_report(device_id, analysis)
            print(f"设备 {device_id} 巡检完成，健康评分：{analysis.get('health_score', 0)}")

        except Exception as e:
            print(f"设备 {device_id} 巡检异常：{str(e)}")

    # 更新任务最后执行时间
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE inspect_task SET last_run_time = %s WHERE id = %s", (datetime.now(), task_id))
    conn.commit()
    conn.close()


def save_inspect_report(device_id: int, ai_result: dict):
    """保存巡检报告"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO inspect_report (device_id, inspect_time, health_score, abnormal, repair_result)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        device_id,
        datetime.now(),
        ai_result.get("health_score", 0),
        json.dumps(ai_result.get("faults", []), ensure_ascii=False),
        json.dumps(ai_result.get("repair_results", []), ensure_ascii=False)
    ))
    # 修复：添加数据库提交和连接关闭
    conn.commit()
    conn.close()

@app.post("/api/scheduler/task/add")
def add_task():
    """添加定时任务"""
    data = request.json

    # 保存任务到数据库
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO inspect_task (name, device_ids, cron_expr, trigger_type, trigger_condition, auto_repair, enabled)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get("name"),
        json.dumps(data.get("device_ids", [])),
        data.get("cron_expr"),
        data.get("trigger_type", "schedule"),
        json.dumps(data.get("trigger_condition", {})),
        data.get("auto_repair", False),
        data.get("enabled", True)
    ))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # 如果启用，添加到调度器
    if data.get("enabled", True):
        schedule_task(task_id, data.get("cron_expr"), data.get("device_ids", []))

    return jsonify({"code": 200, "data": {"id": task_id}})

def schedule_task(task_id: int, cron_expr: str, device_ids: list):
    """将任务添加到调度器"""
    # 解析Cron表达式（简化版，支持：分 时 日 月 周）
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError("Cron表达式格式错误，应为：分 时 日 月 周")

    minute, hour, day, month, day_of_week = parts

    trigger = CronTrigger(
        minute=minute if minute != '*' else None,
        hour=hour if hour != '*' else None,
        day=day if day != '*' else None,
        month=month if month != '*' else None,
        day_of_week=day_of_week if day_of_week != '*' else None
    )

    scheduler.add_job(
        execute_inspect_task,
        trigger=trigger,
        args=[task_id, device_ids],
        id=f"task_{task_id}",
        replace_existing=True
    )

@app.get("/api/scheduler/task/list")
def list_tasks():
    """获取任务列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, cron_expr, trigger_type, enabled, last_run_time FROM inspect_task")

    tasks = []
    for row in cursor.fetchall():
        tasks.append({
            "id": row[0],
            "name": row[1],
            "cron_expr": row[2],
            "trigger_type": row[3],
            "enabled": bool(row[4]),
            "last_run_time": row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else None
        })

    conn.close()
    return jsonify({"code": 200, "data": tasks})

@app.post("/api/scheduler/task/trigger")
def trigger_task():
    """手动触发任务"""
    data = request.json
    task_id = data.get("task_id")

    # 获取任务配置
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT device_ids FROM inspect_task WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    conn.close()

    if not task:
        return jsonify({"code": 404, "msg": "任务不存在"})

    device_ids = json.loads(task[0])
    execute_inspect_task(task_id, device_ids)

    return jsonify({"code": 200, "msg": "任务已触发"})

if __name__ == '__main__':
    # 启动时加载所有启用的任务
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, cron_expr, device_ids FROM inspect_task WHERE enabled = 1")
    for row in cursor.fetchall():
        try:
            schedule_task(row[0], row[1], json.loads(row[2]))
        except Exception as e:
            print(f"加载任务 {row[0]} 失败：{e}")
    conn.close()

    app.run(host='0.0.0.0', port=8003)
