import json
import time
from typing import List, Dict, Any, Optional
from merkle_tree import MerkleTree
from smart_contract import ContractManager
from utils import Utils

# 在顶部添加数据库导入
try:
    from database import db  # 使用全局数据库实例

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️  数据库模块不可用，将使用内存存储")


class Transaction:
    def __init__(self, sender: str, receiver: str, amount: float,
                 transaction_type: str = "transfer", data: str = "", signature: Optional[str] = None, timestamp: Optional[int] = None):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.transaction_type = transaction_type
        self.data = data
        # 🔥 关键修复：先设置时间戳，再计算哈希
        self.timestamp = timestamp if timestamp is not None else Utils.get_current_timestamp()
        self.signature = signature
        self.block_number = None
        self.status = "pending"
        # 🔥 在所有属性设置完成后才计算哈希
        self.transaction_id = self.calculate_hash()

    def calculate_hash(self) -> str:
        transaction_data = {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'type': self.transaction_type,
            'data': self.data,
            'timestamp': self.timestamp
        }
        return Utils.calculate_hash(transaction_data)

    def to_dict(self) -> Dict:
        """转换为字典（包含数据库需要的字段）"""
        transaction_data = {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'type': self.transaction_type,
            'data': self.data,
            'timestamp': self.timestamp,
            'transaction_id': self.transaction_id,
            'block_number': self.block_number,
            'status': self.status,
            'signature': self.signature,
        }
        return transaction_data

    def __str__(self) -> str:
        if self.transaction_type == "transfer":
            return f"Transfer({self.sender} -> {self.receiver}: {self.amount})"
        elif self.transaction_type == "stake":
            return f"Stake({self.sender} 质押 {self.amount})"
        else:
            return f"Transaction[{self.transaction_type}]({self.sender} -> {self.receiver}: {self.amount})"


class Block:
    def __init__(self, index: int, transactions: List[Transaction], previous_hash: str,
                 timestamp: Optional[int] = None, nonce: int = 0):
        self.index = index
        self.timestamp = timestamp or Utils.get_current_timestamp()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.merkle_tree = MerkleTree(transactions)
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """计算区块的哈希值（包含默克尔根和nonce）"""
        block_data = {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'merkle_root': self.merkle_tree.get_root()
        }
        return Utils.calculate_hash(block_data)

    def mine_block(self, difficulty: int) -> None:
        target = '0' * difficulty
        print(f"开始挖矿，难度: {difficulty}, 目标前缀: {target}")
        
        start_time = time.time()
        attempts = 0
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            attempts += 1
            
            if attempts % 1000 == 0:
                elapsed = time.time() - start_time
                rate = attempts / elapsed if elapsed > 0 else 0
                print(f"尝试次数: {attempts}, 速度: {rate:.0f} H/s")
        
        elapsed = time.time() - start_time
        rate = attempts / elapsed if elapsed > 0 else 0
        print(f"✅ 挖矿成功！")
        print(f"  Nonce: {self.nonce}")
        print(f"  哈希: {self.hash}")
        print(f"  尝试次数: {attempts}")
        print(f"  耗时: {elapsed:.2f}秒")
        print(f"  平均算力: {rate:.0f} H/s")

    def to_dict(self) -> Dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'hash': self.hash,
            'nonce': self.nonce,
            'merkle_root': self.merkle_tree.get_root(),
            'transaction_count': len(self.transactions),
            'difficulty': 2,
            'size': len(json.dumps([tx.to_dict() for tx in self.transactions]))
        }

    def __str__(self) -> str:
        return f"Block #{self.index} [Hash: {self.hash[:10]}...]"


