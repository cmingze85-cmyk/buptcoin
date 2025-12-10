"""
数据库初始化脚本
运行此脚本创建数据库和表
"""

import mysql.connector
from mysql.connector import Error
import json
import sys


def init_database():
    """初始化数据库"""

    print("=" * 60)
    print("BuptCoin 数据库初始化工具")
    print("=" * 60)

    # 获取数据库配置
    config = {}
    config['host'] = input("MySQL主机地址 (默认: localhost): ").strip() or 'localhost'
    config['user'] = input("用户名 (默认: root): ").strip() or 'root'
    config['password'] = input("密码: ").strip()
    config['database'] = input("数据库名 (默认: buptcoin): ").strip() or 'buptcoin'

    try:
        # 1. 连接到MySQL服务器（不指定数据库）
        connection = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password']
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # 2. 创建数据库（如果不存在）
            print(f"正在创建数据库 '{config['database']}'...")
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
            print(f"✅ 数据库 '{config['database']}' 创建成功")

            # 3. 切换到新数据库
            cursor.execute(f"USE {config['database']}")

            # 4. 创建所有表
            print("正在创建数据表...")

            # 用户表
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

            # 钱包地址表
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

            # 交易记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                transaction_hash VARCHAR(64) UNIQUE NOT NULL,
                block_number INT,
                from_address VARCHAR(50) NOT NULL,
                to_address VARCHAR(50) NOT NULL,
                amount DECIMAL(18, 8) NOT NULL,
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

            # 区块表
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

            # 5. 创建系统用户和创世地址
            print("\n正在创建初始数据...")

            # 创建系统用户
            import hashlib
            system_hash = hashlib.sha256('system'.encode()).hexdigest()
            cursor.execute('''
            INSERT IGNORE INTO users (id, username, password_hash, email, is_active) 
            VALUES (1, 'system', %s, 'system@buptcoin.org', TRUE)
            ''', (system_hash,))

            # 创建创世地址
            cursor.execute('''
            INSERT IGNORE INTO wallet_addresses 
            (user_id, address, nickname, public_key, private_key_encrypted, balance, is_default, is_active) 
            VALUES 
            (1, 'genesis', '创世地址', 'system_public_key', 'system_private_key', 
             1000000.00000000, TRUE, TRUE)
            ''')

            # 6. 创建系统配置
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                config_key VARCHAR(50) PRIMARY KEY,
                config_value TEXT,
                description VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                updated_by VARCHAR(50) DEFAULT 'system'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            default_configs = [
                ('difficulty', '2', '挖矿难度'),
                ('mining_reward', '10.00000000', '挖矿奖励'),
                ('transaction_fee', '0.10000000', '交易手续费'),
                ('block_time', '10', '出块时间(秒)'),
                ('network_name', 'BuptCoin Mainnet', '网络名称'),
                ('version', '3.0.0', '系统版本'),
                ('total_supply', '1000000', '总发行量'),
                ('max_supply', '21000000', '最大发行量'),
            ]

            for key, value, desc in default_configs:
                cursor.execute('''
                INSERT IGNORE INTO system_config (config_key, config_value, description) 
                VALUES (%s, %s, %s)
                ''', (key, value, desc))

            connection.commit()
            cursor.close()
            connection.close()

            print("\n" + "=" * 60)
            print("✅ 数据库初始化完成！")
            print(f"数据库: {config['database']}")
            print(f"主机: {config['host']}")
            print(f"用户: {config['user']}")

            # 保存配置
            with open("db_config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print("✅ 配置已保存到 db_config.json")

            # 创建测试用户
            print("\n是否创建测试用户？")
            create_test = input("创建测试用户 (y/N): ").strip().lower()
            if create_test == 'y':
                from database import BuptCoinDatabase
                db = BuptCoinDatabase(**config)
                if db.is_connected:
                    # 创建测试用户
                    test_user_id = db.create_user(
                        username="test_user",
                        password="test123",
                        email="test@buptcoin.org",
                        bio="测试用户"
                    )
                    if test_user_id:
                        print(f"✅ 测试用户创建成功")
                        print(f"   用户名: test_user")
                        print(f"   密码: test123")

                        # 创建测试钱包
                        address_info = db.create_wallet_address(test_user_id, "测试钱包")
                        if address_info:
                            # 分配初始余额
                            db.update_address_balance(address_info['address'], 1000.0)
                            print(f"✅ 测试钱包创建成功")
                            print(f"   地址: {address_info['address']}")
                            print(f"   初始余额: 1000.0 BPC")

                    db.close()

            print("\n✅ 初始化全部完成！")
            print("现在可以运行 main.py 启动系统了")

    except Error as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()