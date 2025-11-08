# HertzBeat + openGemini + Grafana 集成说明

本文档记录了如何在本项目中启用 HertzBeat 采集、openGemini 时序存储以及 Grafana 可视化。整体目标是：

```
真实网络设备 ──> HertzBeat 多协议采集 ──> openGemini (时序库)
                                         │
                                         └──> Grafana 仪表盘 / AI 分析 / 告警
```

## 1. 组件概览

| 组件 | 作用 | 暴露端口 | 说明 |
|------|------|----------|------|
| `opengemini` | 时序数据库，兼容 InfluxDB 协议 | 8086 (HTTP API)、8088 (RPC) | 采集指标与异常检测的底座 |
| `hertzbeat` | 多协议采集器 + 告警管理 | 1157 (Web UI) | 支持 SSH / SNMP / Syslog，自定义华为 YANG 模板 |
| `grafana` | 可视化仪表盘 | 3000 | 通过 openGemini 数据源展示实时/历史指标 |

以上组件已经在 `docker-compose.yml` 中定义，可与原有服务一键启动。

## 2. 环境准备

1. **环境变量**：确保 `.env` 中已经设置 `MYSQL_ROOT_PWD`；Grafana 管理员账号可选地通过 `GRAFANA_ADMIN_USER`、`GRAFANA_ADMIN_PASSWORD` 覆盖。
2. **MySQL 初始化**：项目启动时会自动创建 `hertzbeat` 数据库，供 HertzBeat 元数据使用。
3. **目录结构**：

```
infra/
  hertzbeat/
    application.yml   # 覆盖 HertzBeat 默认配置
```

## 3. 启动流程

```bash
docker-compose up -d opengemini hertzbeat grafana
```

> 首次启动 openGemini 可能需要数秒完成内部组件初始化，可通过 `docker logs opengemini` 查看状态。

启动成功后访问：

- HertzBeat Web 控制台：http://localhost:1157 （默认账号：`admin/hertzbeat`）
- Grafana：http://localhost:3000 （默认账号：`admin/admin`，启动时可通过环境变量覆盖）

## 4. HertzBeat 配置要点

1. **数据仓库**：`infra/hertzbeat/application.yml` 已将指标仓库设置为 `http://opengemini:8086`，利用 openGemini 的 Influx 兼容接口。根据实际部署需要，可调整账号、密码、bucket 等参数。
2. **Redis**：HertzBeat 默认将任务状态、告警缓存保存在 Redis，配置中使用了项目已有的 `redis:6379` 库 `2`。
3. **Webhook**：已预留 `HERTZBEAT_ALERT_WEBHOOK`，默认回调到 `alert-service`；若需使用 HertzBeat 自带的邮件/短信，修改配置即可。
4. **导入 YANG 模板**：
   - 登录 HertzBeat Web → “监控模板” → 导入华为 AR / CE / S5700 的 YANG 配置（支持 JSON/YAML）。
   - 创建监控任务时选择自定义模板，配置设备 IP、认证方式（SSH 密钥 / SNMP community 等）。
   - 若需要 Syslog，参考 HertzBeat 官方文档配置日志采集，并将日志流向 openGemini（可通过 Kafka 中转）。
5. **Webhook 告警回调**：
   - 在 HertzBeat 控制台 → “通知” → “WebHook” 中新增回调地址 `http://alert-service:8004/api/alert/hertzbeat`
   - HertzBeat 的优先级会映射到本系统的 `critical/warning/info` 等级，并通过 `alert-service` 继续下发邮件、企业微信、钉钉、短信
   - 如果部署在宿主机，可使用 `http://<宿主机IP>:8004/api/alert/hertzbeat`

## 5. Grafana 接入步骤

1. 登录 Grafana → `Connections` → `Data sources` → 新增 InfluxDB 数据源。
2. 类型选择 **InfluxDB**，URL 填写 `http://opengemini:8086`，数据库填写 `hertzbeat`（或自定义 bucket），认证信息与 HertzBeat 配置保持一致。
3. 导入仪表盘：
   - HertzBeat 官方提供了若干 Grafana Dashboard JSON，可在控制台导出/导入。
   - 也可以从 `docs/integration/dashboards`（待补充）导入项目自定义模板。
4. 若需 3D 拓扑面板，可安装 `grafana-threejs-panel` 或通过本项目自带的 `Topology3D.vue` 调用 openGemini API 获取节点状态。

## 6. 与现有服务的打通

- **AI 服务**：`ai-service` 未来可直接从 openGemini 拉取指标，避免重复采集。建议新增 API `/api/metrics/{deviceId}` 读取 openGemini 数据。
- **巡检调度**：`scheduler-service` 可以通过 HertzBeat 的 REST API 创建/触发任务（详见官方文档 `/api/v1/monitor` 等接口）。
- **告警联动**：HertzBeat 告警 → webhook → `alert-service`，统一走邮件/企业微信/短信渠道。必要时可在 webhook 中携带 monitorId、指标名称等元数据，便于追溯。

## 7. 常见问题

1. **openGemini 端口冲突或启动失败**：检查宿主机是否占用 8086/8088；可在 compose 中修改映射端口。
2. **HertzBeat 连接 TSDB 失败**：确认 openGemini 8086 接口可访问，账号密码正确（默认 root/root）。可使用 `curl http://localhost:8086/ping` 测试。
3. **Grafana 无数据**：
   - 检查 HertzBeat 任务是否在运行，指标是否写入 openGemini（可通过 `curl` 或 `ts-cli` 查询）。
   - 确认 Grafana 数据源数据库名/精度配置正确。
4. **真实设备认证问题**：建议优先使用 SSH 密钥；对于 SNMPv3 设备，在 HertzBeat 模板中开启安全配置项。

## 8. 后续工作建议

- 将 `collect-service` 中的手动巡检结果同步写入 openGemini，保持指标源一致性。
- 编写脚本自动化导入华为 YANG 模板和常用 Grafana 面板，便于快速部署新环境。
- 结合 openGemini 内置 AI 异常检测能力，将结果写入 `alert-service`，实现智能告警。
- 若需要大规模部署，可考虑将 HertzBeat 与 openGemini 独立于主 Compose，通过 Helm Chart 或单独的 Compose 进行运维。

> 更多参数与高级配置，请参考官方文档：
> - HertzBeat: https://hertzbeat.com/
> - openGemini: https://opengemini.org/
> - Grafana: https://grafana.com/docs/


