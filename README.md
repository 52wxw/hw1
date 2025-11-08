# 华为设备AI智能巡检系统（毕业设计优化升级版）

## 项目简介
基于微服务架构的企业级网络运维平台，支持多厂商设备巡检、AI自主修复、3D拓扑可视化、区块链日志存证。本版本为毕业设计优化升级版，从"单设备基础巡检"升级为"多厂商、全流程、智能化、可扩展的企业级网络运维平台"。

## 核心升级亮点

### 1. 架构升级：云原生微服务
- **微服务架构**：设备管理服务（Spring Boot）、数据采集服务（FastAPI）、AI分析服务（Flask）、任务调度服务、告警服务
- **消息队列**：RabbitMQ支持批量巡检任务异步处理
- **容器化部署**：Docker Compose快速部署，支持K8s扩展

### 2. AI能力升级：多模型调度 + 智能决策
- **多模型集成**：DeepSeek-R1-7B（微调）、Llama 3 8B、Qwen 7B，场景化自动选模型
- **故障分级**：P0-P3四级故障自动识别（P0紧急、P1严重、P2重要、P3一般）
- **自动修复**：支持授权式自动修复（如接口down自动执行undo shutdown）
- **知识库**：运维知识库自迭代，支持关键词搜索

### 3. 功能增强：全流程自动化
- **定时巡检**：支持Cron表达式定时任务（如每天凌晨3点批量巡检）
- **触发式巡检**：设备指标超阈值自动触发巡检
- **多渠道告警**：邮件、企业微信、钉钉、短信多渠道告警
- **可视化监控**：HertzBeat + openGemini + Grafana 一体化监控看板，支持 3D 拓扑展示
- **自动化运维**：可选接入 StackStorm/AWX，将 AI 建议转化为标准化修复流程

### 4. 安全性升级
- **权限控制**：分角色权限（管理员/运维员/只读用户）
- **操作审计**：记录所有巡检/修复操作，支持日志导出
- **密码加密**：AES-256加密存储设备密码

## 技术栈
- **后端服务**：
  - Spring Boot（设备管理服务，端口8000）
  - FastAPI（数据采集服务，端口8001）
  - Flask（AI分析服务，端口8002）
  - Flask（任务调度服务，端口8003）
  - Flask（告警服务，端口8004）
- **前端**：Vue3 + Element Plus + Three.js（3D拓扑）
- **中间件**：
  - MySQL 8.0（业务数据 + HertzBeat 元数据）
  - Redis 7.0（缓存 + HertzBeat 状态）
  - RabbitMQ 3.12（消息队列）
  - openGemini（时序指标存储，兼容 InfluxDB）
  - HertzBeat（多协议数据采集及告警）
  - Grafana 10（可视化仪表盘）
- **AI模型**：
  - DeepSeek-R1-7B（微调版，复杂故障分析）
  - Llama 3 8B（通用巡检）
  - Qwen 7B（快速分析）
- **部署**：Docker Compose（演示）、K8s（生产环境）

## 快速部署（Docker Compose）

### 1. 环境准备
- **操作系统**：Ubuntu 22.04 / CentOS 9 / Windows 10+（WSL2）
- **Docker**：版本≥20.10
- **Docker Compose**：版本≥2.0
- **内存**：≥8GB（AI模型推理需4GB+）
- **磁盘**：≥20GB可用空间

