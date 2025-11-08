"""解析设备 LLDP 输出，生成拓扑链路"""

from typing import Dict, List
import re


def parse_lldp_output(device_id: int, device_name: str, output: str) -> List[Dict[str, str]]:
    links = []
    if not output:
        return links

    pattern = re.compile(
        r"(?P<local>GigabitEthernet\S+)\s+"  # 本地端口
        r"(?P<status>Up|Down)\s+"             # 状态
        r"(?P<neighbor>\S+)\s+"              # 邻居设备
        r"(?P<neighbor_port>GigabitEthernet\S+)"  # 邻居端口
    )

    for line in output.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        links.append({
            "device_id": device_id,
            "device_name": device_name,
            "local_port": match.group("local"),
            "neighbor": match.group("neighbor"),
            "neighbor_port": match.group("neighbor_port"),
            "status": match.group("status")
        })

    return links


def merge_links(entries: List[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    link_map = {}

    def normalize_key(a: Dict[str, str], b: Dict[str, str]):
        key1 = (a["device_name"], a["local_port"], b["device_name"], b["local_port"])
        key2 = (b["device_name"], b["local_port"], a["device_name"], a["local_port"])
        return tuple(sorted([key1, key2]))

    for entry in entries:
        if len(entry) < 2:
            continue
        a, b = entry
        key = normalize_key(a, b)
        if key not in link_map:
            link_map[key] = {
                "source_device": a["device_name"],
                "source_port": a["local_port"],
                "target_device": b["device_name"],
                "target_port": b["local_port"],
                "status": "Up" if a.get("status") == "Up" and b.get("status") == "Up" else "Degraded"
            }

    return list(link_map.values())

