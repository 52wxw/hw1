# 拓扑可视化集成指南

本指南描述如何利用设备 LLDP 数据构建实时网络拓扑，并在前端 3D 视图和 Grafana 中展示。

## 1. 数据来源

1. **LLDP 采集**：`collect-service` 提供 `/api/topology/lldp` 接口，可通过 SSH 执行 `display lldp neighbor`（可自定义命令）或直接基于 SNMP LLDP-MIB 拉取邻居表。
2. **Topology API**：`device-service` 的 `/api/topology` 会遍历所有设备，自动解密凭证、查询 `collect-service`，合并双向链路并生成节点坐标。
3. **前端展示**：`Topology3D.vue` 调用 `/api/topology` 并使用 Three.js 渲染 3D 拓扑，节点颜色反映厂商、发光状态反映在线/离线。

## 2. 使用步骤

1. 确保设备已启用 LLDP，且账号有执行 `display lldp neighbor` 权限。
2. 启动所有服务后，访问前端的“拓扑”页面，点击“刷新拓扑”即可拉取最新缓存结果；后端默认每 5 分钟自动刷新一次。
3. 如果需要定制命令，可在请求体中覆盖 `command` 参数（例如调用自定义脚本），或在 `collect-service/topology/lldp_parser.py` 中扩展解析逻辑。启用 SNMP 采集时，将设备 `protocol` 设置为 `snmp`，并在密码字段填写 community。

## 3. 缓存配置

`device-service` 默认开启拓扑缓存，可通过以下属性调整（均支持环境变量覆盖）：

| 属性 | 环境变量 | 默认值 | 说明 |
|------|----------|--------|------|
| `topology.cache.enabled` | `TOPOLOGY_CACHE_ENABLED` | `true` | 是否开启缓存与定时刷新 |
| `topology.cache.ttl` | `TOPOLOGY_CACHE_TTL_SECONDS` | `300` | 缓存有效期（秒） |
| `topology.cache.refresh-interval` | `TOPOLOGY_CACHE_REFRESH_MS` | `300000` | 定时刷新周期（毫秒） |

如果需要及时看到链路变化，可暂时关闭缓存（`TOPOLOGY_CACHE_ENABLED=false`）或调小 `ttl`/`refresh-interval` 配置；也可编写额外任务在缓存过期后调用 `/api/topology` 接口获取最新结果。

## 4. Grafana 结合建议

- 可以在 Grafana 中安装 3D/网络拓扑插件（如 `threejs-panel`）并直接调用 `/api/topology` 数据。
- 另可结合 openGemini 指标，在 Grafana 图表中叠加链路利用率、设备 CPU/内存等信息。

## 5. 常见问题

| 问题 | 解决办法 |
|------|-----------|
| 无法登录设备 | 确认 `device` 表中账号密码正确且支持 SSH 登录 |
| 拓扑只有部分链路 | 检查所有设备是否都启用 LLDP；SNMP 采集需确认 community 权限，部分厂商需额外命令开启全局发现 |
| 性能问题 | 已内置内存缓存和定时刷新，如需跨实例共享可扩展为 Redis/数据库缓存 |

## 6. 后续扩展

- 将拓扑结果写入 Redis 或数据库，实现多实例共享及历史对比。
- 为链路补充带宽、延迟等指标，可从 openGemini 拉取历史数据。
- 若需要更专业的网络控制器，可评估整合 OpenDaylight/ONOS 的拓扑 API。


