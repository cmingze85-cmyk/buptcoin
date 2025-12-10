from blockchain import Transaction, Blockchain
# 在现有导入后添加
import hashlib
import json
import time  # 新增
import base64  # 新增
import rsa  # 需要安装：pip install rsa
from typing import List, Dict, Optional


# 在 Wallet 类中添加数据库相关方法
class Wallet:
    """钱包类，管理用户地址和交易"""

    def __init__(self, name: str, password: str = None, user_id: int = None):
        """
        初始化钱包

        Args:
            name: 钱包名称
            password: 密码（可选）
            user_id: 用户ID（如果从数据库加载）
        """
        self.name = name
        self.password = password
        self.user_id = user_id
        self.addresses = []
        self.private_keys = {}
        self.public_keys = {}

        # 检查是否从数据库加载
        if user_id:
            self.load_from_database()
        else:
            # 生成默认地址
            self.generate_default_addresses()

        print(f"钱包 '{self.name}' 初始化完成")
        if self.addresses:
            print(f"可用地址: {', '.join(self.addresses[:3])}...")

    def load_from_database(self):
        """从数据库加载钱包地址"""
        try:
            from database import db

            if not db or not db.is_connected:
                print("数据库未连接，使用默认地址")
                self.generate_default_addresses()
                return

            # 获取用户的地址
            addresses_info = db.get_user_addresses(self.user_id)
            if addresses_info:
                print(f"从数据库加载用户 {self.user_id} 的钱包地址...")
                for addr_info in addresses_info:
                    address = addr_info['address']
                    self.addresses.append(address)

                    # 注意：真实应用中应该从数据库加载密钥
                    # 这里简化处理，生成新的密钥对
                    key_pair = self.generate_key_pair()
                    self.public_keys[address] = key_pair["public_key"]
                    self.private_keys[address] = key_pair["private_key"]

                print(f"✅ 从数据库加载了 {len(self.addresses)} 个地址")
            else:
                print("用户没有钱包地址，生成默认地址")
                self.generate_default_addresses()

        except ImportError:
            print("数据库模块不可用，使用默认地址")
            self.generate_default_addresses()
        except Exception as e:
            print(f"从数据库加载钱包失败: {e}")
            self.generate_default_addresses()

    def load_from_database(self):
        """从数据库加载钱包地址"""
        try:
            from database import db

            if not db or not db.is_connected:
                print("数据库未连接，使用默认地址")
                self.generate_default_addresses()
                return

            # 获取用户的地址
            addresses_info = db.get_user_addresses(self.user_id)
            if addresses_info:
                print(f"从数据库加载用户 {self.user_id} 的钱包地址...")
                for addr_info in addresses_info:
                    address = addr_info['address']
                    self.addresses.append(address)

                    # 注意：真实应用中应该从数据库加载密钥
                    # 这里简化处理，生成新的密钥对
                    key_pair = self.generate_key_pair()
                    self.public_keys[address] = key_pair["public_key"]
                    self.private_keys[address] = key_pair["private_key"]

                print(f"✅ 从数据库加载了 {len(self.addresses)} 个地址")
            else:
                print("用户没有钱包地址，生成默认地址")
                self.generate_default_addresses()

        except ImportError:
            print("数据库模块不可用，使用默认地址")
            self.generate_default_addresses()
        except Exception as e:
            print(f"从数据库加载钱包失败: {e}")
            self.generate_default_addresses()

    def generate_key_pair(self) -> Dict:
        """生成RSA密钥对"""
        (pub_key, priv_key) = rsa.newkeys(512)

        # 转换为可存储格式
        pub_key_str = pub_key.save_pkcs1().decode('utf-8')
        priv_key_str = priv_key.save_pkcs1().decode('utf-8')

        # 生成地址（公钥的哈希）
        address = self.public_key_to_address(pub_key_str)

        return {
            "address": address,
            "public_key": pub_key_str,
            "private_key": priv_key_str
        }

    def public_key_to_address(self, public_key: str) -> str:
        """将公钥转换为地址"""
        # 先哈希公钥
        key_hash = hashlib.sha256(public_key.encode()).hexdigest()
        # 取前20个字符作为地址
        address = f"0x{key_hash[:40]}"
        return address

    def generate_default_addresses(self):
        """生成默认地址"""
        # 生成5个默认地址
        for i in range(5):
            key_pair = self.generate_key_pair()
            address = key_pair["address"]

            self.addresses.append(address)
            self.public_keys[address] = key_pair["public_key"]
            self.private_keys[address] = key_pair["private_key"]

        # 添加特殊的创世地址
        genesis_address = "genesis"
        self.addresses.insert(0, genesis_address)

    def sign_transaction(self, transaction_data: Dict, address: str) -> Optional[str]:
        """使用私钥对交易进行签名"""
        if address not in self.private_keys:
            print(f"错误：地址 {address} 没有对应的私钥")
            return None

        try:
            # 将交易数据转换为字符串
            data_str = json.dumps(transaction_data, sort_keys=True)

            # 使用私钥签名
            priv_key = rsa.PrivateKey.load_pkcs1(self.private_keys[address])
            signature = rsa.sign(data_str.encode(), priv_key, 'SHA-256')

            # 将签名编码为base64
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            return signature_b64

        except Exception as e:
            print(f"签名失败: {e}")
            return None

    def verify_signature(self, transaction_data: Dict, signature: str, address: str) -> bool:
        """验证交易签名"""
        if address not in self.public_keys:
            return False

        try:
            # 将交易数据转换为字符串
            data_str = json.dumps(transaction_data, sort_keys=True)

            # 解码签名
            signature_bytes = base64.b64decode(signature)

            # 使用公钥验证签名
            pub_key = rsa.PublicKey.load_pkcs1(self.public_keys[address])
            rsa.verify(data_str.encode(), signature_bytes, pub_key)
            return True

        except rsa.VerificationError:
            print("签名验证失败")
            return False
        except Exception as e:
            print(f"验证签名时出错: {e}")
            return False

    def create_signed_transaction(self, blockchain, sender: str, receiver: str,
                                  amount: float, tx_type: str = "transfer",
                                  data: str = "") -> Dict:
        """创建已签名的交易"""
        if sender not in self.addresses:
            print(f"错误：发送方地址 {sender} 不在钱包中")
            return None

        # 创建交易数据
        transaction_data = {
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "type": tx_type,
            "data": data,
            "timestamp": int(time.time())
        }

        # 对交易进行签名
        signature = self.sign_transaction(transaction_data, sender)
        if not signature:
            return None

        # 创建交易对象
        from blockchain import Transaction
        transaction = Transaction(
            sender=sender,
            receiver=receiver,
            amount=amount,
            transaction_type=tx_type,
            data=data
        )

        # 添加到待处理交易池
        if blockchain.add_transaction(transaction):
            print(f"已签名交易创建成功！")
            print(f"交易哈希: {transaction.transaction_id}")
            print(f"签名: {signature[:50]}...")
            return transaction

        return None




    def create_transaction(self,
                           blockchain: Blockchain,
                           sender: str,
                           receiver: str,
                           amount: float) -> bool:
        """
        创建并提交交易

        Args:
            blockchain: 区块链实例
            sender: 发送方地址
            receiver: 接收方地址
            amount: 金额

        Returns:
            bool: 交易是否成功提交
        """
        # 验证发送方是否在钱包地址中
        if sender not in self.addresses:
            print(f"错误：发送方地址 '{sender}' 不在钱包中")
            return False

        # 验证接收方地址格式（简单检查）
        if not receiver or len(receiver) < 3:
            print(f"错误：接收方地址无效")
            return False

        # 验证金额
        if amount <= 0:
            print(f"错误：金额必须大于0")
            return False

        # 创建交易
        transaction = Transaction(sender, receiver, amount)

        # 提交交易到区块链
        success = blockchain.add_transaction(transaction)

        if success:
            print(f"交易创建成功！")
            print(f"交易ID: {transaction.transaction_id}")
        else:
            print("交易创建失败")

        return success

    def get_address_balance(self, blockchain: Blockchain, address: str) -> float:
        """查询地址余额"""
        if address not in self.addresses:
            print(f"警告：地址 '{address}' 不在钱包中")

        balance = blockchain.get_balance(address)
        print(f"地址 '{address}' 的余额: {balance}")
        return balance

    def print_all_balances(self, blockchain: Blockchain) -> None:
        """打印所有地址的余额"""
        print("\n" + "=" * 40)
        print("所有地址余额")
        print("=" * 40)

        total_balance = 0
        for address in self.addresses:
            balance = blockchain.get_balance(address)
            total_balance += balance
            print(f"{address}: {balance}")

        print("-" * 40)
        print(f"总余额: {total_balance}")
        print("=" * 40)