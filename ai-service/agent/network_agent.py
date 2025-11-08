from langchain.agents import Tool, initialize_agent, AgentType
from langchain.llms import Ollama
import requests
import json

class NetworkAgent:
    def __init__(self, ollama_url, collect_service_url):
        self.llm = Ollama(model="deepseek-r1-finetuned", base_url=ollama_url)
        self.collect_service_url = collect_service_url
        self.tools = self._init_tools()
        self.agent = initialize_agent(
            self.tools, self.llm, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True  # 输出推理过程（可解释性）
        )

    def _init_tools(self):
        return [
            Tool(
                name="ExecuteCommand",
                func=self._execute_command,
                description="执行设备命令，参数：device_id（设备ID）、cmd（命令字符串）"
            ),
            Tool(
                name="VerifyStatus",
                func=self._verify_status,
                description="验证修复结果，参数：device_id、指标名称（如'interface_G0/0/1'）"
            )
        ]

    def _execute_command(self, device_id, cmd):
        # 调用采集服务执行命令
        resp = requests.post(
            f"{self.collect_service_url}/api/execute",
            json={"device_id": device_id, "cmd": cmd}
        )
        return resp.json().get("data", "执行失败")

    def _verify_status(self, device_id, metric):
        # 调用采集服务验证指标
        resp = requests.get(f"{self.collect_service_url}/api/metrics/{device_id}")
        metrics = resp.json().get("data", {})
        return f"{metric}状态：{metrics.get(metric, '未知')}"

    def auto_heal(self, device_id, fault_desc):
        """自主修复入口：输入设备ID和故障描述，返回修复结果"""
        prompt = f"设备{device_id}存在故障：{fault_desc}，请执行修复并验证结果，若失败则回滚"
        return self.agent.run(prompt)
