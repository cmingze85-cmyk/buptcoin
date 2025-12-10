# database.py - MySQL 版本，数据库名: buptcoin
import mysql.connector
from mysql.connector import Error
import json
import hashlib
import rsa
import base64
import time
import os
from typing import List, Dict, Optional, Any
from datetime import datetime


class BuptCoinDatabase:
    """BuptCoin 数据库管理器"""

    def __init__(self, host='localhost', user='root', password='', database='buptcoin'):
        """
        初始化数据库连接

        Args:
            host: 数据库主机，默认 localhost
            user: 用户名，默认 root
            password: 密码，默认为空
            database: 数据库名，默认为 buptcoin
        """
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_general_ci'
        }
        self.connection = None
        self.is_connected = False

        print(f"📊 数据库配置:")
        print(f"  主机: {host}")
        print(f"  数据库: {database}")
        print(f"  用户: {user}")

        # 尝试连接
        self.connect()

    def connect(self, max_retries=3) -> bool:
        """连接到 MySQL 数据库"""
        for attempt in range(max_retries):
            try:
                print(f"尝试连接数据库 (第 {attempt + 1} 次)...")

                self.connection = mysql.connector.connect(
                    host=self.config['host'],
                    user=self.config['user'],
                    password=self.config['password'],
                    database=self.config['database'] if self.config['database'] else None,
                    charset=self.config['charset'],
                    autocommit=True
                )

                if self.connection.is_connected():
                    db_info = self.connection.get_server_info()
                    print(f"✅ 成功连接到 MySQL 服务器 (版本: {db_info})")
                    print(f"✅ 数据库: {self.config['database']}")
                    self.is_connected = True

                    # 初始化数据库
                    self.init_database()
                    return True

            except Error as e:
                error_msg = str(e)
                print(f"❌ 连接失败: {error_msg}")

                # 处理特定错误
                if "Unknown database" in error_msg and self.config['database']:
                    print(f"数据库 '{self.config['database']}' 不存在，尝试创建...")
                    if self.create_database():
                        continue  # 重试连接

                elif "Access denied" in error_msg:
                    print("用户名或密码错误")
                    self.prompt_for_credentials()
                    continue

                elif "Can't connect" in error_msg:
                    print("无法连接到 MySQL 服务器，请检查:")
                    print("1. MySQL 服务是否启动")
                    print("2. 主机地址是否正确")
                    print("3. 端口是否被占用 (默认 3306)")

                    if attempt < max_retries - 1:
                        print("等待 3 秒后重试...")
                        time.sleep(3)
                    continue

        print("❌ 多次连接尝试失败")
        return False

    def prompt_for_credentials(self):
        """提示用户输入数据库凭据"""
        print("\n🔧 请输入数据库连接信息:")
        self.config['host'] = input(f"主机地址 [{self.config['host']}]: ") or self.config['host']
        self.config['user'] = input(f"用户名 [{self.config['user']}]: ") or self.config['user']
        self.config['password'] = input(f"密码: ") or self.config['password']
        self.config['database'] = input(f"数据库名 [{self.config['database']}]: ") or self.config['database']

    def create_database(self) -> bool:
        """创建数据库"""
        try:
            # 先连接到 MySQL 服务器（不指定数据库）
            temp_conn = mysql.connector.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password']
            )

            if temp_conn.is_connected():
                cursor = temp_conn.cursor()

                # 创建数据库
                db_name = self.config['database']
                cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS {db_name} 
                CHARACTER SET {self.config['charset']} 
                COLLATE {self.config['collation']}
                """)

                print(f"✅ 数据库 '{db_name}' 创建成功")

                cursor.close()
                temp_conn.close()
                return True

        except Error as e:
            print(f"❌ 创建数据库失败: {e}")

            # 尝试使用 root 用户创建（如果当前用户权限不足）
            if "Access denied" in str(e):
                print("尝试使用 root 用户创建数据库...")
                root_password = input("请输入 root 用户密码: ").strip()

                try:
                    root_conn = mysql.connector.connect(
                        host=self.config['host'],
                        user='root',
                        password=root_password
                    )

                    cursor = root_conn.cursor()
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']}")
                    cursor.execute(
                        f"GRANT ALL PRIVILEGES ON {self.config['database']}.* TO '{self.config['user']}'@'%'")
                    cursor.execute("FLUSH PRIVILEGES")

                    root_conn.commit()
                    cursor.close()
                    root_conn.close()

                    print("✅ 使用 root 用户创建数据库成功")
                    return True

                except Error as root_err:
                    print(f"❌ 使用 root 用户创建数据库失败: {root_err}")

        return False

    def init_database(self):
        """初始化所有表"""
        if not self.is_connected:
            print("❌ 数据库未连接")
            return

        try:
            cursor = self.connection.cursor()

            print("正在创建数据库表...")

            # 1. 用户表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                is_active BOOLEAN DEFAULT TRUE,
                avatar_url VARCHAR(255),
                bio TEXT,
                INDEX idx_username (username),
                INDEX idx_email (email),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("✅ 用户表创建完成")

            # 2. 钱包地址表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallet_addresses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                address VARCHAR(50) UNIQUE NOT NULL,
                nickname VARCHAR(50),
                public_key TEXT NOT NULL,
                private_key_encrypted TEXT NOT NULL,
                balance DECIMAL(18, 8) DEFAULT 0.00000000,
                total_received DECIMAL(18, 8) DEFAULT 0.00000000,
                total_sent DECIMAL(18, 8) DEFAULT 0.00000000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP NULL,
                is_default BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                INDEX idx_user_id (user_id),
                INDEX idx_address (address),
                INDEX idx_nickname (nickname),
                INDEX idx_balance (balance),
                INDEX idx_created_at (created_at),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("✅ 钱包地址表创建完成")

            # 3. 交易记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                transaction_hash VARCHAR(64) UNIQUE NOT NULL,
                block_number INT,
                from_address VARCHAR(50) NOT NULL,
                to_address VARCHAR(50) NOT NULL,
                signature TEXT NOT NULL,
                fee DECIMAL(18, 8) DEFAULT 0.00000000,
                transaction_type VARCHAR(20) DEFAULT 'transfer',
                data TEXT,
                timestamp BIGINT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                confirmations INT DEFAULT 0,
                memo VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_from_address (from_address),
                INDEX idx_to_address (to_address),
                INDEX idx_transaction_hash (transaction_hash),
                INDEX idx_timestamp (timestamp),
                INDEX idx_status (status),
                INDEX idx_block_number (block_number),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("✅ 交易记录表创建完成")

            # 4. 区块表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                block_number INT UNIQUE NOT NULL,
                block_hash VARCHAR(64) UNIQUE NOT NULL,
                previous_hash VARCHAR(64) NOT NULL,
                timestamp BIGINT NOT NULL,
                difficulty INT NOT NULL,
                nonce BIGINT NOT NULL,
                merkle_root VARCHAR(64),
                transaction_count INT DEFAULT 0,
                miner_address VARCHAR(50),
                block_size INT,
                gas_used DECIMAL(18, 8),
                gas_limit DECIMAL(18, 8),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_block_number (block_number),
                INDEX idx_block_hash (block_hash),
                INDEX idx_timestamp (timestamp),
                INDEX idx_miner_address (miner_address)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("✅ 区块表创建完成")

            # 5. 智能合约表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_contracts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contract_address VARCHAR(50) UNIQUE NOT NULL,
                creator_address VARCHAR(50) NOT NULL,
                contract_name VARCHAR(100),
                contract_symbol VARCHAR(20),
                total_supply DECIMAL(18, 8) DEFAULT 0.00000000,
                bytecode TEXT,
                abi_json TEXT,
                balance DECIMAL(18, 8) DEFAULT 0.00000000,
                created_at BIGINT,
                is_active BOOLEAN DEFAULT TRUE,
                description TEXT,
                INDEX idx_contract_address (contract_address),
                INDEX idx_creator_address (creator_address),
                INDEX idx_contract_name (contract_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("✅ 智能合约表创建完成")

            # 6. 系统配置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                config_key VARCHAR(50) PRIMARY KEY,
                config_value TEXT,
                description VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                updated_by VARCHAR(50) DEFAULT 'system'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("✅ 系统配置表创建完成")

            # 7. 质押记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS stakes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                address VARCHAR(50) NOT NULL,
                amount DECIMAL(18, 8) NOT NULL,
                start_time BIGINT NOT NULL,
                end_time BIGINT,
                status VARCHAR(20) DEFAULT 'active',
                reward_earned DECIMAL(18, 8) DEFAULT 0.00000000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_address (address),
                INDEX idx_status (status),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("✅ 质押记录表创建完成")

            # 8. 投票记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                voter_address VARCHAR(50) NOT NULL,
                proposal_id VARCHAR(50) NOT NULL,
                vote_option VARCHAR(50) NOT NULL,
                vote_power DECIMAL(18, 8) NOT NULL,
                timestamp BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_voter_address (voter_address),
                INDEX idx_proposal_id (proposal_id),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("✅ 投票记录表创建完成")

            self.connection.commit()
            cursor.close()

            # 初始化默认数据
            self.init_default_data()

            print("✅ 所有数据库表初始化完成")

        except Error as e:
            print(f"❌ 初始化数据库表失败: {e}")
            if "already exists" not in str(e):
                raise

    def init_default_data(self):
        """初始化默认数据"""
        try:
            cursor = self.connection.cursor()

            # 检查是否已有系统用户
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'system'")
            if cursor.fetchone()[0] == 0:
                # 创建系统用户
                system_hash = hashlib.sha256('system'.encode()).hexdigest()
                cursor.execute('''
                INSERT INTO users (id, username, password_hash, email, is_active) 
                VALUES (1, 'system', %s, 'system@buptcoin.org', TRUE)
                ''', (system_hash,))
                print("✅ 系统用户创建完成")

            # 检查是否已有创世地址
            cursor.execute("SELECT COUNT(*) FROM wallet_addresses WHERE address = 'genesis'")
            if cursor.fetchone()[0] == 0:
                # 创建创世地址
                cursor.execute('''
                INSERT INTO wallet_addresses 
                (user_id, address, nickname, public_key, private_key_encrypted, balance, is_default, is_active) 
                VALUES 
                (1, 'genesis', '创世地址', 'system_public_key', 'system_private_key', 
                 1000000.00000000, TRUE, TRUE)
                ''')
                print("✅ 创世地址创建完成")

            # 初始化系统配置
            default_configs = [
                ('difficulty', '2', '挖矿难度'),
                ('mining_reward', '10.00000000', '挖矿奖励'),
                ('transaction_fee', '0.10000000', '交易手续费'),
                ('block_time', '10', '出块时间(秒)'),
                ('network_name', 'BuptCoin Mainnet', '网络名称'),
                ('version', '3.0.0', '系统版本'),
                ('total_supply', '1000000', '总发行量'),
                ('max_supply', '21000000', '最大发行量'),
                ('inflation_rate', '0.05', '通胀率'),
                ('stake_reward_rate', '0.08', '质押收益率'),
                ('min_stake_amount', '100.0', '最小质押数量'),
                ('vote_min_stake', '1000.0', '投票最小质押'),
                ('database_version', '1.0.0', '数据库版本')
            ]

            for key, value, desc in default_configs:
                cursor.execute('''
                INSERT INTO system_config (config_key, config_value, description) 
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE config_value = %s, description = %s
                ''', (key, value, desc, value, desc))

            self.connection.commit()
            cursor.close()
            print("✅ 默认配置初始化完成")

        except Error as e:
            print(f"❌ 初始化默认数据失败: {e}")

    # ==================== 用户管理方法 ====================

    def create_user(self, username: str, password: str, email: str = None,
                    phone: str = None, avatar_url: str = None, bio: str = None) -> Optional[int]:
        """创建新用户"""
        try:
            cursor = self.connection.cursor()

            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                print(f"❌ 用户名 '{username}' 已存在")
                cursor.close()
                return None

            # 检查邮箱是否已存在
            if email:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    print(f"❌ 邮箱 '{email}' 已被注册")
                    cursor.close()
                    return None

            # 创建密码哈希
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            cursor.execute('''
            INSERT INTO users (username, password_hash, email, phone, avatar_url, bio) 
            VALUES (%s, %s, %s, %s, %s, %s)
            ''', (username, password_hash, email, phone, avatar_url, bio))

            user_id = cursor.lastrowid
            self.connection.commit()
            cursor.close()

            print(f"✅ 用户 '{username}' 创建成功，ID: {user_id}")
            return user_id

        except Error as e:
            print(f"❌ 创建用户失败: {e}")
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """用户认证"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            cursor.execute('''
            SELECT id, username, password_hash, email, created_at, avatar_url, bio 
            FROM users 
            WHERE username = %s AND is_active = TRUE
            ''', (username,))

            user = cursor.fetchone()
            cursor.close()

            if user:
                input_hash = hashlib.sha256(password.encode()).hexdigest()
                if user['password_hash'] == input_hash:
                    # 更新最后登录时间
                    self.update_user_last_login(user['id'])
                    return user

            return None

        except Error as e:
            print(f"❌ 用户认证失败: {e}")
            return None

    def update_user_last_login(self, user_id: int):
        """更新用户最后登录时间"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s
            ''', (user_id,))
            self.connection.commit()
            cursor.close()
        except Error:
            pass

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            cursor.execute('''
            SELECT id, username, email, phone, created_at, last_login, avatar_url, bio 
            FROM users 
            WHERE id = %s AND is_active = TRUE
            ''', (user_id,))

            user = cursor.fetchone()
            cursor.close()
            return user

        except Error as e:
            print(f"❌ 获取用户信息失败: {e}")
            return None

    # ==================== 钱包地址管理 ====================

    def create_wallet_address(self, user_id: int, nickname: str = None) -> Optional[Dict]:
        """创建钱包地址"""
        try:
            # 生成密钥对
            (pub_key, priv_key) = rsa.newkeys(512)
            pub_key_str = pub_key.save_pkcs1().decode('utf-8')
            priv_key_str = priv_key.save_pkcs1().decode('utf-8')

            # 生成地址（公钥的哈希）
            address_hash = hashlib.sha256(pub_key_str.encode()).hexdigest()
            address = f"BPC_{address_hash[:40]}"

            # 加密私钥
            encrypted_priv_key = base64.b64encode(priv_key_str.encode()).decode('utf-8')

            cursor = self.connection.cursor()

            # 检查地址是否已存在（极小概率但检查一下）
            cursor.execute("SELECT id FROM wallet_addresses WHERE address = %s", (address,))
            if cursor.fetchone():
                cursor.close()
                print("❌ 地址生成冲突，请重试")
                return None

            # 检查昵称是否重复
            if nickname:
                cursor.execute("SELECT id FROM wallet_addresses WHERE nickname = %s", (nickname,))
                if cursor.fetchone():
                    cursor.close()
                    print(f"❌ 昵称 '{nickname}' 已被使用")
                    return None

            # 插入地址记录
            cursor.execute('''
            INSERT INTO wallet_addresses 
            (user_id, address, nickname, public_key, private_key_encrypted, balance) 
            VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, address, nickname, pub_key_str, encrypted_priv_key, 0.0))

            address_id = cursor.lastrowid

            # 如果是用户的第一个地址，设置为默认地址
            cursor.execute('''
            SELECT COUNT(*) FROM wallet_addresses WHERE user_id = %s
            ''', (user_id,))
            count = cursor.fetchone()[0]

            if count == 1:
                cursor.execute('''
                UPDATE wallet_addresses SET is_default = TRUE WHERE id = %s
                ''', (address_id,))

            self.connection.commit()
            cursor.close()

            # 获取完整地址信息
            address_info = self.get_address_info(address)
            if address_info:
                print(f"✅ 钱包地址创建成功")
                print(f"   地址: {address_info['address']}")
                print(f"   昵称: {address_info['nickname']}")
                print(f"   余额: {address_info['balance']:.8f} BPC")

            return address_info

        except ImportError:
            print("❌ 需要安装 rsa 库: pip install rsa")
            return None
        except Error as e:
            print(f"❌ 创建钱包地址失败: {e}")
            return None

    def get_address_info(self, address: str) -> Optional[Dict]:
        """获取地址详细信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            cursor.execute('''
            SELECT 
                wa.id, wa.address, wa.nickname, wa.balance, 
                wa.total_received, wa.total_sent, wa.created_at,
                wa.last_activity, wa.is_default, wa.is_active,
                u.username as owner_name
            FROM wallet_addresses wa
            LEFT JOIN users u ON wa.user_id = u.id
            WHERE wa.address = %s
            ''', (address,))

            address_info = cursor.fetchone()
            cursor.close()

            if address_info:
                # 格式化数据
                address_info['balance'] = float(address_info['balance']) if address_info['balance'] else 0.0
                address_info['total_received'] = float(address_info['total_received']) if address_info[
                    'total_received'] else 0.0
                address_info['total_sent'] = float(address_info['total_sent']) if address_info['total_sent'] else 0.0

                if address_info['created_at']:
                    address_info['created_at'] = address_info['created_at'].strftime("%Y-%m-%d %H:%M")
                if address_info['last_activity']:
                    address_info['last_activity'] = address_info['last_activity'].strftime("%Y-%m-%d %H:%M")

                if not address_info['nickname']:
                    address_info['nickname'] = address_info['address'][:10] + "..."

            return address_info

        except Error as e:
            print(f"❌ 获取地址信息失败: {e}")
            return None

    def get_user_addresses(self, user_id: int) -> List[Dict]:
        """获取用户的所有钱包地址"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            cursor.execute('''
            SELECT 
                id, address, nickname, balance, created_at, 
                last_activity, is_default, is_active
            FROM wallet_addresses 
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY is_default DESC, created_at DESC
            ''', (user_id,))

            addresses = cursor.fetchall()
            cursor.close()

            # 格式化数据
            for addr in addresses:
                addr['balance'] = float(addr['balance']) if addr['balance'] else 0.0

                if not addr['nickname']:
                    addr['nickname'] = addr['address'][:10] + "..."

                if addr['created_at']:
                    addr['created_at'] = addr['created_at'].strftime("%Y-%m-%d %H:%M")
                if addr['last_activity']:
                    addr['last_activity'] = addr['last_activity'].strftime("%Y-%m-%d %H:%M")
                else:
                    addr['last_activity'] = "从未使用"

            return addresses

        except Error as e:
            print(f"❌ 获取用户地址列表失败: {e}")
            return []

    def update_address_balance(self, address: str, amount: float,
                               update_type: str = 'add') -> bool:
        """更新地址余额"""
        try:
            cursor = self.connection.cursor()

            if update_type == 'add':
                # 增加余额和总接收
                cursor.execute('''
                UPDATE wallet_addresses 
                SET balance = balance + %s, 
                    total_received = total_received + %s,
                    last_activity = CURRENT_TIMESTAMP
                WHERE address = %s
                ''', (amount, amount if amount > 0 else 0, address))

            elif update_type == 'subtract':
                # 减少余额和增加总发送
                cursor.execute('''
                UPDATE wallet_addresses 
                SET balance = balance - %s, 
                    total_sent = total_sent + %s,
                    last_activity = CURRENT_TIMESTAMP
                WHERE address = %s
                ''', (amount, amount, address))

            else:
                # 直接设置余额
                cursor.execute('''
                UPDATE wallet_addresses 
                SET balance = %s,
                    last_activity = CURRENT_TIMESTAMP
                WHERE address = %s
                ''', (amount, address))

            self.connection.commit()
            affected = cursor.rowcount
            cursor.close()

            return affected > 0

        except Error as e:
            print(f"❌ 更新地址余额失败: {e}")
            return False

    def get_address_balance(self, address: str) -> float:
        """查询地址余额"""
        try:
            cursor = self.connection.cursor()

            cursor.execute('''
            SELECT balance FROM wallet_addresses WHERE address = %s
            ''', (address,))

            result = cursor.fetchone()
            cursor.close()

            return float(result[0]) if result and result[0] is not None else 0.0

        except Error as e:
            print(f"❌ 查询地址余额失败: {e}")
            return 0.0

    def get_address_by_nickname(self, nickname: str) -> Optional[str]:
        """通过昵称获取地址"""
        try:
            cursor = self.connection.cursor()

            cursor.execute('''
            SELECT address FROM wallet_addresses WHERE nickname = %s
            ''', (nickname,))

            result = cursor.fetchone()
            cursor.close()

            return result[0] if result else None

        except Error as e:
            print(f"❌ 通过昵称查询地址失败: {e}")
            return None

    # ==================== 交易管理 ====================

    def record_transaction(self, tx_data: Dict) -> bool:
        """记录交易"""
        try:
            cursor = self.connection.cursor()

            cursor.execute('''
            INSERT INTO transactions 
            (transaction_hash, from_address, to_address, amount, fee, 
             transaction_type, data, timestamp, status, memo) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                tx_data.get('hash'),
                tx_data.get('from'),
                tx_data.get('to'),
                tx_data.get('amount', 0),
                tx_data.get('fee', 0),
                tx_data.get('type', 'transfer'),
                tx_data.get('data', ''),
                tx_data.get('timestamp', int(time.time())),
                tx_data.get('status', 'pending'),
                tx_data.get('memo', '')
            ))

            self.connection.commit()
            cursor.close()
            return True

        except Error as e:
            print(f"❌ 记录交易失败: {e}")
            return False

    def get_transaction_history(self, address: str, limit: int = 50,
                                offset: int = 0) -> List[Dict]:
        """获取地址的交易历史"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            cursor.execute('''
            SELECT 
                transaction_hash, from_address, to_address, amount, fee,
                transaction_type, data, timestamp, status, memo, created_at,
                confirmations, block_number
            FROM transactions 
            WHERE from_address = %s OR to_address = %s 
            ORDER BY timestamp DESC 
            LIMIT %s OFFSET %s
            ''', (address, address, limit, offset))

            transactions = cursor.fetchall()
            cursor.close()

            # 格式化数据
            for tx in transactions:
                tx['direction'] = "发送" if tx['from_address'] == address else "接收"
                tx['counterparty'] = tx['to_address'] if tx['direction'] == "发送" else tx['from_address']
                tx['time_str'] = datetime.fromtimestamp(tx['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                tx['amount'] = float(tx['amount'])
                tx['fee'] = float(tx['fee']) if tx['fee'] else 0.0

                if tx['created_at']:
                    tx['created_at'] = tx['created_at'].strftime("%Y-%m-%d %H:%M:%S")

            return transactions

        except Error as e:
            print(f"❌ 获取交易历史失败: {e}")
            return []

    def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict]:
        """根据哈希获取交易"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            cursor.execute('''
            SELECT * FROM transactions WHERE transaction_hash = %s
            ''', (tx_hash,))

            tx = cursor.fetchone()
            cursor.close()

            if tx:
                tx['amount'] = float(tx['amount']) if tx['amount'] else 0.0
                tx['fee'] = float(tx['fee']) if tx['fee'] else 0.0
                tx['time_str'] = datetime.fromtimestamp(tx['timestamp']).strftime("%Y-%m-%d %H:%M:%S")

                if tx['created_at']:
                    tx['created_at'] = tx['created_at'].strftime("%Y-%m-%d %H:%M:%S")

            return tx

        except Error as e:
            print(f"❌ 获取交易详情失败: {e}")
            return None

    # ==================== 区块管理 ====================

    def record_block(self, block_data: Dict) -> bool:
        """记录区块"""
        try:
            cursor = self.connection.cursor()

            cursor.execute('''
            INSERT INTO blocks 
            (block_number, block_hash, previous_hash, timestamp, difficulty,
             nonce, merkle_root, transaction_count, miner_address, block_size) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                block_data.get('number'),
                block_data.get('hash'),
                block_data.get('previous_hash'),
                block_data.get('timestamp'),
                block_data.get('difficulty'),
                block_data.get('nonce'),
                block_data.get('merkle_root'),
                block_data.get('transaction_count', 0),
                block_data.get('miner'),
                block_data.get('size', 0)
            ))

            self.connection.commit()
            cursor.close()
            return True

        except Error as e:
            print(f"❌ 记录区块失败: {e}")
            return False

    def get_latest_block(self) -> Optional[Dict]:
        """获取最新区块"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            cursor.execute('''
            SELECT * FROM blocks 
            ORDER BY block_number DESC 
            LIMIT 1
            ''')

            block = cursor.fetchone()
            cursor.close()

            if block and block['timestamp']:
                block['time_str'] = datetime.fromtimestamp(block['timestamp']).strftime("%Y-%m-%d %H:%M:%S")

            return block

        except Error as e:
            print(f"❌ 获取最新区块失败: {e}")
            return None

    # ==================== 系统配置 ====================

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        try:
            cursor = self.connection.cursor()

            cursor.execute('''
            SELECT config_value FROM system_config WHERE config_key = %s
            ''', (key,))

            result = cursor.fetchone()
            cursor.close()

            if result and result[0]:
                try:
                    # 尝试解析为数字
                    return float(result[0]) if '.' in result[0] else int(result[0])
                except ValueError:
                    return result[0]

            return default

        except Error:
            return default

    def set_config_value(self, key: str, value: Any, description: str = None):
        """设置配置值"""
        try:
            cursor = self.connection.cursor()

            cursor.execute('''
            INSERT INTO system_config (config_key, config_value, description) 
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE config_value = %s, description = %s
            ''', (key, str(value), description, str(value), description))

            self.connection.commit()
            cursor.close()

        except Error as e:
            print(f"❌ 设置配置失败: {e}")

    # ==================== 统计信息 ====================

    def get_system_stats(self) -> Dict:
        """获取系统统计信息"""
        stats = {}
        try:
            cursor = self.connection.cursor(dictionary=True)

            # 用户统计
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE id > 1 AND is_active = TRUE")
            stats['active_users'] = cursor.fetchone()['count']

            # 地址统计
            cursor.execute("SELECT COUNT(*) as count FROM wallet_addresses WHERE is_active = TRUE")
            stats['active_addresses'] = cursor.fetchone()['count']

            # 交易统计
            cursor.execute("SELECT COUNT(*) as count FROM transactions")
            stats['total_transactions'] = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE status = 'confirmed'")
            stats['confirmed_transactions'] = cursor.fetchone()['count']

            # 余额统计
            cursor.execute("SELECT SUM(balance) as total FROM wallet_addresses WHERE is_active = TRUE")
            total = cursor.fetchone()['total']
            stats['total_balance'] = float(total) if total else 0.0

            # 区块统计
            cursor.execute("SELECT COUNT(*) as count FROM blocks")
            stats['block_count'] = cursor.fetchone()['count']

            # 今日活跃
            cursor.execute("""
            SELECT COUNT(DISTINCT from_address) as active_today 
            FROM transactions 
            WHERE DATE(FROM_UNIXTIME(timestamp)) = CURDATE()
            """)
            stats['active_addresses_today'] = cursor.fetchone()['active_today']

            # 获取最新区块
            latest_block = self.get_latest_block()
            if latest_block:
                stats['latest_block'] = latest_block['block_number']
                stats['latest_block_hash'] = latest_block['block_hash'][:16] + "..."
            else:
                stats['latest_block'] = 0
                stats['latest_block_hash'] = "无"

            cursor.close()

        except Error as e:
            print(f"❌ 获取统计信息失败: {e}")

        return stats

    def get_rich_list(self, limit: int = 10) -> List[Dict]:
        """获取富豪榜"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            cursor.execute('''
            SELECT 
                wa.address, 
                wa.nickname, 
                wa.balance,
                u.username as owner_name
            FROM wallet_addresses wa
            LEFT JOIN users u ON wa.user_id = u.id
            WHERE wa.is_active = TRUE AND wa.balance > 0
            ORDER BY wa.balance DESC
            LIMIT %s
            ''', (limit,))

            rich_list = cursor.fetchall()
            cursor.close()

            # 格式化数据
            for item in rich_list:
                item['balance'] = float(item['balance']) if item['balance'] else 0.0
                if not item['nickname']:
                    item['nickname'] = item['address'][:10] + "..."

            return rich_list

        except Error as e:
            print(f"❌ 获取富豪榜失败: {e}")
            return []

    # ==================== 数据备份 ====================

    def export_data(self, export_dir: str = "exports"):
        """导出数据"""
        try:
            import csv
            import os

            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 导出地址
            addresses = self.get_rich_list(limit=1000)
            if addresses:
                csv_file = os.path.join(export_dir, f"addresses_{timestamp}.csv")
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['address', 'nickname', 'balance', 'owner_name'])
                    writer.writeheader()
                    writer.writerows(addresses)
                print(f"✅ 地址数据已导出到: {csv_file}")

            # 导出交易
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute('''
            SELECT transaction_hash, from_address, to_address, amount, fee, 
                   transaction_type, timestamp, status
            FROM transactions 
            ORDER BY timestamp DESC 
            LIMIT 1000
            ''')

            transactions = cursor.fetchall()
            cursor.close()

            if transactions:
                csv_file = os.path.join(export_dir, f"transactions_{timestamp}.csv")
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'transaction_hash', 'from_address', 'to_address',
                        'amount', 'fee', 'transaction_type', 'timestamp', 'status'
                    ])
                    writer.writeheader()
                    writer.writerows(transactions)
                print(f"✅ 交易数据已导出到: {csv_file}")

            print(f"✅ 数据导出完成，目录: {export_dir}")

        except Exception as e:
            print(f"❌ 导出数据失败: {e}")



    # ==================== 数据库维护 ====================

    def backup_database(self, backup_dir: str = "backups"):
        """备份数据库"""
        try:
            import subprocess
            import os

            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"buptcoin_backup_{timestamp}.sql")

            # 构建 mysqldump 命令
            cmd = ['mysqldump']

            # 添加参数
            cmd.extend(['-h', self.config['host']])
            cmd.extend(['-u', self.config['user']])

            # 处理密码参数（避免引号嵌套问题）
            if self.config['password']:
                # 方法1：使用双引号
                cmd.append(f"--password={self.config['password']}")

            cmd.extend([
                '--skip-comments',
                '--skip-extended-insert',
                '--single-transaction',
                self.config['database']
            ])

            print(f"正在备份数据库到: {backup_file}")
            print(f"执行命令: {' '.join(cmd[:5])} [密码已隐藏] {' '.join(cmd[5:])}")

            with open(backup_file, 'w', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)

                if result.returncode == 0:
                    print(f"✅ 数据库备份成功: {backup_file}")

                    # 压缩备份文件
                    import gzip
                    compressed_file = f"{backup_file}.gz"
                    with open(backup_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            f_out.write(f_in.read())

                    os.remove(backup_file)
                    print(f"✅ 备份文件已压缩: {compressed_file}")

                    # 清理旧备份（保留最近5个）
                    backups = [f for f in os.listdir(backup_dir) if f.endswith('.gz')]
                    backups.sort(reverse=True)
                    for old_backup in backups[5:]:
                        os.remove(os.path.join(backup_dir, old_backup))
                        print(f"清理旧备份: {old_backup}")

                else:
                    print(f"❌ 数据库备份失败: {result.stderr}")
                    if os.path.exists(backup_file):
                        os.remove(backup_file)

        except Exception as e:
            print(f"❌ 备份数据库失败: {e}")

    def check_database_health(self):
        """检查数据库健康状态"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            # 检查表状态
            cursor.execute('''
            SELECT 
                TABLE_NAME as table_name,
                TABLE_ROWS as row_count,
                DATA_LENGTH as data_size,
                INDEX_LENGTH as index_size,
                CREATE_TIME as created
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = %s
            ''', (self.config['database'],))

            tables = cursor.fetchall()

            print("\n📊 数据库健康检查")
            print("=" * 80)
            print(f"{'表名':<20} {'记录数':<10} {'数据大小':<12} {'索引大小':<12} {'创建时间':<20}")
            print("-" * 80)

            total_rows = 0
            total_data = 0
            total_index = 0

            for table in tables:
                table_name = table['table_name']
                row_count = table['row_count'] or 0
                data_size = table['data_size'] or 0
                index_size = table['index_size'] or 0
                created = table['created'].strftime("%Y-%m-%d %H:%M") if table['created'] else ""

                print(f"{table_name:<20} {row_count:<10} "
                      f"{data_size / 1024 / 1024:<10.2f} MB {index_size / 1024 / 1024:<10.2f} MB {created:<20}")

                total_rows += row_count
                total_data += data_size
                total_index += index_size

            print("-" * 80)
            print(f"{'总计':<20} {total_rows:<10} "
                  f"{total_data / 1024 / 1024:<10.2f} MB {total_index / 1024 / 1024:<10.2f} MB")
            print("=" * 80)

            cursor.close()

            # 检查连接数
            cursor = self.connection.cursor()
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            connections = cursor.fetchone()
            cursor.close()

            if connections:
                print(f"当前数据库连接数: {connections[1]}")

            return True

        except Error as e:
            print(f"❌ 数据库健康检查失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ 数据库连接已关闭")
            self.is_connected = False


# ==================== 数据库工具函数 ====================

# 修改 create_db_manager() 函数，添加更多配置选项
def create_db_manager():
    """创建数据库管理器实例"""

    print("=" * 60)
    print("BuptCoin 数据库配置")
    print("=" * 60)

    # 尝试多种默认配置
    possible_configs = [
        {'host': 'localhost', 'user': 'root', 'password': '', 'database': 'buptcoin'},
        {'host': 'localhost', 'user': 'root', 'password': 'root', 'database': 'buptcoin'},
        {'host': '127.0.0.1', 'user': 'root', 'password': '', 'database': 'buptcoin'},
        {'host': 'localhost', 'user': 'buptcoin', 'password': 'buptcoin', 'database': 'buptcoin'},
    ]

    # 检查哪个配置能连接
    working_config = None
    for config in possible_configs:
        print(f"尝试连接配置: {config['user']}@{config['host']}/{config['database']}")
        try:
            temp_conn = mysql.connector.connect(
                host=config['host'],
                user=config['user'],
                password=config['password'],
                database=config['database'] if config['database'] else None
            )
            if temp_conn.is_connected():
                temp_conn.close()
                working_config = config
                print(f"✅ 配置可用: {config['user']}@{config['host']}")
                break
        except:
            continue

    if not working_config:
        print("❌ 所有预设配置都不可用，请手动配置")
        # 手动配置
        working_config = {}
        working_config['host'] = input("MySQL主机地址 (默认: localhost): ").strip() or 'localhost'
        working_config['user'] = input("用户名 (默认: root): ").strip() or 'root'
        working_config['password'] = input("密码: ").strip()
        working_config['database'] = input("数据库名 (默认: buptcoin): ").strip() or 'buptcoin'

    # 创建数据库管理器
    db = BuptCoinDatabase(
        host=working_config['host'],
        user=working_config['user'],
        password=working_config['password'],
        database=working_config['database']
    )

    # 保存配置
    try:
        with open("db_config.json", 'w', encoding='utf-8') as f:
            json.dump(working_config, f, indent=2)
        print("✅ 配置已保存到 db_config.json")
    except:
        print("⚠️  无法保存配置到文件")

    return db


# 全局数据库实例
db = create_db_manager()


# 测试函数
def test_database_connection():
    """测试数据库连接和基本功能"""
    if not db.is_connected:
        print("❌ 数据库未连接，无法测试")
        return

    print("\n🔧 测试数据库功能...")

    # 测试创建测试用户
    test_user_id = db.create_user(
        username="test_user_" + str(int(time.time())),
        password="test123",
        email="test@buptcoin.org",
        bio="测试用户"
    )

    if test_user_id:
        print(f"✅ 测试用户创建成功，ID: {test_user_id}")

        # 测试创建钱包地址
        address_info = db.create_wallet_address(test_user_id, "测试钱包")
        if address_info:
            print(f"✅ 测试钱包创建成功: {address_info['address']}")

            # 测试更新余额
            if db.update_address_balance(address_info['address'], 500.0):
                print(f"✅ 余额更新成功")

                # 测试查询余额
                balance = db.get_address_balance(address_info['address'])
                print(f"✅ 查询余额: {balance:.8f} BPC")

                # 测试获取地址列表
                addresses = db.get_user_addresses(test_user_id)
                print(f"✅ 获取地址列表: {len(addresses)} 个地址")

        # 测试系统统计
        stats = db.get_system_stats()
        print(f"✅ 系统统计: {stats}")

        # 测试富豪榜
        rich_list = db.get_rich_list(limit=5)
        if rich_list:
            print(f"✅ 富豪榜: {len(rich_list)} 个地址")
            for i, rich in enumerate(rich_list[:3], 1):
                print(f"  {i}. {rich['nickname']}: {rich['balance']:.2f} BPC")

    print("✅ 数据库测试完成")


def run_database_admin():
    """运行数据库管理界面"""
    if not db.is_connected:
        print("❌ 数据库未连接")
        return

    while True:
        print("\n" + "=" * 60)
        print("BuptCoin 数据库管理")
        print("=" * 60)
        print("1. 查看系统统计")
        print("2. 查看富豪榜")
        print("3. 检查数据库健康")
        print("4. 备份数据库")
        print("5. 导出数据")
        print("6. 运行 SQL 查询")
        print("7. 返回主菜单")
        print("=" * 60)

        choice = input("请选择操作 (1-7): ").strip()

        if choice == '1':
            stats = db.get_system_stats()
            print("\n📊 系统统计信息:")
            print(f"  活跃用户: {stats.get('active_users', 0)}")
            print(f"  活跃地址: {stats.get('active_addresses', 0)}")
            print(f"  总交易数: {stats.get('total_transactions', 0)}")
            print(f"  已确认交易: {stats.get('confirmed_transactions', 0)}")
            print(f"  区块数量: {stats.get('block_count', 0)}")
            print(f"  总余额: {stats.get('total_balance', 0):.2f} BPC")
            print(f"  今日活跃地址: {stats.get('active_addresses_today', 0)}")
            print(f"  最新区块: #{stats.get('latest_block', 0)}")
            print(f"  最新区块哈希: {stats.get('latest_block_hash', '无')}")

        elif choice == '2':
            limit = input("显示前多少名？(默认10): ").strip()
            limit = int(limit) if limit.isdigit() else 10

            rich_list = db.get_rich_list(limit=limit)
            if rich_list:
                print(f"\n🏆 富豪榜 (前{limit}名):")
                print("=" * 80)
                print(f"{'排名':<5} {'地址/昵称':<30} {'余额(BPC)':<15} {'所有者':<15}")
                print("-" * 80)

                for i, rich in enumerate(rich_list, 1):
                    print(
                        f"{i:<5} {rich['nickname']:<30} {rich['balance']:<15.2f} {rich.get('owner_name', '系统'):<15}")

                print("=" * 80)
            else:
                print("暂无数据")

        elif choice == '3':
            db.check_database_health()

        elif choice == '4':
            confirm = input("确定要备份数据库吗？(y/N): ").strip().lower()
            if confirm == 'y':
                db.backup_database()

        elif choice == '5':
            export_dir = input("导出目录 (默认: exports): ").strip() or "exports"
            db.export_data(export_dir)

        elif choice == '6':
            print("输入 SQL 查询语句 (输入 'exit' 退出):")
            while True:
                sql = input("SQL> ").strip()
                if sql.lower() in ['exit', 'quit', 'q']:
                    break

                if not sql:
                    continue

                try:
                    cursor = db.connection.cursor(dictionary=True)
                    cursor.execute(sql)

                    if sql.strip().upper().startswith('SELECT'):
                        results = cursor.fetchall()
                        if results:
                            # 简单显示结果
                            import pandas as pd
                            df = pd.DataFrame(results)
                            print(df.to_string(index=False))
                        else:
                            print("查询结果为空")
                    else:
                        db.connection.commit()
                        print(f"执行成功，影响行数: {cursor.rowcount}")

                    cursor.close()

                except Error as e:
                    print(f"SQL 错误: {e}")

        elif choice == '7':
            break

        else:
            print("无效选择")


if __name__ == "__main__":
    if db.is_connected:
        # 运行数据库测试
        test_database_connection()

        # 运行数据库管理界面
        run_database_admin()

        # 关闭数据库连接
        db.close()
    else:
        print("❌ 数据库连接失败，请检查配置")