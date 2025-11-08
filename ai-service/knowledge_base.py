"""
运维知识库：存储故障解决方案，支持关键词搜索和自迭代
"""
import json
import os
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

class KnowledgeBase:
    """运维知识库管理器"""
    
    def __init__(self, db_path: str = "knowledge_base.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化知识库数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建知识库表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                title TEXT NOT NULL,
                solution TEXT NOT NULL,
                device_type TEXT,
                fault_level TEXT,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hit_count INTEGER DEFAULT 0
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_keyword ON knowledge(keyword)
        """)
        
        conn.commit()
        conn.close()
        
        # 初始化默认知识库
        self._init_default_knowledge()
    
    def _init_default_knowledge(self):
        """初始化默认知识库内容"""
        default_knowledge = [
            {
                "keyword": "接口down",
                "title": "接口状态为down的修复方法",
                "solution": "1. 检查物理链路是否正常\n2. 执行 undo shutdown 启用接口\n3. 检查接口配置是否正确\n4. 查看接口日志确认原因",
                "device_type": "华为",
                "fault_level": "P1"
            },
            {
                "keyword": "路由环路",
                "title": "路由环路故障处理",
                "solution": "1. 检查路由表是否有重复路由\n2. 检查OSPF/BGP配置\n3. 执行 reset ip routing-table statistics 重置路由统计\n4. 检查网络拓扑是否有环路",
                "device_type": "华为",
                "fault_level": "P1"
            },
            {
                "keyword": "CPU过载",
                "title": "CPU使用率过高处理",
                "solution": "1. 使用 display cpu-usage 查看进程占用\n2. 检查是否有异常进程\n3. 优化配置减少计算负载\n4. 考虑升级硬件",
                "device_type": "华为",
                "fault_level": "P2"
            }
        ]
        
        for item in default_knowledge:
            if not self.search(item["keyword"]):
                self.add(item["keyword"], item["title"], item["solution"], 
                        item.get("device_type"), item.get("fault_level"))
    
    def add(self, keyword: str, title: str, solution: str, 
            device_type: str = None, fault_level: str = None) -> int:
        """
        添加知识条目
        :return: 知识条目ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO knowledge (keyword, title, solution, device_type, fault_level)
            VALUES (?, ?, ?, ?, ?)
        """, (keyword, title, solution, device_type, fault_level))
        
        knowledge_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return knowledge_id
    
    def search(self, keyword: str, limit: int = 5) -> List[Dict]:
        """
        搜索知识库
        :param keyword: 搜索关键词
        :param limit: 返回结果数量
        :return: 知识条目列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 模糊搜索
        cursor.execute("""
            SELECT id, keyword, title, solution, device_type, fault_level, hit_count
            FROM knowledge
            WHERE keyword LIKE ? OR title LIKE ? OR solution LIKE ?
            ORDER BY hit_count DESC, update_time DESC
            LIMIT ?
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "keyword": row[1],
                "title": row[2],
                "solution": row[3],
                "device_type": row[4],
                "fault_level": row[5],
                "hit_count": row[6]
            })
            # 增加命中次数
            cursor.execute("""
                UPDATE knowledge SET hit_count = hit_count + 1, update_time = ?
                WHERE id = ?
            """, (datetime.now(), row[0]))
        
        conn.commit()
        conn.close()
        
        return results
    
    def get_by_id(self, knowledge_id: int) -> Optional[Dict]:
        """根据ID获取知识条目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, keyword, title, solution, device_type, fault_level, hit_count
            FROM knowledge
            WHERE id = ?
        """, (knowledge_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "keyword": row[1],
                "title": row[2],
                "solution": row[3],
                "device_type": row[4],
                "fault_level": row[5],
                "hit_count": row[6]
            }
        return None
    
    def update(self, knowledge_id: int, title: str = None, solution: str = None):
        """更新知识条目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title:
            updates.append("title = ?")
            params.append(title)
        if solution:
            updates.append("solution = ?")
            params.append(solution)
        
        if updates:
            updates.append("update_time = ?")
            params.append(datetime.now())
            params.append(knowledge_id)
            
            cursor.execute(f"""
                UPDATE knowledge SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            
            conn.commit()
        
        conn.close()