### 2. 配置环境变量
创建 `.env` 文件（在项目根目录）：
```bash
# MySQL配置
MYSQL_ROOT_PWD=your_mysql_password

# 加密密钥（用于设备密码加密）
FERNET_KEY=your_fernet_key_32_bytes

# Ollama服务地址（AI模型服务）
OLLAMA_URL=http://localhost:11434

# 告警服务配置（可选）
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your_email@qq.com
SMTP_PASSWORD=your_email_password
FROM_EMAIL=your_email@qq.com
WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_key
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=your_token

# Grafana（可选）
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin

# HertzBeat 通知（可选）
HERTZBEAT_INFLUX_USERNAME=root
HERTZBEAT_INFLUX_PASSWORD=root
HERTZBEAT_INFLUX_BUCKET=hertzbeat
HERTZBEAT_ALERT_WEBHOOK=http://alert-service:8004/api/alert/hertzbeat

# StackStorm 自动修复（可选）
STACKSTORM_BASE_URL=https://stackstorm/api/v1
STACKSTORM_API_KEY=your_st2_api_key
# 或使用 Auth Token
# STACKSTORM_AUTH_TOKEN=xxxxxxxx
# 将故障关键字映射到 StackStorm 动作（可选）
STACKSTORM_ACTION_MAP={"接口down":"network.remediation.enable_interface","cpu":"network.remediation.cpu_optimize"}
STACKSTORM_DEFAULT_ACTION=network.remediation.generic_fix
STACKSTORM_FALLBACK_AGENT=true
```

