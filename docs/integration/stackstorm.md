# StackStorm 集成指南

本指南说明如何将 StackStorm 作为自动化运维平台，配合 `ai-service` 实现 AI 建议 → 自动修复 的闭环。

## 1. 组件概览

- **StackStorm**：事件驱动自动化平台，提供 Workflow/Action 管理、规则引擎与审计。
- **本项目**：AI 分析模块在识别可自动修复的故障后，会调用 StackStorm REST API 执行对应动作。在执行失败时可回退到本地 `NetworkAgent`。

## 2. 前置条件

1. 已部署 StackStorm（参考官方 [Quick Start](https://docs.stackstorm.com/install/) 或 Docker 镜像）。
2. 创建 API Key 或 Auth Token（`st2 apikey create` / `st2 auth`）。
3. 准备网络自动化 Pack，例如：
   - 官方 `network_essentials`
   - 社区 Pack（Ansible / Napalm / Netmiko 等）
   - 自定义动作（可使用 Python、Bash、Ansible Playbook 等）

## 3. 配置环境变量

在 `.env` 中新增：

```bash
STACKSTORM_BASE_URL=https://stackstorm.example.com/api/v1
STACKSTORM_API_KEY=xxxxxxxxxxxxxxxx
# 可选：使用 Auth Token
# STACKSTORM_AUTH_TOKEN=yyyyyyyyyyyyyyyy

# 故障关键字 → StackStorm 动作的映射（JSON）
STACKSTORM_ACTION_MAP={
  "接口down": "network.remediation.enable_interface",
  "cpu": "network.remediation.reduce_cpu"
}

# 未匹配到关键字时的默认动作
STACKSTORM_DEFAULT_ACTION=network.remediation.generic_fix

# StackStorm 执行失败后是否回退到本地 NetworkAgent
STACKSTORM_FALLBACK_AGENT=true

# 请求超时时间（秒，默认 15）
# STACKSTORM_TIMEOUT=20

# 是否验证 HTTPS 证书（默认为 true）
# STACKSTORM_VERIFY_SSL=false
```

> `STACKSTORM_ACTION_MAP` 中的键为故障描述中的关键词（按小写匹配），值为 StackStorm `pack.action`。

## 4. AI 服务行为说明

1. `auto_repair` 开启时，`ai-service` 会尝试：
   - 匹配故障描述 → StackStorm 动作
   - 调用 `/executions` 触发 Action，并记录 `execution_id`、状态等信息
   - 如果执行状态为 `succeeded/success/completed`，判定修复成功
   - 失败时根据 `STACKSTORM_FALLBACK_AGENT` 决定是否继续尝试本地 `NetworkAgent`
2. 成功的修复会自动写入知识库，便于后续检索。
3. 返回结构示例：

```json
"repair_results": [
  {
    "fault": "接口Gig0/0/1 down",
    "result": "StackStorm 动作 network.remediation.enable_interface 状态：succeeded (execution: 640c8...)",
    "success": true,
    "provider": "stackstorm",
    "details": {
      "id": "640c8...",
      "status": "succeeded",
      "action": {"ref": "network.remediation.enable_interface"},
      "result": {"stdout": "..."}
    }
  }
]
```

## 5. 在 StackStorm 中定义动作

示例：使用 Netmiko 重新启用接口

```yaml
# packs/network/actions/enable_interface.yaml
---
description: Enable interface via Netmiko
runner_type: python-script
entry_point: enable_interface.py
parameters:
  device_id:
    type: string
    required: true
  fault_description:
    type: string
  fault_level:
    type: string
```

```python
# packs/network/actions/enable_interface.py
from st2common.runners.base_action import Action


class EnableInterfaceAction(Action):
    def run(self, device_id, fault_description=None, fault_level=None):
        # 根据 device_id 查询设备信息，可调用外部 API 或配置管理数据库
        # 这里简化为伪代码
        ip, username, password = lookup_device(device_id)
        interface = parse_interface_from_fault(fault_description)
        enable_interface(ip, username, password, interface)
        return {"result": f"Interface {interface} enabled"}
```

> 实际实现可结合 Ansible、Netmiko、RESTConf 等工具。

## 6. 与现有系统协同

- **告警联动**：HertzBeat → `alert-service` → StackStorm（可通过 StackStorm Rule 触发）
- **巡检调度**：StackStorm 完成修复后可调用 `scheduler-service` / `device-service` 进行验证
- **审计**：StackStorm 自带执行记录，可与 `operation_log` 结合导出

## 7. 常见问题

| 问题 | 解决办法 |
|------|-----------|
| `STACKSTORM_ACTION_MAP` 解析失败 | 确认 JSON 格式是否正确，建议使用双引号 |
| API 返回 401/403 | 检查 API Key / Auth Token 是否有效，URL 是否指向 `/api/v1` |
| HTTPS 证书错误 | 将 `STACKSTORM_VERIFY_SSL=false`（仅限测试环境），或导入 CA 证书 |
| 无动作匹配 | 设置 `STACKSTORM_DEFAULT_ACTION` 或完善映射表 |

## 8. 参考资料

- StackStorm 官方文档：https://docs.stackstorm.com/
- 社区 Pack 列表：https://exchange.stackstorm.org/
- Ansible AWX（可与 StackStorm 互补）：https://github.com/ansible/awx


