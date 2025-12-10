# smart_contract.py - 创建新文件
"""
智能合约系统
实现基础的智能合约功能
"""

from typing import Dict, List, Any
import json


class SmartContract:
    """智能合约基类"""

    def __init__(self, address: str, creator: str):
        self.address = address
        self.creator = creator
        self.balance = 0.0
        self.storage = {}
        self.code = ""
        self.timestamp = None

    def execute(self, function: str, args: List, caller: str, value: float = 0) -> Dict:
        """执行合约函数"""
        result = {
            "success": False,
            "data": None,
            "message": ""
        }

        self.balance += value

        if function == "transfer":
            if len(args) >= 2:
                to_address = args[0]
                amount = float(args[1])
                if self.balance >= amount:
                    self.balance -= amount
                    result["success"] = True
                    result["message"] = f"Transferred {amount} to {to_address}"
                    result["data"] = {
                        "from": self.address,
                        "to": to_address,
                        "amount": amount
                    }
                else:
                    result["message"] = "Insufficient contract balance"
        elif function == "getBalance":
            result["success"] = True
            result["data"] = self.balance
            result["message"] = f"Contract balance: {self.balance}"
        elif function == "mint":
            amount = float(args[0]) if args else 100.0
            self.balance += amount
            result["success"] = True
            result["message"] = f"Minted {amount} tokens"
            result["data"] = amount

        return result

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "address": self.address,
            "creator": self.creator,
            "balance": self.balance,
            "storage": self.storage,
            "timestamp": self.timestamp
        }


class ContractManager:
    """合约管理器"""

    def __init__(self):
        self.contracts: Dict[str, SmartContract] = {}

    def deploy_contract(self, creator: str, initial_balance: float = 0) -> SmartContract:
        """部署新合约"""
        import hashlib
        import time

        # 生成合约地址
        contract_data = f"{creator}{time.time()}"
        contract_address = f"contract_{hashlib.sha256(contract_data.encode()).hexdigest()[:20]}"

        contract = SmartContract(contract_address, creator)
        contract.balance = initial_balance
        contract.timestamp = int(time.time())

        self.contracts[contract_address] = contract
        return contract

    def get_contract(self, address: str) -> SmartContract:
        """获取合约"""
        return self.contracts.get(address)

    def execute_contract(self, contract_address: str, function: str, args: List, caller: str, value: float = 0) -> Dict:
        """执行合约"""
        contract = self.get_contract(contract_address)
        if not contract:
            return {"success": False, "message": f"Contract {contract_address} not found"}

        return contract.execute(function, args, caller, value)