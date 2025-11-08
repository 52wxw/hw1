"""
告警服务：支持邮件、企业微信、短信多渠道告警
"""
from flask import Flask, request, jsonify
import os
import json
import pymysql
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Tuple
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# 数据库配置
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "mysql"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "root"),
    "database": os.getenv("MYSQL_DATABASE", "ai_inspect"),
    "charset": "utf8mb4"
}

# 告警渠道配置
EMAIL_CONFIG = {
    "smtp_host": os.getenv("SMTP_HOST", "smtp.qq.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", 587)),
    "smtp_user": os.getenv("SMTP_USER", ""),
    "smtp_password": os.getenv("SMTP_PASSWORD", ""),
    "from_email": os.getenv("FROM_EMAIL", "")
}

WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK", "")  # 企业微信机器人Webhook
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK", "")  # 钉钉机器人Webhook
DEFAULT_ALERT_CONFIG_NAME = os.getenv("DEFAULT_ALERT_CONFIG_NAME", "HERTZBEAT_DEFAULT")

PRIORITY_LEVEL_MAP = {
    "CRITICAL": "critical",
    "EMERGENCY": "critical",
    "HIGH": "critical",
    "MAJOR": "critical",
    "MEDIUM": "warning",
    "LOW": "info",
    "INFO": "info"
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def send_email(to_email: str, subject: str, content: str) -> bool:
    """发送邮件告警"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["from_email"]
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["smtp_user"], EMAIL_CONFIG["smtp_password"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"邮件发送失败：{e}")
        return False

def send_wechat(message: str) -> bool:
    """发送企业微信告警"""
    if not WECHAT_WEBHOOK:
        return False
    
    try:
        data = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        resp = requests.post(WECHAT_WEBHOOK, json=data, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"企业微信发送失败：{e}")
        return False

def send_dingtalk(message: str) -> bool:
    """发送钉钉告警"""
    if not DINGTALK_WEBHOOK:
        return False
    
    try:
        data = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        resp = requests.post(DINGTALK_WEBHOOK, json=data, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"钉钉发送失败：{e}")
        return False

def send_sms(phone: str, message: str) -> bool:
    """发送短信告警（需要接入短信服务商API）"""
    # 这里需要接入阿里云、腾讯云等短信服务
    # 示例：调用阿里云短信API
    print(f"短信发送到 {phone}：{message}")
    return True

def fetch_recipients() -> List[Tuple[str, str]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, phone FROM user WHERE role IN ('admin', 'operator')")
    recipients = cursor.fetchall()
    conn.close()
    return recipients

def ensure_default_alert_config() -> Tuple[int, List[str]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, channels FROM alert_config WHERE name = %s LIMIT 1", (DEFAULT_ALERT_CONFIG_NAME,))
    row = cursor.fetchone()
    if row:
        config_id = row[0]
        channels = json.loads(row[1]) if row[1] else []
        conn.close()
        return config_id, channels

    default_channels = ["email", "wechat", "dingtalk", "sms"]
    cursor.execute(
        """
        INSERT INTO alert_config (name, device_id, metric, threshold, comparison, channels, enabled)
        VALUES (%s, NULL, %s, %s, %s, %s, %s)
        """,
        (
            DEFAULT_ALERT_CONFIG_NAME,
            "generic",
            0,
            ">",
            json.dumps(default_channels),
            True
        )
    )
    config_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return config_id, default_channels

def execute_channels(channels: List[str], recipients: List[Tuple[str, str]], alert_name: str, message: str):
    send_results = {}
    combined_message = f"{alert_name}\n{message}" if alert_name else message

    if "email" in channels:
        for email, _ in recipients:
            if email:
                send_results[f"email_{email}"] = send_email(
                    email,
                    f"【网络巡检告警】{alert_name}",
                    message
                )

    if "wechat" in channels:
        send_results["wechat"] = send_wechat(combined_message)

    if "dingtalk" in channels:
        send_results["dingtalk"] = send_dingtalk(combined_message)

    if "sms" in channels:
        for _, phone in recipients:
            if phone:
                send_results[f"sms_{phone}"] = send_sms(phone, combined_message)

    return send_results

def record_alert(alert_config_id, device_id, metric_value, level, message, channels, send_results):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO alert_record (alert_config_id, device_id, metric_value, alert_level, message, channels, send_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            alert_config_id,
            device_id,
            metric_value,
            level,
            message,
            json.dumps(channels),
            "success" if any(send_results.values()) else "failed"
        )
    )
    conn.commit()
    conn.close()

def process_alert(alert_config_id, device_id, metric, metric_value, message, level="warning", title=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT channels, name FROM alert_config WHERE id = %s", (alert_config_id,))
    config = cursor.fetchone()
    conn.close()

    if not config:
        return None, "告警配置不存在"

    channels = json.loads(config[0]) if config[0] else []
    alert_name = title or config[1] or "告警通知"
    recipients = fetch_recipients()

    send_results = execute_channels(channels, recipients, alert_name, message)
    record_alert(alert_config_id, device_id, metric_value, level, message, channels, send_results)

    return send_results, None

@app.post("/api/alert/send")
def send_alert():
    """发送告警"""
    data = request.json
    
    device_id = data.get("device_id")
    alert_config_id = data.get("alert_config_id")
    metric = data.get("metric")
    metric_value = data.get("metric_value")
    message = data.get("message", f"设备 {device_id} 指标 {metric} 异常：{metric_value}")
    
    send_results, error = process_alert(
        alert_config_id=alert_config_id,
        device_id=device_id,
        metric=metric,
        metric_value=metric_value,
        message=message,
        level="warning"
    )

    if error:
        return jsonify({"code": 404, "msg": error})

    return jsonify({"code": 200, "data": send_results})

def resolve_device_id_by_target(target: str):
    if not target:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM device WHERE ip = %s LIMIT 1", (target,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def build_hertzbeat_message(alert: dict, priority: str, target: str) -> str:
    parts = ["[HertzBeat 告警]", alert.get("content") or alert.get("alert") or "检测到异常"]
    if alert.get("monitorName"):
        parts.append(f"监控对象：{alert['monitorName']}")
    if target:
        parts.append(f"目标：{target}")
    if alert.get("metric"):
        parts.append(f"指标：{alert['metric']}")
    expected = alert.get("expected") or alert.get("threshold")
    actual = alert.get("actual") or alert.get("collectValue") or alert.get("value")
    if expected is not None and actual is not None:
        parts.append(f"阈值：{expected}，实际值：{actual}")
    parts.append(f"优先级：{priority or 'UNKNOWN'}")
    trigger_time = alert.get("triggerTime")
    if trigger_time:
        try:
            ts_raw = float(trigger_time)
            if ts_raw > 1e12:
                ts_raw = ts_raw / 1000
            parts.append(f"触发时间：{datetime.fromtimestamp(ts_raw).strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception:
            pass
    return "\n".join(parts)

@app.post("/api/alert/hertzbeat")
def receive_hertzbeat_alert():
    payload = request.json
    if not payload:
        return jsonify({"code": 400, "msg": "空告警数据"}), 400

    alerts = payload if isinstance(payload, list) else [payload]
    config_id, _ = ensure_default_alert_config()
    processed_results = []

    for alert in alerts:
        if not isinstance(alert, dict):
            continue

        priority = str(alert.get("priority", "")).upper()
        level = PRIORITY_LEVEL_MAP.get(priority, "warning")
        target = alert.get("target") or alert.get("tags", {}).get("ip") if isinstance(alert.get("tags"), dict) else None
        device_id = resolve_device_id_by_target(target)
        metric = alert.get("metric") or alert.get("monitorName") or alert.get("app") or "unknown"
        metric_raw = alert.get("actual") or alert.get("collectValue") or alert.get("value")
        try:
            metric_value = float(metric_raw)
        except (TypeError, ValueError):
            metric_value = 0
        message = build_hertzbeat_message(alert, priority, target)

        send_results, error = process_alert(
            alert_config_id=config_id,
            device_id=device_id,
            metric=metric,
            metric_value=metric_value,
            message=message,
            level=level,
            title="HertzBeat 告警"
        )

        processed_results.append({
            "monitorId": alert.get("monitorId"),
            "priority": priority,
            "level": level,
            "send_results": send_results,
            "error": error
        })

    if not processed_results:
        return jsonify({"code": 400, "msg": "未识别到有效告警"}), 400

    return jsonify({"code": 200, "data": processed_results})

@app.post("/api/alert/config/add")
def add_alert_config():
    """添加告警配置"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alert_config (name, device_id, metric, threshold, comparison, channels, enabled)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get("name"),
        data.get("device_id"),
        data.get("metric"),
        data.get("threshold"),
        data.get("comparison", ">"),
        json.dumps(data.get("channels", [])),
        data.get("enabled", True)
    ))
    
    config_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"code": 200, "data": {"id": config_id}})

