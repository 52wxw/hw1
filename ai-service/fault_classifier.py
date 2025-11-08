"""
故障分级器：自动识别故障等级（P0-P3）
P0: 紧急（系统宕机、核心路由中断）
P1: 严重（接口down、路由环路）
P2: 重要（CPU过载、内存告警）
P3: 一般（接口未启用、配置建议）
"""
import re
from typing import Dict, List, Tuple

class FaultClassifier:
    """故障分级与自动修复建议生成器"""
    
    # 故障关键词与等级映射
    FAULT_PATTERNS = {
        "P0": [
            r"系统.*宕机", r"核心.*中断", r"设备.*离线", r"无法.*连接",
            r"路由.*完全.*中断", r"网络.*瘫痪"
        ],
        "P1": [
            r"接口.*down", r"接口.*关闭", r"路由.*环路", r"路由.*异常",
            r"BGP.*断开", r"OSPF.*故障", r"链路.*中断"
        ],
        "P2": [
            r"CPU.*过载", r"CPU.*超过.*80", r"内存.*告警", r"内存.*超过.*90",
            r"流量.*异常", r"丢包.*率.*高", r"延迟.*高"
        ],
        "P3": [
            r"接口.*未启用", r"配置.*建议", r"版本.*升级", r"日志.*清理",
            r"性能.*优化", r"冗余.*配置"
        ]
    }
    
    # 自动修复命令映射（华为设备）
    AUTO_REPAIR_COMMANDS = {
        "接口down": {
            "huawei": "undo shutdown",
            "cisco": "no shutdown"
        },
        "接口未启用": {
            "huawei": "undo shutdown",
            "cisco": "no shutdown"
        },
        "路由异常": {
            "huawei": "reset ip routing-table statistics",
            "cisco": "clear ip route *"
        }
    }
    
    def classify(self, report_text: str, metrics: Dict = None) -> List[Dict]:
        """
        对故障报告进行分级
        :param report_text: AI生成的报告文本
        :param metrics: 设备指标数据
        :return: 故障列表，每个故障包含 {level, description, evidence, repair_suggestion}
        """
        faults = []
        
        # 基于关键词匹配
        for level, patterns in self.FAULT_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, report_text, re.IGNORECASE)
                for match in matches:
                    # 提取上下文作为证据
                    start = max(0, match.start() - 50)
                    end = min(len(report_text), match.end() + 50)
                    evidence = report_text[start:end].strip()
                    
                    fault_desc = match.group(0)
                    repair_suggestion = self._generate_repair_suggestion(fault_desc, level)
                    
                    faults.append({
                        "level": level,
                        "description": fault_desc,
                        "evidence": evidence,
                        "repair_suggestion": repair_suggestion,
                        "auto_repairable": level in ["P3", "P2"]  # P3和部分P2可自动修复
                    })
        
        # 基于指标数据补充判断
        if metrics:
            faults.extend(self._classify_by_metrics(metrics))
        
        # 去重（相同描述只保留一次）
        unique_faults = []
        seen = set()
        for fault in faults:
            key = fault["level"] + ":" + fault["description"]
            if key not in seen:
                seen.add(key)
                unique_faults.append(fault)
        
        # 按优先级排序（P0 > P1 > P2 > P3）
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        unique_faults.sort(key=lambda x: priority_order.get(x["level"], 99))
        
        return unique_faults
    
    def _classify_by_metrics(self, metrics: Dict) -> List[Dict]:
        """基于指标数据判断故障"""
        faults = []
        
        # CPU过载判断
        if metrics.get("cpu_usage", 0) > 80:
            faults.append({
                "level": "P2",
                "description": f"CPU使用率过高：{metrics.get('cpu_usage')}%",
                "evidence": f"CPU使用率：{metrics.get('cpu_usage')}%",
                "repair_suggestion": "检查进程占用，优化配置或升级硬件",
                "auto_repairable": False
            })
        
        # 内存告警判断
        if metrics.get("memory_usage", 0) > 90:
            faults.append({
                "level": "P2",
                "description": f"内存使用率过高：{metrics.get('memory_usage')}%",
                "evidence": f"内存使用率：{metrics.get('memory_usage')}%",
                "repair_suggestion": "清理缓存或重启设备",
                "auto_repairable": False
            })
        
        # 接口down判断
        for interface, status in metrics.get("interfaces", {}).items():
            if status.get("status") == "down":
                faults.append({
                    "level": "P1",
                    "description": f"接口 {interface} 状态为down",
                    "evidence": f"接口 {interface}：{status}",
                    "repair_suggestion": "执行 undo shutdown 命令启用接口",
                    "auto_repairable": True
                })
        
        return faults
    
    def _generate_repair_suggestion(self, fault_desc: str, level: str) -> str:
        """生成修复建议"""
        fault_lower = fault_desc.lower()
        
        # 检查是否有自动修复命令
        for key, commands in self.AUTO_REPAIR_COMMANDS.items():
            if key.lower() in fault_lower:
                return f"建议执行：{commands.get('huawei', commands.get('cisco', '未知'))}"
        
        # 默认建议
        if level == "P0":
            return "紧急故障，建议立即人工介入处理"
        elif level == "P1":
            return "严重故障，建议检查配置和链路状态"
        elif level == "P2":
            return "重要告警，建议监控并优化性能"
        else:
            return "一般问题，建议按计划优化"


