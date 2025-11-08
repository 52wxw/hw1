import json
import os
from typing import Any, Dict, Optional

import requests


def _to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


class StackStormClient:
    """轻量封装 StackStorm REST API，用于触发自动化运维流程"""

    def __init__(self) -> None:
        self.base_url = os.getenv("STACKSTORM_BASE_URL")
        self.api_key = os.getenv("STACKSTORM_API_KEY")
        self.auth_token = os.getenv("STACKSTORM_AUTH_TOKEN")
        self.verify_ssl = _to_bool(os.getenv("STACKSTORM_VERIFY_SSL", "true"), default=True)
        self.default_action = os.getenv("STACKSTORM_DEFAULT_ACTION")
        self._action_map = self._load_action_map()

    def _load_action_map(self) -> Dict[str, str]:
        mapping = {}
        raw = os.getenv("STACKSTORM_ACTION_MAP", "")
        if not raw:
            return mapping
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                mapping = {str(k).lower(): str(v) for k, v in loaded.items() if v}
        except json.JSONDecodeError:
            pass
        return mapping

    def is_enabled(self) -> bool:
        return bool(self.base_url and (self.api_key or self.auth_token))

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["St2-Api-Key"] = self.api_key
        if self.auth_token:
            headers["X-Auth-Token"] = self.auth_token
        return headers

    def resolve_action(self, fault_description: str) -> Optional[str]:
        if not fault_description:
            return self.default_action
        description = fault_description.lower()
        for keyword, action in self._action_map.items():
            if keyword in description:
                return action
        return self.default_action

    def run_action(self, action: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"action": action}
        if parameters:
            payload["parameters"] = parameters

        response = requests.post(
            f"{self.base_url.rstrip('/')}/executions",
            headers=self._headers(),
            json=payload,
            timeout=float(os.getenv("STACKSTORM_TIMEOUT", "15")),
            verify=self.verify_ssl,
        )
        response.raise_for_status()
        return response.json()

    def trigger_for_fault(self, device_id: int, fault: Dict[str, Any], extra_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """根据故障描述匹配 StackStorm 动作并执行"""
        if not self.is_enabled():
            raise RuntimeError("StackStorm 未启用")

        action = self.resolve_action(fault.get("description", ""))
        if not action:
            raise RuntimeError("未配置 StackStorm 动作映射")

        parameters = {
            "device_id": device_id,
            "fault_description": fault.get("description"),
            "fault_level": fault.get("level"),
        }
        if extra_context:
            parameters.update(extra_context)

        execution = self.run_action(action, parameters)
        return {
            "action": action,
            "execution_id": execution.get("id"),
            "status": execution.get("status"),
            "result": execution,
        }


stackstorm_client = StackStormClient()