class Blockchain:
    def __init__(self, difficulty: int = 2):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.difficulty = difficulty
        self.transaction_fee = 0.1
        self.mining_reward = 10.0
        self.contract_manager = ContractManager()
        self.forks = []

        self.db = None
        if DATABASE_AVAILABLE:
            self.db = db
            print("✅ 数据库连接可用")
        else:
            print("⚠️  使用内存存储，数据不会持久化")

        loaded = self.load_from_database()
        
        if loaded and self.chain:
            if self.chain[0].index != 0:
                print(f"\n🚨 致命错误：数据库已损坏！")
                print(f"   第一个区块的索引是 {self.chain[0].index}，应该是 0！")
                print(f"   正在清空并重新创建区块链...\n")
                self.chain = []
                self.pending_transactions = []
                loaded = False
        
        if not loaded:
            print("数据库中没有有效区块，创建创世区块")
            self.create_genesis_block()
        else:
            print(f"✅ 从数据库成功加载区块链，跳过创世区块创建")

    def load_from_database(self) -> bool:
        if not self.db or not self.db.is_connected:
            print("数据库未连接，跳过数据加载")
            return False

        try:
            print("正在从数据库加载数据...")

            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute('''
            SELECT DISTINCT block_number FROM transactions 
            WHERE block_number IS NOT NULL AND status = 'confirmed'
            ORDER BY block_number ASC
            ''')
            block_numbers = [row['block_number'] for row in cursor.fetchall()]
            cursor.close()

            if not block_numbers:
                print("数据库中没有任何区块")
                return False

            print(f"数据库中找到区块: {block_numbers}")

            if block_numbers[0] != 0:
                print(f"⚠️ 警告：数据库中第一个区块不是0，而是 {block_numbers[0]}！数据库可能损坏！")
                return False

            blocks_dict = {}
            for block_num in block_numbers:
                cursor = self.db.connection.cursor(dictionary=True)
                cursor.execute('''
                SELECT * FROM transactions 
                WHERE block_number = %s AND status = 'confirmed'
                ORDER BY timestamp ASC
                ''', (block_num,))
                transactions_data = cursor.fetchall()
                cursor.close()

                if transactions_data:
                    transactions = []
                    for tx_data in transactions_data:
                        tx = Transaction(
                            sender=tx_data['from_address'],
                            receiver=tx_data['to_address'],
                            amount=float(tx_data['amount']),
                            transaction_type=tx_data['transaction_type'],
                            data=tx_data.get('data', ''),
                            timestamp=tx_data['timestamp']
                        )
                        # 🔥 用数据库中的transaction_hash覆盖
                        tx.transaction_id = tx_data['transaction_hash']
                        tx.block_number = tx_data['block_number']
                        tx.status = tx_data['status']
                        transactions.append(tx)

                    cursor = self.db.connection.cursor(dictionary=True)
                    cursor.execute('SELECT * FROM blocks WHERE block_number = %s', (block_num,))
                    block_data = cursor.fetchone()
                    cursor.close()

                    if block_data:
                        block = Block(
                            index=block_data['block_number'],
                            transactions=transactions,
                            previous_hash=block_data['previous_hash'],
                            timestamp=block_data['timestamp'],
                            nonce=block_data['nonce']
                        )
                        # 🔥 用数据库中的block_hash覆盖
                        block.hash = block_data['block_hash']
                        blocks_dict[block_num] = block
                        print(f"  加载区块 #{block_num}: {block.hash[:20]}...")

            sorted_blocks = sorted(blocks_dict.items(), key=lambda x: x[0])
            for _, block in sorted_blocks:
                self.chain.append(block)

            print(f"✅ 从数据库加载了 {len(self.chain)} 个区块")

            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute('''
            SELECT * FROM transactions 
            WHERE status = 'pending' 
            ORDER BY timestamp ASC
            ''')
            pending_txs = cursor.fetchall()
            cursor.close()

            for tx_data in pending_txs:
                tx = Transaction(
                    sender=tx_data['from_address'],
                    receiver=tx_data['to_address'],
                    amount=float(tx_data['amount']),
                    transaction_type=tx_data['transaction_type'],
                    data=tx_data.get('data', ''),
                    timestamp=tx_data['timestamp']
                )
                tx.transaction_id = tx_data['transaction_hash']
                tx.status = tx_data['status']
                self.pending_transactions.append(tx)

            if self.pending_transactions:
                print(f"✅ 从数据库加载了 {len(self.pending_transactions)} 笔待处理交易")

            return True

        except Exception as e:
            print(f"❌ 从数据库加载数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_genesis_block(self) -> None:
        print("正在创建创世区块...")

        GENESIS_TIMESTAMP = 1633046400
        
        genesis_transaction = Transaction(
            sender="0",
            receiver="genesis",
            amount=1000.0,
            transaction_type="genesis",
            timestamp=GENESIS_TIMESTAMP
        )

        genesis_block = Block(
            index=0,
            transactions=[genesis_transaction],
            previous_hash="0" * 64,
            timestamp=GENESIS_TIMESTAMP,
            nonce=0
        )

        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)

        print(f"✅ 创世区块创建完成！")
        print(f"   索引: {genesis_block.index}")
        print(f"   哈希: {genesis_block.hash}")
        print(f"   时间戳: {GENESIS_TIMESTAMP}")

        if self.db and self.db.is_connected:
            try:
                block_data = {
                    'number': genesis_block.index,
                    'hash': genesis_block.hash,
                    'previous_hash': genesis_block.previous_hash,
                    'timestamp': genesis_block.timestamp,
                    'difficulty': self.difficulty,
                    'nonce': genesis_block.nonce,
                    'merkle_root': genesis_block.merkle_tree.get_root(),
                    'transaction_count': 1,
                    'miner_address': 'system',
                    'block_size': 0
                }
                self.db.record_block(block_data)

                tx_data = {
                    'hash': genesis_transaction.transaction_id,
                    'from': genesis_transaction.sender,
                    'to': genesis_transaction.receiver,
                    'amount': genesis_transaction.amount,
                    'fee': 0,
                    'transaction_type': genesis_transaction.transaction_type,
                    'data': genesis_transaction.data,
                    'timestamp': genesis_transaction.timestamp,
                    'status': 'confirmed',
                    'confirmations': 1,
                    'block_number': 0,
                    'memo': 'Genesis Transaction'
                }
                self.db.record_transaction(tx_data)

                print("✅ 创世区块已保存到数据库")
            except Exception as e:
                print(f"⚠️ 保存创世区块到数据库失败 (可能已存在): {e}")

    def add_transaction(self, transaction: Transaction, signature: str = None) -> bool:
        if signature and transaction.sender != "0":
            if not self.verify_transaction_signature(transaction, signature):
                print(f"❌ 交易签名验证失败！交易ID: {transaction.transaction_id}")
                return False

        if transaction.sender != "0":
            sender_balance = self.get_balance(transaction.sender)
            total_cost = transaction.amount + self.transaction_fee

            if sender_balance < total_cost:
                print(f"❌ 交易失败：余额不足！")
                print(f"   需要: {total_cost:.8f}, 余额: {sender_balance:.8f}")
                return False

        self.pending_transactions.append(transaction)

        if self.db and self.db.is_connected:
            try:
                tx_data = {
                    'hash': transaction.transaction_id,
                    'from': transaction.sender,
                    'to': transaction.receiver,
                    'amount': float(transaction.amount),
                    'fee': float(self.transaction_fee),
                    'transaction_type': transaction.transaction_type,
                    'data': transaction.data,
                    'timestamp': transaction.timestamp,
                    'status': 'pending',
                    'confirmations': 0,
                    'block_number': None,
                    'memo': f'{transaction.transaction_type} transaction'
                }

                success = self.db.record_transaction(tx_data)
                if not success:
                    print("❌ 保存交易到数据库失败")
            except Exception as e:
                print(f"❌ 数据库操作异常: {e}")
                import traceback
                traceback.print_exc()

        print(f"✅ 交易已添加到待处理池: {transaction}")
        print(f"   交易ID: {transaction.transaction_id}")
        print(f"   手续费: {self.transaction_fee}")

        return True

    def mine_pending_transactions(self, miner_address: str) -> bool:
        if not self.pending_transactions:
            print("没有待处理的交易，无需挖矿")
            return False

        print(f"\n{'=' * 60}")
        print("开始挖矿")
        print(f"{'=' * 60}")
        print(f"矿工地址: {miner_address}")
        print(f"挖矿奖励: {self.mining_reward}")
        print(f"待处理交易数: {len(self.pending_transactions)}")
        print(f"挖矿难度: {self.difficulty}")

        total_fees = len(self.pending_transactions) * self.transaction_fee
        print(f"总手续费: {total_fees}")

        reward_transaction = Transaction(
            sender="0",
            receiver=miner_address,
            amount=self.mining_reward + total_fees,
            transaction_type="mining_reward",
            data=f"Block reward and fees for mining block #{len(self.chain)}"
        )

        all_transactions = self.pending_transactions.copy()
        all_transactions.append(reward_transaction)

        print(f"打包交易总数: {len(all_transactions)}")
        
        # 🔥 关键修复：打印所有交易的transaction_id，用于调试
        print("\n交易列表：")
        for i, tx in enumerate(all_transactions):
            print(f"  [{i}] {tx.sender} -> {tx.receiver}: {tx.amount}, TxID: {tx.transaction_id[:20]}...")

        new_block = Block(
            index=len(self.chain),
            transactions=all_transactions,
            previous_hash=self.get_latest_block().hash
        )

        print(f"\n开始计算工作量证明...")
        start_time = time.time()
        new_block.mine_block(self.difficulty)
        mining_time = time.time() - start_time
        print(f"挖矿耗时: {mining_time:.2f}秒")
        
        # 🔥 关键修复：挖矿后再次打印哈希，确认没有变化
        print(f"挖矿后区块哈希: {new_block.hash}")

        self.chain.append(new_block)

        if self.db and self.db.is_connected:
            try:
                # 🔥 关键：保存区块时使用new_block.hash（已挖矿的哈希）
                block_data = {
                    'number': new_block.index,
                    'hash': new_block.hash,  # 🔥 这个哈希是挖矿后的
                    'previous_hash': new_block.previous_hash,
                    'timestamp': new_block.timestamp,
                    'difficulty': self.difficulty,
                    'nonce': new_block.nonce,
                    'merkle_root': new_block.merkle_tree.get_root(),
                    'transaction_count': len(all_transactions),
                    'miner_address': miner_address,
                    'block_size': len(json.dumps([tx.to_dict() for tx in all_transactions]))
                }

                print(f"\n保存区块到数据库...")
                print(f"  区块哈希: {block_data['hash']}")
                
                block_success = self.db.record_block(block_data)

                if block_success:
                    print(f"✅ 区块 #{new_block.index} 已保存到数据库")

                    for tx in all_transactions:
                        tx.block_number = new_block.index
                        tx.status = 'confirmed'

                        cursor = self.db.connection.cursor()
                        if tx.sender == "0":
                            # 🔥 关键修复：保存系统奖励交易时，使用tx.transaction_id
                            tx_data = {
                                'hash': tx.transaction_id,  # 🔥 使用已计算的transaction_id
                                'from': tx.sender,
                                'to': tx.receiver,
                                'amount': float(tx.amount),
                                'fee': 0,
                                'transaction_type': tx.transaction_type,
                                'data': tx.data,
                                'timestamp': tx.timestamp,
                                'status': 'confirmed',
                                'confirmations': 1,
                                'block_number': new_block.index,
                                'memo': 'Mining reward'
                            }
                            print(f"  保存奖励交易: {tx.transaction_id[:20]}...")
                            self.db.record_transaction(tx_data)
                        else:
                            cursor.execute('''
                            UPDATE transactions 
                            SET status = 'confirmed', 
                                block_number = %s, 
                                confirmations = 1,
                                fee = %s
                            WHERE transaction_hash = %s
                            ''', (new_block.index, self.transaction_fee, tx.transaction_id))

                        if tx.sender != "0":
                            self.db.update_address_balance(tx.sender, tx.amount, 'subtract')
                            self.db.update_address_balance(tx.sender, self.transaction_fee, 'subtract')

                        self.db.update_address_balance(tx.receiver, tx.amount, 'add')

                    self.db.connection.commit()
                    cursor.close()

                    self.db.update_address_balance(miner_address, self.mining_reward + total_fees, 'add')
                    print(f"✅ 矿工 {miner_address} 获得奖励: {self.mining_reward + total_fees}")

                else:
                    print("❌ 保存区块到数据库失败")

            except Exception as e:
                print(f"❌ 数据库保存过程中出错: {e}")
                import traceback
                traceback.print_exc()
                self.chain.pop()
                return False

        self.pending_transactions = []

        print(f"\n{'=' * 60}")
        print("挖矿完成！")
        print(f"{'=' * 60}")
        print(f"新区块 #{new_block.index} 已添加到区块链")
        print(f"区块哈希: {new_block.hash}")
        print(f"区块包含 {len(all_transactions)} 笔交易:")

        for i, tx in enumerate(all_transactions):
            if tx.sender == "0":
                print(f"  [{i}] 🎯 [系统奖励] -> {tx.receiver}: {tx.amount:.8f}")
            else:
                print(f"  [{i}] 📨 {tx.sender} -> {tx.receiver}: {tx.amount:.8f} (手续费: {self.transaction_fee})")

        print(f"{'=' * 60}")

        return True

    def get_balance(self, address: str) -> float:
        balance = 0.0

        if self.db and self.db.is_connected:
            try:
                db_balance = self.db.get_address_balance(address)
                if db_balance is not None:
                    pending_sent = 0.0
                    for tx in self.pending_transactions:
                        if tx.sender == address:
                            pending_sent += tx.amount + self.transaction_fee

                    return max(0, db_balance - pending_sent)
            except Exception as e:
                print(f"从数据库查询余额失败，使用本地计算: {e}")

        for block in self.chain:
            for transaction in block.transactions:
                if transaction.receiver == address:
                    balance += transaction.amount
                if transaction.sender == address and transaction.sender != "0":
                    balance -= transaction.amount

        for transaction in self.pending_transactions:
            if transaction.sender == address:
                balance -= transaction.amount + self.transaction_fee

        return round(balance, 8)

    def verify_transaction_signature(self, transaction: Transaction, signature: str) -> bool:
        try:
            return True
        except Exception as e:
            print(f"验证签名时出错: {e}")
            return False

    def get_latest_block(self) -> Block:
        return self.chain[-1] if self.chain else None

    def is_chain_valid(self) -> bool:
        print("\n" + "="*60)
        print("正在验证区块链...")
        print("="*60)

        if len(self.chain) == 0:
            print("区块链为空")
            return True

        genesis_block = self.chain[0]
        if genesis_block.index != 0:
            print(f"❌ 错误：创世区块索引应为0，实际为{genesis_block.index}")
            print(f"\n🔍 诊断信息：")
            print(f"   区块链总数: {len(self.chain)}")
            print(f"   第一个区块索引: {genesis_block.index}")
            print(f"   第一个区块哈希: {genesis_block.hash[:20]}...")
            print(f"\n💡 解决方案：删除数据库重新开始！")
            print(f"   cd D:\\pyqt5\\BuptCoin")
            print(f"   del buptcoin.db")
            print(f"   python BuptCoin/main.py\n")
            return False
        
        if genesis_block.previous_hash != "0" * 64:
            print(f"❌ 错误：创世区块的前驱哈希格式错误")
            return False

        print(f"✅ 创世区块验证通过 (索引: {genesis_block.index})")

        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            print(f"\n检查区块 #{current_block.index}...")
            
            # 🔥 调试信息：打印区块的交易transaction_id
            print(f"  区块 #{current_block.index} 包含 {len(current_block.transactions)} 笔交易：")
            for j, tx in enumerate(current_block.transactions):
                print(f"    [{j}] TxID: {tx.transaction_id[:20]}...")

            if current_block.index != previous_block.index + 1:
                print(f"❌ 错误：区块索引不连续")
                print(f"   前一个区块: #{previous_block.index}")
                print(f"   当前区块: #{current_block.index}")
                return False

            if current_block.previous_hash != previous_block.hash:
                print(f"❌ 错误：区块 #{current_block.index} 的前驱哈希不匹配")
                print(f"   期望: {previous_block.hash[:20]}...")
                print(f"   实际: {current_block.previous_hash[:20]}...")
                return False

            original_hash = current_block.hash
            calculated_hash = current_block.calculate_hash()
            
            if original_hash != calculated_hash:
                print(f"❌ 错误：区块 #{current_block.index} 的哈希值不匹配（可能被篡改）")
                print(f"   存储的哈希: {original_hash[:20]}...")
                print(f"   计算的哈希: {calculated_hash[:20]}...")
                print(f"   Nonce: {current_block.nonce}")
                print(f"\n💡 解决方案：删除数据库重新开始！")
                print(f"   cd D:\\pyqt5\\BuptCoin")
                print(f"   del buptcoin.db")
                return False

            if current_block.hash[:self.difficulty] != '0' * self.difficulty:
                print(f"❌ 错误：区块 #{current_block.index} 的工作量证明无效")
                print(f"   要求难度: {self.difficulty}")
                print(f"   哈希前缀: {current_block.hash[:self.difficulty]}")
                return False

            print(f"✅ 区块 #{current_block.index} 验证通过")
            print(f"   哈希: {current_block.hash[:20]}...")
            print(f"   Nonce: {current_block.nonce}")
            print(f"   交易数: {len(current_block.transactions)}")

        print("\n" + "="*60)
        print("✅ 区块链验证完全通过！所有区块都是有效的！")
        print(f"   总区块数: {len(self.chain)}")
        print(f"   难度: {self.difficulty}")
        print("="*60 + "\n")
        return True

    def to_dict(self) -> Dict:
        return {
            'chain': [block.to_dict() for block in self.chain],
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions],
            'difficulty': self.difficulty,
            'mining_reward': self.mining_reward,
            'transaction_fee': self.transaction_fee
        }

    def print_chain(self) -> None:
        print("\n" + "=" * 60)
        print("区块链状态")
        print("=" * 60)

        print(f"区块总数: {len(self.chain)}")
        print(f"待处理交易数: {len(self.pending_transactions)}")
        print(f"挖矿难度: {self.difficulty}")
        print(f"挖矿奖励: {self.mining_reward}")
        print(f"交易手续费: {self.transaction_fee}")

        if self.db and self.db.is_connected:
            stats = self.db.get_system_stats()
            print(f"数据库总交易数: {stats.get('total_transactions', 0)}")
            print(f"数据库总余额: {stats.get('total_balance', 0):.2f} BPC")

        print("\n最近5个区块:")
        recent_blocks = self.chain[-5:] if len(self.chain) > 5 else self.chain

        for block in recent_blocks:
            print(f"\n🔷 区块 #{block.index}")
            print(f"   哈希: {block.hash[:20]}...")
            print(f"   时间: {block.timestamp}")
            print(f"   交易数: {len(block.transactions)}")
            print(f"   前驱哈希: {block.previous_hash[:20]}...")

        print("=" * 60)
