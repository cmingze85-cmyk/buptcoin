# 🏛️ BuptCoin 区块链系统架构文档

## 📚 目录

- [系统概述](#系统概述)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [核心模块](#核心模块)
- [数据流程](#数据流程)
- [数据库设计](#数据库设计)
- [安全机制](#安全机制)
- [性能优化](#性能优化)

---

## 🌐 系统概述

**BuptCoin** 是一个基于 Python 开发的完整区块链系统，实现了区块链的核心功能，包括：

- ✅ **PoW 共识机制**：基于工作量证明的挖矿算法
- ✅ **分布式账本**：MySQL 数据库持久化存储
- ✅ **智能合约**：支持简单的合约部署和执行
- ✅ **P2P 网络**：节点间的区块和交易同步
- ✅ **数字钱包**：基于非对称加密的账户系统
- ✅ **可视化界面**：PyQt5 开发的图形界面

---

## 🛠️ 技术栈

### 后端技术

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 编程语言 | Python | 3.8+ | 核心逻辑开发 |
| 数据库 | MySQL | 8.0+ | 区块链数据存储 |
| 加密库 | hashlib, ecdsa | - | 哈希计算和签名 |
| 网络 | socket | - | P2P 通信 |

### 前端技术

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| GUI 框架 | PyQt5 | 5.15+ | 图形界面开发 |
| 图表库 | matplotlib | 3.5+ | 数据可视化 |

---

## 🏛️ 系统架构

```
┌────────────────────────────────────────────────────────────┐
│                      表示层 (Presentation Layer)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          PyQt5 GUI (gui_enhanced.py + main.py)           │  │
│  │  - 交易管理  - 区块浏览  - 挖矿控制  - 钱包管理  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────┐
│                       业务逻辑层 (Business Layer)                    │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Blockchain Core  │  │  Wallet System  │  │  Network Layer  │  │
│  │  (blockchain.py)  │  │   (wallet.py)    │  │   (network.py)   │  │
│  │                  │  │                  │  │                  │  │
│  │ - Transaction    │  │ - 公钥/私钥生成 │  │ - P2P 连接      │  │
│  │ - Block          │  │ - 数字签名       │  │ - 区块同步      │  │
│  │ - Blockchain     │  │ - 地址管理       │  │ - 交易广播      │  │
│  │ - Mining/PoW     │  │ - 余额查询       │  │ - 节点发现      │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Smart Contract │  │  Merkle Tree    │  │  Utilities      │  │
│  │ (smart_contract) │  │ (merkle_tree.py)│  │   (utils.py)     │  │
│  │                  │  │                  │  │                  │  │
│  │ - 合约部署       │  │ - 交易校验       │  │ - 哈希计算      │  │
│  │ - 合约执行       │  │ - Merkle Root   │  │ - 时间戳生成    │  │
│  │ - 状态管理       │  │ - Merkle Proof  │  │ - 工具函数      │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────┐
│                      数据持久层 (Data Layer)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Database Layer (database.py)              │  │
│  │                                                          │  │
│  │  - MySQL 连接管理           - 区块数据存储              │  │
│  │  - 交易记录管理             - 用户账户管理              │  │
│  │  - 地址余额管理             - 系统统计查询              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                                      │
│                      MySQL Database (buptcoin)                      │
└────────────────────────────────────────────────────────────┘
```

---

## 📦 核心模块

### 1️⃣ Blockchain Core (`blockchain.py`)

**责任：**区块链核心逻辑实现

#### **主要类：**

##### 📦 `Transaction` 类
```python
class Transaction:
    """交易对象"""
    - sender: str          # 发送者地址
    - receiver: str        # 接收者地址
    - amount: float        # 交易金额
    - transaction_type: str # 交易类型（transfer/mining_reward/genesis）
    - timestamp: int       # 时间戳
    - transaction_id: str  # 交易哈希
    - signature: str       # 数字签名
```

**主要方法：**
- `calculate_hash()`: 计算交易哈希
- `to_dict()`: 序列化为字典

##### 🧱 `Block` 类
```python
class Block:
    """区块对象"""
    - index: int               # 区块索引
    - timestamp: int           # 时间戳
    - transactions: List       # 交易列表
    - previous_hash: str       # 前一个区块哈希
    - nonce: int               # 工作量证明随机数
    - hash: str                # 当前区块哈希
    - merkle_tree: MerkleTree  # 默克尔树
```

**主要方法：**
- `calculate_hash()`: 计算区块哈希
- `mine_block(difficulty)`: PoW 挖矿算法
- `to_dict()`: 序列化为字典

##### ⛓️ `Blockchain` 类
```python
class Blockchain:
    """区块链主类"""
    - chain: List[Block]           # 区块链
    - pending_transactions: List   # 待处理交易
    - difficulty: int              # 挖矿难度
    - mining_reward: float         # 挖矿奖励
    - transaction_fee: float       # 交易手续费
```

**主要方法：**
- `create_genesis_block()`: 创建创世区块
- `add_transaction()`: 添加交易
- `mine_pending_transactions()`: 挖矿待处理交易
- `is_chain_valid()`: 验证区块链完整性
- `get_balance()`: 查询地址余额
- `load_from_database()`: 从数据库加载数据

---

### 2️⃣ Wallet System (`wallet.py`)

**责任：**数字钱包管理

#### **主要功能：**
- 🔑 **密钥对生成**：基于 ECDSA 算法生成公私钥
- ✉️ **地址生成**：从公钥生成唯一区块链地址
- ✍️ **数字签名**：使用私钥签名交易
- ✅ **签名验证**：验证交易签名有效性
- 💾 **钱包导出/导入**：备份和恢复钱包

#### **核心方法：**
```python
generate_keypair()      # 生成密钥对
generate_address()      # 生成地址
sign_transaction()      # 签名交易
verify_signature()      # 验证签名
export_wallet()         # 导出钱包
import_wallet()         # 导入钱包
```

---

### 3️⃣ Network Layer (`network.py`)

**责任：**P2P 网络通信

#### **主要功能：**
- 🌐 **节点发现**：自动发现网络中的其他节点
- 🔗 **节点连接**：建立 TCP Socket 连接
- 📤 **数据同步**：同步区块和交易
- 📡 **消息广播**：向所有节点广播新区块/交易

#### **消息类型：**
```python
- NEW_BLOCK       # 新区块通知
- NEW_TRANSACTION # 新交易通知
- REQUEST_CHAIN   # 请求区块链
- SEND_CHAIN      # 发送区块链
- PING/PONG       # 心跳检测
```

---

### 4️⃣ Database Layer (`database.py`)

**责任：**数据持久化存储

#### **核心方法：**
```python
record_block()              # 保存区块
record_transaction()        # 保存交易
get_address_balance()       # 查询余额
update_address_balance()    # 更新余额
get_system_stats()          # 系统统计
get_transaction_history()   # 交易历史
```

---

### 5️⃣ Merkle Tree (`merkle_tree.py`)

**责任：**交易数据校验

#### **主要功能：**
- 🌳 **构建默克尔树**：从交易列表构建
- 🎯 **计算 Root**：生成默克尔根哈希
- ✅ **验证交易**：验证交易是否存在

```python
class MerkleTree:
    build_tree()           # 构建树
    get_root()             # 获取根哈希
    verify_transaction()   # 验证交易
```

---

### 6️⃣ Smart Contract (`smart_contract.py`)

**责任：**智能合约执行

#### **主要功能：**
- 📝 **合约部署**：部署新合约
- ▶️ **合约执行**：执行合约逻辑
- 📊 **状态管理**：管理合约状态

---

### 7️⃣ GUI (`gui_enhanced.py` + `main.py`)

**责任：**用户界面

#### **主要功能模块：**

| 模块 | 功能 |
|------|------|
| 💼 交易管理 | 创建交易、查看交易历史 |
| 📊 区块浏览 | 浏览区块信息、查看区块详情 |
| ⛏️ 挖矿控制 | 启动/停止挖矿、查看算力 |
| 👛 钱包管理 | 创建钱包、导入/导出钱包 |
| 🔍 系统监控 | 网络状态、系统统计 |
| ⚙️ 设置 | 难度设置、网络配置 |

---

## 🔄 数据流程

### 💸 交易流程

```
1. 用户创建交易
   ↓
2. Wallet 签名交易
   ↓
3. Blockchain.add_transaction() 验证
   ↓
4. 交易加入 pending_transactions
   ↓
5. Database 保存 (status=pending)
   ↓
6. Network 广播交易
   ↓
7. 等待挖矿
```

### ⛏️ 挖矿流程

```
1. 矿工启动挖矿
   ↓
2. 打包 pending_transactions
   ↓
3. 创建奖励交易 (mining_reward)
   ↓
4. 创建新区块
   ↓
5. Block.mine_block() - PoW 计算
   ↓
6. 找到有效 nonce
   ↓
7. 区块加入链
   ↓
8. Database 保存区块和交易
   ↓
9. 更新所有地址余额
   ↓
10. Network 广播新区块
```

### 🔍 区块链验证流程

```
1. 验证创世区块
   - index = 0
   - previous_hash = "0" * 64
   ↓
2. 遍历每个区块：
   - 验证索引连续性
   - 验证 previous_hash 链接
   - 验证工作量证明 (hash 前缀)
   ↓
3. 返回验证结果
```

---

## 🗄️ 数据库设计

### 表结构

#### 1. `blocks` 表
```sql
CREATE TABLE blocks (
    block_number INT PRIMARY KEY,
    block_hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    timestamp BIGINT NOT NULL,
    nonce INT NOT NULL,
    difficulty INT NOT NULL,
    merkle_root VARCHAR(64) NOT NULL,
    transaction_count INT NOT NULL,
    miner_address VARCHAR(66),
    block_size INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `transactions` 表
```sql
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_hash VARCHAR(64) UNIQUE NOT NULL,
    from_address VARCHAR(66) NOT NULL,
    to_address VARCHAR(66) NOT NULL,
    amount DECIMAL(20,8) NOT NULL,
    fee DECIMAL(20,8) DEFAULT 0,
    transaction_type VARCHAR(20) NOT NULL,
    data TEXT,
    signature TEXT,
    timestamp BIGINT NOT NULL,
    block_number INT,
    status VARCHAR(20) DEFAULT 'pending',
    confirmations INT DEFAULT 0,
    memo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (block_number) REFERENCES blocks(block_number)
);
```

#### 3. `addresses` 表
```sql
CREATE TABLE addresses (
    address VARCHAR(66) PRIMARY KEY,
    balance DECIMAL(20,8) DEFAULT 0,
    transaction_count INT DEFAULT 0,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 4. `users` 表
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    address VARCHAR(66) UNIQUE NOT NULL,
    public_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 索引优化
```sql
CREATE INDEX idx_tx_hash ON transactions(transaction_hash);
CREATE INDEX idx_tx_from ON transactions(from_address);
CREATE INDEX idx_tx_to ON transactions(to_address);
CREATE INDEX idx_tx_block ON transactions(block_number);
CREATE INDEX idx_tx_status ON transactions(status);
CREATE INDEX idx_block_hash ON blocks(block_hash);
```

---

## 🔒 安全机制

### 1. 加密算法

| 组件 | 算法 | 用途 |
|------|------|------|
| 哈希 | SHA-256 | 区块哈希、交易哈希 |
| 数字签名 | ECDSA | 交易签名验证 |
| 地址生成 | RIPEMD-160 + SHA-256 | 生成区块链地址 |

### 2. 共识机制

**PoW (Proof of Work)**
- 难度调整：默认 difficulty = 2
- 目标：找到 hash 前缀有 N 个 0 的 nonce
- 防止双花：最长链原则

### 3. 验证机制

```python
✅ 交易验证：
  - 签名验证
  - 余额检查
  - 手续费检查

✅ 区块验证：
  - 索引连续性
  - previous_hash 链接
  - 工作量证明
  - Merkle Root 校验

✅ 区块链验证：
  - 创世区块检查
  - 全链完整性
```

---

## ⚡ 性能优化

### 1. 数据库优化
- ✅ 使用索引加速查询
- ✅ 连接池管理
- ✅ 事务批量提交
- ✅ 缓存热数据

### 2. 挖矿优化
- ✅ 多线程挖矿（可扩展）
- ✅ 难度动态调整
- ✅ Nonce 范围分割

### 3. 网络优化
- ✅ 异步 I/O
- ✅ 数据压缩
- ✅ 心跳检测

---

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 初始化数据库
```bash
python BuptCoin/init_database.py
```

### 启动系统
```bash
python BuptCoin/main.py
```

---

## 📚 相关文档

- [QUICKSTART.md](./BuptCoin/QUICKSTART.md) - 快速开始指南
- [ENHANCEMENT_GUIDE.md](./BuptCoin/ENHANCEMENT_GUIDE.md) - 功能增强指南

---

## 📝 License

MIT License

---

## 👥 Contributors

- cmingze85-cmyk - 主要开发者

---

⭐ **Star this repo if you find it helpful!**
