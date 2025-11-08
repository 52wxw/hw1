"""
多模型调度器：根据场景自动选择最优模型
支持 DeepSeek-R1-7B、Llama 3 8B、Qwen 7B
"""
from langchain.llms import Ollama
import os
import time
from typing import Dict, List, Tuple

class ModelScheduler:
    """场景化模型调度器"""
    
    def __init__(self, ollama_url: str):
        self.ollama_url = ollama_url
        self.models = {
            "deepseek-r1": {
                "model": "deepseek-r1-finetuned",
                "use_case": ["复杂故障分析", "路由环路", "配置错误", "P0/P1级故障"],
                "accuracy": 0.95,  # 微调后准确率
                "speed": "慢"
            },
            "llama3": {
                "model": "llama3:8b",
                "use_case": ["通用巡检", "中等复杂度分析"],
                "accuracy": 0.88,
                "speed": "中"
            },
            "qwen": {
                "model": "qwen:7b",
                "use_case": ["简单巡检", "快速分析", "P3级故障"],
                "accuracy": 0.85,
                "speed": "快"
            }
        }
        self.llm_instances = {}
        self._init_models()
    
    def _init_models(self):
        """初始化所有模型实例"""
        for key, config in self.models.items():
            try:
                self.llm_instances[key] = Ollama(
                    model=config["model"],
                    base_url=self.ollama_url
                )
            except Exception as e:
                print(f"警告：模型 {key} 初始化失败：{e}")
    
    def select_model(self, scenario: str, fault_level: str = None) -> str:
        """
        根据场景和故障等级选择最优模型
        :param scenario: 巡检场景（简单巡检/复杂故障/路由分析等）
        :param fault_level: 故障等级（P0/P1/P2/P3）
        :return: 模型key
        """
        # 高优先级故障使用DeepSeek
        if fault_level in ["P0", "P1"]:
            return "deepseek-r1"
        
        # 简单场景使用Qwen提速
        if scenario in ["简单巡检", "快速分析"] or fault_level == "P3":
            return "qwen"
        
        # 默认使用Llama3
        return "llama3"
    
    def predict(self, prompt: str, scenario: str = "通用巡检", fault_level: str = None) -> Dict:
        """
        使用最优模型进行预测
        :return: {"model": 模型名, "result": 结果, "time_cost": 耗时}
        """
        model_key = self.select_model(scenario, fault_level)
        model_config = self.models[model_key]
        llm = self.llm_instances.get(model_key)
        
        if not llm:
            raise Exception(f"模型 {model_key} 未初始化")
        
        start_time = time.time()
        try:
            result = llm(prompt)
            time_cost = time.time() - start_time
            return {
                "model": model_config["model"],
                "result": result,
                "time_cost": round(time_cost, 2),
                "accuracy": model_config["accuracy"]
            }
        except Exception as e:
            raise Exception(f"模型推理失败：{str(e)}")


