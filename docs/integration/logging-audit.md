# 日志审计集成（ELK + Loki）

本指南说明如何使用 `deploy/logging/docker-compose.logging.yml` 快速部署 Elasticsearch / Logstash / Kibana（ELK）与 Loki / Promtail / Grafana，实现统一日志采集、查询与审计。

## 1. 部署拓扑

1. 进入 `deploy/logging` 目录，执行 `docker compose -f docker-compose.logging.yml up -d` 启动所有组件。
2. 部署将创建以下端口：
   - Elasticsearch: `9200`
   - Logstash Beats 输入: `5044`
   - Kibana: `5601`
   - Loki API: `3100`
   - Grafana: `3000`
3. Grafana 默认账号密码为 `admin/admin`，可通过环境变量 `GRAFANA_USER`、`GRAFANA_PASSWORD` 覆盖。

## 2. 日志采集

- **容器日志（Loki）**：Promtail 默认挂载 Docker 容器日志目录 `/var/lib/docker/containers` 并追加元数据标签 `job=container-logs`。确保主机运行 Docker 引擎且容器路径对 Promtail 可读。
- **应用文件日志（ELK）**：如需采集宿主机文件，可在 Logstash 前增加 Filebeat 或直接把日志通过 Beats 协议发送到 `logstash:5044`，同时在 event 中补充 `fields.service` 字段标识来源服务。

示例 Filebeat 片段：

```yaml
filebeat.inputs:
  - type: filestream
    id: device-service
    enabled: true
    paths:
      - /var/log/bs/device-service/*.log
    fields:
      service: device-service

output.logstash:
  hosts: ["127.0.0.1:5044"]
```

## 3. Grafana 可视化

Grafana 在启动时会自动导入以下配置：

- `Loki` 数据源：用于查询容器日志。
- `Elasticsearch-Logs` 数据源：用于聚合结构化日志。
- `Logging Overview` 仪表板：包含 Loki 日志面板与基于 Elasticsearch 的最近日志表格展示，可在 `Logging` 文件夹中查看。

访问 `http://<宿主机IP>:3000/` 登录 Grafana，即可在单一界面同时审计 Loki 与 ELK 数据。

## 4. Kibana 查询

访问 `http://<宿主机IP>:5601/` 打开 Kibana，可通过 `Discover` 建立 `bs-logs-*` 索引模式（`@timestamp` 字段），进行全文检索与告警。

## 5. 与业务服务集成

- 在主 `docker-compose.yml` 中为各服务追加 `logging` 配置或挂载文件路径，便于 Promtail / Filebeat 采集。
- 可将 `deploy/logging` Compose 与主 Compose 放在同一网络，或在主 Compose 中新增 `extra_hosts` 指向日志组件。
- 若需在 `device-service` 中记录操作审计，可调用 `OperationLogService` 并将日志输出到文件，再由 Filebeat 推送至 ELK。

## 6. 扩展建议

- 可为 Logstash 添加 GeoIP/IP2Region 等过滤器，增强审计信息。
- 使用 Loki Alerting 或 Grafana Mimir/Loki Ruler 创建日志告警规则并回调到 AI 服务。
- 生产环境需考虑 Elasticsearch 鉴权、TLS 与磁盘规划，建议对接外部对象存储或 S3 兼容系统保存 Loki Chunk。