### 3. 部署步骤
```bash
# 1. 克隆项目代码
git clone https://github.com/your-username/Huawei-AI-Inspection.git
cd Huawei-AI-Inspection

# 2. 启动所有服务（首次启动会自动构建镜像）
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

### 4. 访问服务
- **前端界面**：http://localhost:80
- **RabbitMQ管理界面**：http://localhost:15672（用户名/密码：guest/guest）
- **设备管理API**：http://localhost:8000
- **采集服务API**：http://localhost:8001
- **AI服务API**：http://localhost:8002
- **调度服务API**：http://localhost:8003
- **告警服务API**：http://localhost:8004
- **HertzBeat 控制台**：http://localhost:1157
- **Grafana 面板**：http://localhost:3000
- **openGemini (Influx 兼容)**：http://localhost:8086

## 功能使用指南

### 1. 设备管理
- **添加设备**：通过前端界面或API添加华为/思科设备
- **设备分组**：支持设备分组管理，便于批量操作
- **密码加密**：设备密码自动AES-256加密存储

### 2. 定时巡检
- **创建定时任务**：通过调度服务API创建Cron表达式定时任务
  ```bash
  POST http://localhost:8003/api/scheduler/task/add
  {
    "name": "每日凌晨巡检",
    "device_ids": [1, 2, 3],
    "cron_expr": "0 3 * * *",
    "auto_repair": true
  }
  ```
- **手动触发**：支持手动触发任务执行

### 3. AI分析
- **单设备分析**：调用AI服务分析设备健康状态
  ```bash
  POST http://localhost:8002/api/ai/analyze
  {
    "device_id": 1,
    "scenario": "通用巡检",
    "auto_repair": true
  }
  ```
- **故障分级**：自动识别P0-P3级故障
- **知识库搜索**：搜索历史故障解决方案

### 4. 告警配置
- **添加告警规则**：配置指标阈值和告警渠道
  ```bash
  POST http://localhost:8004/api/alert/config/add
  {
    "name": "CPU告警",
    "device_id": 1,
    "metric": "cpu_usage",
    "threshold": 80,
    "comparison": ">",
    "channels": ["email", "wechat"]
  }
  ```

### 5. HertzBeat + openGemini 集成
- 启动前请阅读 `docs/integration/hertzbeat-opengemini.md`
- 导入华为 AR/CE/S5700 的 YANG 模板，自定义采集任务
- Grafana 中使用 openGemini 数据源构建实时仪表盘

### 6. StackStorm 自动化修复（可选）
- 参考 `docs/integration/stackstorm.md` 部署 StackStorm 并配置 API Key
- 在 `.env` 中设置动作映射与默认流程
- AI 分析开启 `auto_repair` 后，将优先调用 StackStorm 动作执行修复，失败时可回退至本地脚本

### 7. 网络拓扑
- `/api/topology` 自动聚合 LLDP 链路，支持 SSH 命令与 SNMP LLDP-MIB 双模式采集
- 设备服务内置拓扑缓存与定时刷新，默认 5 分钟更新一次，可通过 `topology.cache.*` 配置调整
- 详情见 `docs/integration/topology.md`

### 8. 日志审计
- `deploy/logging/docker-compose.logging.yml` 可一键启动 Elasticsearch / Logstash / Kibana 与 Loki / Grafana
- Promtail 默认采集 Docker 容器日志，亦可通过 Filebeat 将应用日志发送至 Logstash
- 详情见 `docs/integration/logging-audit.md`

## 数据库结构
- `device`：设备表
- `device_group`：设备分组表
- `inspect_report`：巡检报告表
- `inspect_task`：任务调度表
- `alert_config`：告警配置表
- `alert_record`：告警记录表
- `user`：用户表（权限控制）
- `operation_log`：操作日志表（审计）

详细SQL脚本见 `sql/init.sql`

## 实验设计（毕业设计）

### 1. 模型性能对比实验
- 测试DeepSeek（微调前/后）、Llama 3、Qwen在故障识别准确率、推理速度上的差异
- 脚本：`tests/model_performance.py`

### 2. 巡检效率对比实验
- 传统人工巡检 vs AI巡检（10台设备，统计总耗时、故障漏检率）
- 脚本：`tests/protocol_test.py`

### 3. 协议效率对比实验
- SSH vs SNMP采集数据的耗时差异
- 脚本：`tests/protocol_test.py`

### 4. 压力测试
- 模拟50台虚拟设备同时巡检，测试系统并发处理能力
- 脚本：`tests/concurrent_test.py`

## 项目结构
```
bs-main/
├── device-service/          # 设备管理服务（Spring Boot）
├── collect-service/          # 数据采集服务（FastAPI）
├── ai-service/               # AI分析服务（Flask）
│   ├── model_scheduler.py   # 多模型调度器
│   ├── fault_classifier.py  # 故障分级器
│   └── knowledge_base.py    # 知识库
├── scheduler-service/        # 任务调度服务
├── alert-service/            # 告警服务
├── frontend/                 # 前端（Vue3）
├── blockchain/              # 区块链存证
├── deploy/                   # 部署配置（K8s）
├── sql/                      # 数据库脚本
├── tests/                    # 测试脚本
├── docs/                     # 文档
└── docker-compose.yml        # Docker Compose配置
```

## 常见问题

### 1. AI模型服务未启动
- 确保Ollama服务已启动：`ollama serve`
- 检查环境变量 `OLLAMA_URL` 配置是否正确

### 2. 数据库连接失败
- 检查MySQL容器是否正常运行：`docker-compose ps mysql`
- 确认环境变量 `MYSQL_ROOT_PWD` 配置正确

### 3. RabbitMQ连接失败
- 检查RabbitMQ容器状态：`docker-compose ps rabbitmq`
- 访问管理界面确认服务正常：http://localhost:15672

## 毕业设计论文结构建议
1. **引言**：研究背景、意义、国内外现状、论文结构
2. **相关技术**：AI大模型微调、微服务架构、网络自动化协议、容器编排
3. **系统需求分析**：功能需求、非功能需求、用例图
4. **系统设计**：架构设计、模块设计、数据库设计、接口设计
5. **系统实现**：核心代码、关键功能实现细节
6. **实验结果与分析**：对比实验、压力测试、结果讨论
7. **总结与展望**：系统不足、未来优化方向（如引入LLM Agent实现自主运维）

## 答辩演示亮点
- **3分钟快速演示**：设备拓扑自动绘制→定时巡检触发→AI识别故障→企业微信告警→自动修复→报告导出
- **技术深度展示**：模型微调数据集样本、故障识别准确率对比图表、微服务架构调用链路
- **工程实用性**：强调方案可直接迁移至企业生产环境，提供部署脚本和运维手册

## 许可证
MIT License

## 联系方式
如有问题，请提交Issue或联系项目维护者。