@app.get("/api/alert/config/list")
def list_alert_configs():
    """获取告警配置列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, device_id, metric, threshold, enabled FROM alert_config")
    
    configs = []
    for row in cursor.fetchall():
        configs.append({
            "id": row[0],
            "name": row[1],
            "device_id": row[2],
            "metric": row[3],
            "threshold": float(row[4]),
            "enabled": bool(row[5])
        })
    
    conn.close()
    return jsonify({"code": 200, "data": configs})

@app.get("/api/alert/record/list")
def list_alert_records():
    """获取告警记录列表"""
    device_id = request.args.get("device_id")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if device_id:
        cursor.execute("""
            SELECT id, device_id, metric_value, alert_level, message, send_status, create_time
            FROM alert_record WHERE device_id = %s ORDER BY create_time DESC LIMIT 50
        """, (device_id,))
    else:
        cursor.execute("""
            SELECT id, device_id, metric_value, alert_level, message, send_status, create_time
            FROM alert_record ORDER BY create_time DESC LIMIT 50
        """)
    
    records = []
    for row in cursor.fetchall():
        records.append({
            "id": row[0],
            "device_id": row[1],
            "metric_value": float(row[2]),
            "alert_level": row[3],
            "message": row[4],
            "send_status": row[5],
            "create_time": row[6].strftime("%Y-%m-%d %H:%M:%S")
        })
    
    conn.close()
    return jsonify({"code": 200, "data": records})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8004)


