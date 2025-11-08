import requests
import json
import hashlib
from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

class BlockchainClient:
    def __init__(self, chain_url):
        # 修复：如果 chain_url 为空或 None，则禁用区块链功能
        if not chain_url:
            self.web3 = None
            self.account = None
            self.contract = None
            self.contract_address = None
            self.contract_abi = []
            self.enabled = False
            return
        
        try:
            self.web3 = Web3(Web3.HTTPProvider(chain_url))
            # 修复：从环境变量读取合约地址
            self.contract_address = os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS")
            # 修复：从环境变量读取私钥，如果不存在则禁用区块链功能
            private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")
            if private_key:
                self.account = self.web3.eth.account.from_key(private_key)
            else:
                self.account = None
                self.contract = None
                self.contract_abi = []
                self.enabled = False
                print("警告：BLOCKCHAIN_PRIVATE_KEY 未设置，区块链功能已禁用")
                return
            
            # 修复：使用相对于模块位置的路径
            contract_abi_path = os.path.join(os.path.dirname(__file__), "contract", "LogStore.abi")
            if os.path.exists(contract_abi_path):
                self.contract_abi = json.load(open(contract_abi_path))
            else:
                # 如果ABI文件不存在，使用空列表（需要编译合约生成ABI）
                self.contract_abi = []
                print("警告：合约ABI文件不存在，区块链功能已禁用")
            
            if self.contract_address and self.contract_abi:
                self.contract = self.web3.eth.contract(address=self.contract_address, abi=self.contract_abi)
                self.enabled = True
            else:
                self.contract = None
                self.enabled = False
        except Exception as e:
            # 如果初始化失败，禁用区块链功能但允许服务继续运行
            print(f"警告：区块链客户端初始化失败：{str(e)}，区块链功能已禁用")
            self.web3 = None
            self.account = None
            self.contract = None
            self.contract_address = None
            self.contract_abi = []
            self.enabled = False

    def _calc_hash(self, content):
        """计算内容哈希"""
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()

    def upload_log(self, log_data, operator="system"):
        """上传日志哈希到区块链"""
        # 如果区块链功能未启用，只返回哈希值
        if not self.enabled or not self.web3 or not self.contract:
            return self._calc_hash(log_data)
        
        try:
            if not self.web3.is_connected():
                print("警告：区块链节点连接失败，仅返回哈希值")
                return self._calc_hash(log_data)
            
            log_hash = self._calc_hash(log_data)
            # 构建交易
            tx = self.contract.functions.uploadLog(
                deviceId=str(log_data["device_id"]),
                opType=log_data["type"],
                logHash=log_hash,
                operator=operator
            ).build_transaction({
                "from": self.account.address,
                "nonce": self.web3.eth.get_transaction_count(self.account.address)
            })
            # 签名并发送交易
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            # 等待确认
            self.web3.eth.wait_for_transaction_receipt(tx_hash)
            return log_hash
        except Exception as e:
            # 如果上链失败，只返回哈希值，不中断服务
            print(f"警告：日志上链失败：{str(e)}，仅返回哈希值")
            return self._calc_hash(log_data)
