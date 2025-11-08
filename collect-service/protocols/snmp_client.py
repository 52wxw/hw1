from pysnmp.hlapi import *

class SNMPClient:
    def __init__(self, ip, community, port=161, version=2):
        self.ip = ip
        self.community = community
        self.port = port
        self.version = version  # 2 for v2c, 3 for v3

    def get_metrics(self, metric_types):
        """获取指定类型的SNMP指标（CPU/内存/接口）"""
        metrics = {}
        if "cpu" in metric_types:
            metrics["cpu_usage"] = self._get_cpu_usage()
        if "memory" in metric_types:
            metrics["memory_usage"] = self._get_memory_usage()
        if "interface" in metric_types:
            metrics["interface_status"] = self._get_interface_status()
        return metrics

    def get_lldp_neighbors(self):
        """采集 LLDP 邻居信息（基于 LLDP-MIB）"""
        # OID 常量
        lldp_rem_table_oids = {
            "neighbor": "1.0.8802.1.1.2.1.4.1.1.9",  # lldpRemSysName
            "neighbor_port": "1.0.8802.1.1.2.1.4.1.1.8",  # lldpRemPortDesc
            "neighbor_port_id": "1.0.8802.1.1.2.1.4.1.1.7",  # lldpRemPortId
            "local_port_num": "1.0.8802.1.1.2.1.4.1.1.2",  # lldpRemLocalPortNum
        }
        lldp_loc_port_desc_oid = "1.0.8802.1.1.2.1.3.7.1.4"  # lldpLocPortDesc

        local_port_desc = self._walk_oid_with_suffix(lldp_loc_port_desc_oid)

        neighbor_data = {}
        for key, oid in lldp_rem_table_oids.items():
            values = self._walk_oid_with_suffix(oid)
            for suffix, value in values.items():
                entry = neighbor_data.setdefault(suffix, {})
                entry[key] = value

        lldp_entries = []
        for suffix, data in neighbor_data.items():
            local_port_num = data.get("local_port_num")
            local_port = local_port_desc.get(str(local_port_num)) if local_port_num else None
            if not local_port and local_port_num:
                local_port = f"LocalPort-{local_port_num}"
            neighbor = data.get("neighbor") or data.get("neighbor_port_id")
            if not neighbor:
                continue
            lldp_entries.append({
                "local_port": local_port,
                "neighbor": neighbor,
                "neighbor_port": data.get("neighbor_port") or data.get("neighbor_port_id"),
                "status": "Up"
            })
        return lldp_entries

    def _get_cpu_usage(self):
        """获取CPU使用率（华为设备OID示例）"""
        oid = "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.6.1"  # 华为CPU使用率OID
        return self._get_oid_value(oid)

    def _get_memory_usage(self):
        """获取内存使用率（华为设备OID示例）"""
        oid = "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.8.1"  # 华为内存使用率OID
        return self._get_oid_value(oid)

    def _get_interface_status(self):
        """获取接口状态（通用OID）"""
        oid = "1.3.6.1.2.1.2.2.1.8"  # ifOperStatus
        results = self._walk_oid(oid)
        status_map = {1: "up", 2: "down"}
        return {f"if{idx}": status_map.get(int(val), "unknown") 
                for idx, val in results.items()}

    def _get_oid_value(self, oid):
        """获取单个OID的值"""
        error_indication, error_status, error_index, var_binds = next(
            getCmd(SnmpEngine(),
                   CommunityData(self.community, mpModel=self.version-1),
                   UdpTransportTarget((self.ip, self.port)),
                   ContextData(),
                   ObjectType(ObjectIdentity(oid)))
        )
        if error_indication:
            raise Exception(f"SNMP错误: {error_indication}")
        return var_binds[0][1].prettyPrint()

    def _walk_oid(self, oid):
        """遍历OID获取多个值"""
        results = {}
        for (error_indication, error_status, error_index, var_binds) in nextCmd(
            SnmpEngine(),
            CommunityData(self.community, mpModel=self.version-1),
            UdpTransportTarget((self.ip, self.port)),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False
        ):
            if error_indication:
                raise Exception(f"SNMP错误: {error_indication}")
            for var_bind in var_binds:
                oid_str = str(var_bind[0])
                idx = oid_str.split('.')[-1]  # 提取接口索引
                results[idx] = var_bind[1].prettyPrint()
        return results

    def _walk_oid_with_suffix(self, oid):
        """遍历OID并保留完整后缀索引"""
        results = {}
        for (error_indication, error_status, error_index, var_binds) in nextCmd(
            SnmpEngine(),
            CommunityData(self.community, mpModel=self.version-1),
            UdpTransportTarget((self.ip, self.port)),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False
        ):
            if error_indication:
                raise Exception(f"SNMP错误: {error_indication}")
            for var_bind in var_binds:
                oid_str = str(var_bind[0])
                base_len = len(oid.split('.'))
                suffix = '.'.join(oid_str.split('.')[base_len:])
                results[suffix] = var_bind[1].prettyPrint()
        return results
