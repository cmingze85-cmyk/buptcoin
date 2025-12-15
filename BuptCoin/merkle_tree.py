# merkle_tree.py - 新增文件
import hashlib
from typing import List


class MerkleTree:
    """默克尔树，用于验证交易完整性"""

    def __init__(self, transactions: List['Transaction']):
        self.transactions = transactions
        self.leaves = []
        self.root = None
        self.build_tree()

    def hash_data(self, data: str) -> str:
        """计算数据的SHA256哈希"""
        return hashlib.sha256(data.encode()).hexdigest()

    def build_tree(self):
        """构建默克尔树"""
        if not self.transactions:
            self.root = ""
            return

        # 🔥 关键修复：使用transaction_id而不是str(tx)
        # str(tx)会返回 "Transfer(A -> B: 10.0)"，不包含时间戳等关键信息
        # transaction_id 是交易的完整哈希，包含所有信息
        self.leaves = [tx.transaction_id for tx in self.transactions]

        # 2. 逐层计算父节点哈希
        current_level = self.leaves

        while len(current_level) > 1:
            next_level = []

            # 每两个节点组合计算父节点哈希
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                else:
                    combined = current_level[i] + current_level[i]  # 奇数时复制最后一个

                parent_hash = self.hash_data(combined)
                next_level.append(parent_hash)

            current_level = next_level

        self.root = current_level[0] if current_level else ""

    def get_root(self) -> str:
        """返回默克尔根"""
        return self.root

    def verify_transaction(self, transaction: 'Transaction', merkle_proof: List[str]) -> bool:
        """验证交易是否在默克尔树中"""
        if not self.root:
            return False

        # 🔥 使用transaction_id而不是str(transaction)
        tx_hash = transaction.transaction_id
        current_hash = tx_hash

        # 使用证明路径重新计算根哈希
        for proof_hash in merkle_proof:
            # 根据位置决定组合顺序
            if current_hash < proof_hash:
                combined = current_hash + proof_hash
            else:
                combined = proof_hash + current_hash

            current_hash = self.hash_data(combined)

        return current_hash == self.root

    def __str__(self):
        return f"MerkleTree(Root: {self.root[:10] if self.root else 'empty'}...)"
