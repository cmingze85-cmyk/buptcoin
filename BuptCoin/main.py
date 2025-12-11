import os
import sys
import time
from blockchain import Blockchain, Transaction
from wallet import Wallet

# 在现有导入后添加数据库导入
try:
    from database import db, test_database_connection  # 导入数据库实例

    DATABASE_ENABLED = True
except ImportError:
    DATABASE_ENABLED = False
    print("⚠️  数据库模块不可用，部分功能将受限")


class SimpleCoinCLI:
    def __init__(self):
        # 显示数据库初始化信息
        print("\n" + "=" * 60)
        print("BuptCoin v3.0 - 支持数据库持久化")
        print("=" * 60)

        # 检查数据库连接
        self.database_connected = False
        self.current_user = None

        if DATABASE_ENABLED and hasattr(db, 'is_connected') and db.is_connected:
            self.database_connected = True
            print("✅ 数据库连接成功")

            # 显示数据库统计
            stats = db.get_system_stats()
            print(f"📊 数据库统计:")
            print(f"  区块数量: {stats.get('block_count', 0)}")
            print(f"  总交易数: {stats.get('total_transactions', 0)}")
            print(f"  活跃用户: {stats.get('active_users', 0)}")
            print(f"  活跃地址: {stats.get('active_addresses', 0)}")
            print(f"  总余额: {stats.get('total_balance', 0):.2f} BPC")

            # 用户登录/注册
            self.handle_user_auth()
        else:
            print("⚠️  数据库未连接，使用内存模式")
            print("注意：重启后数据将丢失")
            # 创建访客用户
            self.current_user = {
                'id': 0,
                'username': 'guest',
                'email': None
            }

        # 初始化区块链（它会自动从数据库加载）
        print("\n正在初始化区块链...")
        self.blockchain = Blockchain(difficulty=2)

        # 显示区块链状态
        print(f"✅ 区块链初始化完成")
        print(f"  当前区块数: {len(self.blockchain.chain)}")
        print(f"  待处理交易: {len(self.blockchain.pending_transactions)}")

        # 初始化钱包
        if self.current_user and self.current_user['id'] > 0:
            # 如果用户已登录，使用用户ID初始化钱包
            print(f"正在加载用户 {self.current_user['username']} 的钱包...")
            self.wallet = Wallet(f"User_{self.current_user['id']}_Wallet",
                                 user_id=self.current_user['id'])
        else:
            # 如果没有数据库或未登录，使用默认钱包
            print("正在初始化默认钱包...")
            self.wallet = Wallet("BuptCoin Wallet")

        print("\n✅ 系统初始化完成！")
        print("=" * 60)

    def handle_user_auth(self):
        """处理用户认证"""
        print("\n" + "=" * 40)
        print("用户认证")
        print("=" * 40)
        print("1. 登录现有账户")
        print("2. 注册新账户")
        print("3. 以访客身份继续")

        while True:
            choice = input("\n请选择 (1-3): ").strip()

            if choice == '1':
                self.user_login()
                break
            elif choice == '2':
                self.user_register()
                break
            elif choice == '3':
                print("以访客身份继续，部分功能受限")
                # 创建临时用户
                self.current_user = {
                    'id': 0,
                    'username': 'guest',
                    'email': None
                }
                break
            else:
                print("无效选择，请重新输入")

    def user_login(self):
        """用户登录"""
        print("\n" + "=" * 40)
        print("用户登录")
        print("=" * 40)

        max_attempts = 3
        attempts = 0

        while attempts < max_attempts:
            username = input("用户名: ").strip()
            password = input("密码: ").strip()

            if not username or not password:
                print("❌ 用户名和密码不能为空")
                attempts += 1
                continue

            user = db.authenticate_user(username, password)
            if user:
                self.current_user = user
                print(f"\n✅ 登录成功！欢迎 {username}")

                # 显示用户的钱包地址
                addresses = db.get_user_addresses(user['id'])
                if addresses:
                    print(f"您有 {len(addresses)} 个钱包地址:")
                    for i, addr in enumerate(addresses, 1):
                        default_tag = " [默认]" if addr.get('is_default') else ""
                        print(f"  {i}. {addr['address']}{default_tag}")
                        print(f"     昵称: {addr['nickname']}")
                        print(f"     余额: {addr['balance']:.8f} BPC")
                else:
                    print("您还没有钱包地址，系统将自动创建...")
                    # 自动创建钱包地址
                    new_address = db.create_wallet_address(user['id'], f"{username}的默认钱包")
                    if new_address:
                        print(f"✅ 已创建钱包地址: {new_address['address']}")
                        print(f"   昵称: {new_address['nickname']}")
                        print(f"   余额: {new_address['balance']:.8f} BPC")

                return True
            else:
                attempts += 1
                remaining = max_attempts - attempts
                if remaining > 0:
                    print(f"❌ 用户名或密码错误，还剩 {remaining} 次尝试")
                else:
                    print("❌ 登录失败次数过多")
                    break

        # 登录失败，使用访客模式
        print("将以访客身份继续...")
        self.current_user = {
            'id': 0,
            'username': 'guest',
            'email': None
        }
        return False

    def user_register(self):
        """用户注册"""
        print("\n" + "=" * 40)
        print("用户注册")
        print("=" * 40)

        while True:
            username = input("用户名: ").strip()
            if not username:
                print("❌ 用户名不能为空")
                continue

            password = input("密码: ").strip()
            if len(password) < 6:
                print("❌ 密码长度至少6位")
                continue

            confirm_password = input("确认密码: ").strip()
            if password != confirm_password:
                print("❌ 两次输入的密码不一致")
                continue

            email = input("邮箱 (可选): ").strip()
            if email and '@' not in email:
                print("⚠️  邮箱格式可能不正确，继续吗？")
                confirm = input("(y/N): ").strip().lower()
                if confirm != 'y':
                    continue

            # 创建用户
            user_id = db.create_user(username, password, email)
            if user_id:
                user = db.get_user_by_id(user_id)
                if user:
                    self.current_user = user
                    print(f"\n✅ 注册成功！用户ID: {user_id}")
                    print(f"   用户名: {username}")
                    if email:
                        print(f"   邮箱: {email}")

                    # 自动创建钱包地址
                    print("\n正在创建默认钱包地址...")
                    new_address = db.create_wallet_address(user_id, f"{username}的默认钱包")
                    if new_address:
                        print(f"✅ 钱包地址创建成功！")
                        print(f"   地址: {new_address['address']}")
                        print(f"   昵称: {new_address['nickname']}")
                        print(f"   初始余额: {new_address['balance']:.8f} BPC")

                    return True
                else:
                    print("❌ 用户创建成功但获取信息失败")
            else:
                print("❌ 注册失败，用户名可能已存在")

            retry = input("\n是否重试注册？(y/N): ").strip().lower()
            if retry != 'y':
                break

        # 注册失败，使用访客模式
        print("将以访客身份继续...")
        self.current_user = {
            'id': 0,
            'username': 'guest',
            'email': None
        }
        return False

    def print_menu(self):
        """打印主菜单"""
        print("\n" + "=" * 60)
        print("💰 BuptCoin - 区块链数字货币系统")
        print("=" * 60)

        # 显示当前用户信息
        if self.current_user['id'] > 0:
            print(f"👤 用户: {self.current_user['username']} (ID: {self.current_user['id']})")
        else:
            print("👤 用户: 访客模式")

        print(f"⛓️  当前区块: #{len(self.blockchain.chain)}")
        print(f"📝 待处理交易: {len(self.blockchain.pending_transactions)}")

        print("\n主菜单:")
        print("1. 查看区块链")
        print("2. 查看所有地址余额")
        print("3. 查询单个地址余额")
        print("4. 创建交易 (支持多种类型)")
        print("5. 挖矿")
        print("6. 验证区块链")
        print("7. 查看质押排名")
        print("8. 查看投票结果")
        print("9. 系统信息")
        print("10. 高级功能")

        if self.database_connected:
            print("11. 数据库功能")

        print("0. 退出")
        print("=" * 60)

    def view_blockchain(self):
        """查看区块链"""
        self.blockchain.print_chain()

        # 如果数据库连接，显示更多信息
        if self.database_connected:
            print("\n" + "=" * 40)
            print("数据库区块链信息")
            print("=" * 40)

            # 获取最新区块
            latest_block = db.get_latest_block()
            if latest_block:
                print(f"最新区块: #{latest_block['block_number']}")
                print(f"区块哈希: {latest_block['block_hash'][:20]}...")
                print(f"矿工地址: {latest_block.get('miner_address', '未知')}")
                print(f"交易数量: {latest_block.get('transaction_count', 0)}")

            # 显示富豪榜前5名
            rich_list = db.get_rich_list(limit=5)
            if rich_list:
                print(f"\n🏆 富豪榜前5名:")
                for i, rich in enumerate(rich_list, 1):
                    print(f"  {i}. {rich['nickname']}: {rich['balance']:.2f} BPC")

    def view_all_balances(self):
        """查看所有地址余额"""
        print("\n" + "=" * 60)
        print("所有地址余额")
        print("=" * 60)

        total_balance = 0
        addresses_to_check = []

        # 确定要检查哪些地址
        if self.database_connected and self.current_user['id'] > 0:
            # 从数据库获取用户地址
            addresses_info = db.get_user_addresses(self.current_user['id'])
            if addresses_info:
                print(f"用户 {self.current_user['username']} 的钱包地址:")
                print("-" * 60)
                for addr_info in addresses_info:
                    address = addr_info['address']
                    balance = self.blockchain.get_balance(address)
                    total_balance += balance

                    print(f"地址: {address}")
                    print(f"昵称: {addr_info['nickname']}")
                    print(f"余额: {balance:.8f} BPC")
                    if addr_info.get('is_default'):
                        print("状态: 默认地址")
                    print("-" * 60)

                    addresses_to_check.append(address)
            else:
                print("⚠️  用户没有钱包地址")
                addresses_to_check = self.wallet.addresses
        else:
            # 使用钱包地址
            addresses_to_check = self.wallet.addresses

        # 检查钱包中的其他地址
        for address in addresses_to_check:
            if address not in [addr['address'] for addr in (addresses_info if 'addresses_info' in locals() else [])]:
                balance = self.blockchain.get_balance(address)
                total_balance += balance
                print(f"地址: {address}")
                print(f"余额: {balance:.8f} BPC")
                print("-" * 60)

        print(f"💰 总余额: {total_balance:.8f} BPC")
        print("=" * 60)

    def check_balance(self):
        """查询单个地址余额"""
        print("\n" + "=" * 40)
        print("查询地址余额")
        print("=" * 40)

        # 显示可用地址
        print("\n可用地址:")
        if self.database_connected and self.current_user['id'] > 0:
            # 从数据库获取用户地址
            addresses_info = db.get_user_addresses(self.current_user['id'])
            if addresses_info:
                for i, addr_info in enumerate(addresses_info, 1):
                    default_tag = " [默认]" if addr_info.get('is_default') else ""
                    print(f"{i}. {addr_info['address']}{default_tag} - {addr_info['nickname']}")

        # 显示钱包中的其他地址
        wallet_addresses = [addr for addr in self.wallet.addresses
                            if not self.database_connected or
                            self.current_user['id'] == 0 or
                            not any(addr == db_addr['address']
                                    for db_addr in (addresses_info if 'addresses_info' in locals() else []))]

        if wallet_addresses:
            start_idx = (len(addresses_info) if 'addresses_info' in locals() else 0) + 1
            for i, addr in enumerate(wallet_addresses, start_idx):
                print(f"{i}. {addr}")

        try:
            choice = input("\n请选择地址编号或直接输入地址: ").strip()

            if choice.isdigit():
                idx = int(choice) - 1
                if 'addresses_info' in locals() and 0 <= idx < len(addresses_info):
                    address = addresses_info[idx]['address']
                elif wallet_addresses:
                    wallet_idx = idx - (len(addresses_info) if 'addresses_info' in locals() else 0)
                    if 0 <= wallet_idx < len(wallet_addresses):
                        address = wallet_addresses[wallet_idx]
                    else:
                        print("❌ 编号无效")
                        return
                else:
                    print("❌ 编号无效")
                    return
            else:
                address = choice

            # 查询余额
            balance = self.blockchain.get_balance(address)

            print(f"\n📊 地址信息:")
            print(f"地址: {address}")
            print(f"余额: {balance:.8f} BPC")

            # 如果数据库连接，显示更多信息
            if self.database_connected:
                address_info = db.get_address_info(address)
                if address_info:
                    print(f"昵称: {address_info['nickname']}")
                    print(f"创建时间: {address_info['created_at']}")
                    print(f"最后活动: {address_info['last_activity']}")
                    print(f"总接收: {address_info['total_received']:.8f} BPC")
                    print(f"总发送: {address_info['total_sent']:.8f} BPC")
                    if address_info.get('owner_name'):
                        print(f"所有者: {address_info['owner_name']}")

                    # 显示最近的交易
                    transactions = db.get_transaction_history(address, limit=5)
                    if transactions:
                        print(f"\n最近5笔交易:")
                        for tx in transactions:
                            direction = "📤 发送" if tx['direction'] == "发送" else "📥 接收"
                            print(f"  {direction} {tx['amount']:.8f} BPC")
                            print(f"    对方: {tx['counterparty']}")
                            print(f"    时间: {tx['time_str']}")
                            print(f"    状态: {tx['status']}")
                            print()

        except (ValueError, IndexError) as e:
            print(f"❌ 输入无效: {e}")
        except Exception as e:
            print(f"❌ 查询失败: {e}")

    def create_transaction(self):
        """创建交易"""
        print("\n" + "=" * 60)
        print("创建新交易")
        print("=" * 60)

        # 第一步：选择交易类型
        print("\n请选择交易类型:")
        print("1. 普通转账 (transfer)")
        print("2. 质押代币 (stake)")
        print("3. 投票 (vote)")
        print("4. 智能合约调用 (contract)")

        try:
            type_choice = input("选择交易类型 (1-4，默认1): ").strip()

            if type_choice == "2":
                transaction_type = "stake"
                print("您选择了: 质押代币")
            elif type_choice == "3":
                transaction_type = "vote"
                print("您选择了: 投票")
            elif type_choice == "4":
                transaction_type = "contract"
                print("您选择了: 智能合约调用")
            else:
                transaction_type = "transfer"
                print("您选择了: 普通转账")

            # 第二步：显示可用地址
            print("\n可用地址:")
            available_addresses = []

            # 从数据库获取用户地址
            if self.database_connected and self.current_user['id'] > 0:
                addresses_info = db.get_user_addresses(self.current_user['id'])
                if addresses_info:
                    for addr_info in addresses_info:
                        available_addresses.append({
                            'address': addr_info['address'],
                            'nickname': addr_info['nickname'],
                            'balance': addr_info['balance']
                        })

            # 添加钱包中的其他地址
            for addr in self.wallet.addresses:
                if not any(a['address'] == addr for a in available_addresses):
                    available_addresses.append({
                        'address': addr,
                        'nickname': f"钱包地址{len(available_addresses) + 1}",
                        'balance': self.blockchain.get_balance(addr)
                    })

            # 显示地址
            for i, addr_info in enumerate(available_addresses, 1):
                balance = self.blockchain.get_balance(addr_info['address'])
                print(f"{i}. {addr_info['address']}")
                print(f"   昵称: {addr_info['nickname']}")
                print(f"   余额: {balance:.8f} BPC")
                print()

            # 第三步：选择发送方
            sender_input = input("\n选择发送方编号或直接输入地址: ").strip()
            if sender_input.isdigit():
                idx = int(sender_input) - 1
                if 0 <= idx < len(available_addresses):
                    sender = available_addresses[idx]['address']
                else:
                    print("❌ 编号无效")
                    return
            else:
                sender = sender_input

            # 检查发送方地址是否有效
            sender_valid = any(addr['address'] == sender for addr in available_addresses)
            if not sender_valid:
                print(f"⚠️  发送方地址 '{sender}' 不在可用地址列表中")
                confirm = input("是否继续？(y/n): ").lower()
                if confirm != 'y':
                    return

            # 第四步：根据交易类型处理接收方
            receiver = sender  # 默认接收方为自己（如质押）
            extra_data = ""  # 附加数据

            if transaction_type == "transfer":
                # 普通转账需要选择接收方
                print("\n选择接收方地址:")
                for i, addr_info in enumerate(available_addresses, 1):
                    if addr_info['address'] != sender:  # 不显示发送方自己
                        print(f"{i}. {addr_info['address']} ({addr_info['nickname']})")

                receiver_input = input("选择接收方编号或输入地址: ").strip()
                if receiver_input.isdigit():
                    idx = int(receiver_input) - 1
                    if 0 <= idx < len(available_addresses):
                        receiver = available_addresses[idx]['address']
                    else:
                        print("❌ 编号无效")
                        return
                else:
                    receiver = receiver_input

                if receiver == sender:
                    print("⚠️  发送方和接收方相同！")
                    confirm = input("是否继续？(y/n): ").lower()
                    if confirm != 'y':
                        return

                memo = input("备注 (可选): ").strip()
                if memo:
                    extra_data = f"备注: {memo}"

            elif transaction_type == "stake":
                # 质押交易：接收方是自己
                receiver = sender
                print(f"质押交易：{sender} 质押代币给自己")
                stake_period = input("质押周期 (天，默认30): ").strip() or "30"
                extra_data = f"质押周期: {stake_period}天"

            elif transaction_type == "vote":
                # 投票交易：接收方是投票池
                receiver = "vote_pool"
                print("投票交易：需要指定候选人")
                candidates = ["候选人A", "候选人B", "候选人C"]
                for i, candidate in enumerate(candidates, 1):
                    print(f"{i}. {candidate}")

                candidate_choice = input("选择候选人编号或输入候选人名称: ").strip()
                if candidate_choice.isdigit():
                    idx = int(candidate_choice) - 1
                    if 0 <= idx < len(candidates):
                        candidate = candidates[idx]
                    else:
                        print("❌ 编号无效")
                        return
                else:
                    candidate = candidate_choice

                extra_data = f"投票给: {candidate}"
                print(f"您将投票给: {candidate}")

            elif transaction_type == "contract":
                # 智能合约调用
                print("智能合约调用")
                contract_address = input("请输入合约地址 (或按回车使用默认): ").strip()
                if contract_address:
                    receiver = contract_address
                else:
                    receiver = "contract_address"

                print("可用的合约函数:")
                print("1. transfer(address, amount) - 转账")
                print("2. getBalance(address) - 查询余额")
                print("3. mint(amount) - 铸造代币")
                print("4. deploy - 部署新合约")

                func_choice = input("选择函数 (1-4): ").strip()
                if func_choice == "1":
                    target_address = input("输入目标地址: ").strip()
                    amount = input("输入转账金额: ").strip()
                    extra_data = f"contract_call:transfer({target_address},{amount})"
                elif func_choice == "2":
                    query_address = input("输入查询地址: ").strip()
                    extra_data = f"contract_call:getBalance({query_address})"
                elif func_choice == "3":
                    amount = input("输入铸造金额: ").strip()
                    extra_data = f"contract_call:mint({amount})"
                elif func_choice == "4":
                    extra_data = "contract_deploy"
                else:
                    extra_data = "contract_call:unknown"

            # 第五步：输入金额
            try:
                amount_input = input("\n输入金额: ").strip()
                amount = float(amount_input)

                if amount <= 0:
                    print("❌ 金额必须大于0")
                    return

                # 检查余额
                sender_balance = self.blockchain.get_balance(sender)
                total_cost = amount + self.blockchain.transaction_fee

                if sender_balance < total_cost:
                    print(f"❌ 余额不足！")
                    print(f"  需要: {total_cost:.8f}")
                    print(f"  余额: {sender_balance:.8f}")
                    return

                # 显示手续费信息
                if transaction_type != "stake":  # 质押不显示手续费（因为是给自己）
                    print(f"\n💰 交易详情:")
                    print(f"  转账金额: {amount:.8f}")
                    print(f"  手续费: {self.blockchain.transaction_fee:.8f}")
                    print(f"  总计支出: {total_cost:.8f}")

            except ValueError:
                print("❌ 金额必须是数字")
                return

            # 第六步：确认交易
            print("\n" + "=" * 40)
            print("交易详情确认")
            print("=" * 40)
            print(f"类型: {transaction_type}")
            print(f"发送方: {sender}")
            print(f"接收方: {receiver}")
            print(f"金额: {amount:.8f}")
            if transaction_type == "transfer" and self.blockchain.transaction_fee > 0:
                print(f"手续费: {self.blockchain.transaction_fee:.8f}")
                print(f"总计: {amount + self.blockchain.transaction_fee:.8f}")
            if extra_data:
                print(f"附加数据: {extra_data}")

            confirm = input("\n确认创建此交易？(y/n): ").lower()
            if confirm != 'y':
                print("交易已取消")
                return

            # 第七步：创建并提交交易
            print("\n正在创建交易...")

            # 创建交易对象
            transaction = Transaction(
                sender=sender,
                receiver=receiver,
                amount=amount,
                transaction_type=transaction_type,
                data=extra_data
            )

            # 提交到区块链
            success = self.blockchain.add_transaction(transaction)

            if success:
                print("✅ 交易创建成功！")
                print(f"交易ID: {transaction.transaction_id}")
                print(f"交易哈希: {transaction.transaction_id[:20]}...")
                print(f"时间戳: {transaction.timestamp}")

                # 显示交易池状态
                pending_count = len(self.blockchain.pending_transactions)
                print(f"当前待处理交易: {pending_count} 笔")

                if pending_count >= 3:
                    print("💡 提示：待处理交易较多，建议进行挖矿确认")

                # 如果数据库连接，显示数据库状态
                if self.database_connected:
                    print("\n📊 数据库状态:")
                    tx_info = db.get_transaction_by_hash(transaction.transaction_id)
                    if tx_info:
                        print(f"交易状态: {tx_info['status']}")
                        print(f"确认数: {tx_info.get('confirmations', 0)}")
            else:
                print("❌ 交易创建失败")

        except (ValueError, IndexError) as e:
            print(f"❌ 输入无效: {e}")
        except KeyboardInterrupt:
            print("\n操作已取消")
        except Exception as e:
            print(f"❌ 发生未知错误: {e}")
            import traceback
            traceback.print_exc()

    def mine_block(self):
        """挖矿"""
        print("\n" + "=" * 40)
        print("挖矿")
        print("=" * 40)

        # 检查是否有待处理交易
        if not self.blockchain.pending_transactions:
            print("⚠️  没有待处理交易，无需挖矿")
            return

        print(f"当前有 {len(self.blockchain.pending_transactions)} 笔待处理交易")
        print("交易列表:")
        for i, tx in enumerate(self.blockchain.pending_transactions, 1):
            print(f"  {i}. {tx.sender} -> {tx.receiver}: {tx.amount:.8f} ({tx.transaction_type})")

        print("\n选择矿工地址:")

        # 显示可用地址
        available_addresses = []

        # 从数据库获取用户地址
        if self.database_connected and self.current_user['id'] > 0:
            addresses_info = db.get_user_addresses(self.current_user['id'])
            if addresses_info:
                for addr_info in addresses_info:
                    available_addresses.append(addr_info['address'])

        # 添加钱包中的其他地址
        for addr in self.wallet.addresses:
            if addr not in available_addresses:
                available_addresses.append(addr)

        for i, address in enumerate(available_addresses, 1):
            print(f"{i}. {address}")

        try:
            choice = input("请选择矿工地址编号: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(available_addresses):
                    miner_address = available_addresses[idx]

                    print(f"\n开始挖矿...")
                    print(f"矿工地址: {miner_address}")
                    print(f"挖矿难度: {self.blockchain.difficulty}")
                    print(f"挖矿奖励: {self.blockchain.mining_reward}")

                    # 执行挖矿
                    success = self.blockchain.mine_pending_transactions(miner_address)

                    if success:
                        print("✅ 挖矿成功！")

                        # 显示新区块信息
                        latest_block = self.blockchain.get_latest_block()
                        if latest_block:
                            print(f"新区块: #{latest_block.index}")
                            print(f"区块哈希: {latest_block.hash[:20]}...")
                            print(f"包含交易: {len(latest_block.transactions)} 笔")

                        # 显示矿工收益
                        miner_balance = self.blockchain.get_balance(miner_address)
                        print(f"矿工余额: {miner_balance:.8f}")
                    else:
                        print("❌ 挖矿失败")
                else:
                    print("❌ 编号无效")
            else:
                print("❌ 请输入数字")
        except ValueError:
            print("❌ 输入无效")
        except Exception as e:
            print(f"❌ 挖矿过程中出错: {e}")

    def validate_blockchain(self):
        """验证区块链"""
        print("\n正在验证区块链完整性...")

        if self.blockchain.is_chain_valid():
            print("✅ 区块链验证成功！")

            # 显示详细信息
            print(f"区块数量: {len(self.blockchain.chain)}")

            # 验证每个区块
            for block in self.blockchain.chain:
                print(f"  区块 #{block.index}: 哈希 {block.hash[:10]}... ✓")

            # 如果数据库连接，验证数据库一致性
            if self.database_connected:
                print("\n验证数据库一致性...")
                db_blocks = len(db.get_all_blocks()) if hasattr(db, 'get_all_blocks') else 0
                print(f"本地区块数: {len(self.blockchain.chain)}")
                print(f"数据库区块数: {db_blocks}")

                if len(self.blockchain.chain) == db_blocks:
                    print("✅ 本地与数据库区块数一致")
                else:
                    print("⚠️  本地与数据库区块数不一致")
        else:
            print("❌ 区块链验证失败！")
            print("可能的原因:")
            print("1. 区块链数据被篡改")
            print("2. 工作量证明无效")
            print("3. 区块哈希链断裂")

    def system_info(self):
        """显示系统信息"""
        print("\n" + "=" * 60)
        print("系统信息")
        print("=" * 60)

        print(f"📊 区块链信息:")
        print(f"  区块链长度: {len(self.blockchain.chain)}")
        print(f"  待处理交易: {len(self.blockchain.pending_transactions)}")
        print(f"  挖矿难度: {self.blockchain.difficulty}")
        print(f"  挖矿奖励: {self.blockchain.mining_reward}")
        print(f"  交易手续费: {self.blockchain.transaction_fee}")

        # 计算总流通量
        total_supply = 0
        addresses = set()

        # 统计所有地址的余额
        if self.database_connected:
            stats = db.get_system_stats()
            print(f"\n💾 数据库信息:")
            print(f"  总交易数: {stats.get('total_transactions', 0)}")
            print(f"  已确认交易: {stats.get('confirmed_transactions', 0)}")
            print(f"  活跃地址: {stats.get('active_addresses', 0)}")
            print(f"  总余额: {stats.get('total_balance', 0):.2f} BPC")
            print(f"  最新区块: #{stats.get('latest_block', 0)}")

        # 显示钱包信息
        print(f"\n👛 钱包信息:")
        print(f"  钱包名称: {self.wallet.name}")
        print(f"  地址数量: {len(self.wallet.addresses)}")

        # 显示合约信息
        if hasattr(self.blockchain, 'contract_manager'):
            contracts = self.blockchain.contract_manager.contracts
            if contracts:
                print(f"\n📜 智能合约:")
                print(f"  合约数量: {len(contracts)}")
                for i, (address, contract) in enumerate(list(contracts.items())[:3], 1):
                    print(f"  {i}. {address[:20]}... (余额: {contract.balance:.2f})")

        print("=" * 60)

    def view_stake_ranking(self):
        """查看质押排名"""
        print("\n" + "=" * 60)
        print("质押排名")
        print("=" * 60)

        # 从区块链收集质押数据
        stake_amounts = {}

        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.transaction_type == "stake":
                    address = tx.sender
                    amount = tx.amount

                    if address in stake_amounts:
                        stake_amounts[address] += amount
                    else:
                        stake_amounts[address] = amount

        if not stake_amounts:
            print("暂无质押记录")
            print("您可以通过创建'质押交易'来质押代币")
            return

        # 排序并显示
        sorted_stakes = sorted(stake_amounts.items(), key=lambda x: x[1], reverse=True)

        print(f"{'排名':<5} {'地址':<25} {'质押金额':<15} {'占比':<10}")
        print("-" * 60)

        total_stake = sum(stake_amounts.values())

        for i, (address, amount) in enumerate(sorted_stakes, 1):
            percentage = (amount / total_stake * 100) if total_stake > 0 else 0

            # 获取地址昵称（如果有）
            nickname = address
            if self.database_connected:
                address_info = db.get_address_info(address)
                if address_info and address_info['nickname']:
                    nickname = f"{address_info['nickname']} ({address[:10]}...)"
                else:
                    nickname = f"{address[:10]}..."

            print(f"{i:<5} {nickname:<25} {amount:<15.2f} {percentage:<10.1f}%")

            if i >= 10:  # 只显示前10名
                break

        print("-" * 60)
        print(f"总质押量: {total_stake:.2f}")
        print(f"质押地址数: {len(stake_amounts)}")
        print("=" * 60)

    def view_vote_results(self):
        """查看投票结果"""
        print("\n" + "=" * 60)
        print("投票结果")
        print("=" * 60)

        # 收集投票数据
        votes = {}
        total_votes = 0

        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.transaction_type == "vote":
                    # 从data中提取候选人
                    data = tx.data
                    if "投票给:" in data:
                        candidate = data.split("投票给:")[1].strip()
                        amount = tx.amount

                        if candidate in votes:
                            votes[candidate] += amount
                        else:
                            votes[candidate] = amount

                        total_votes += amount

        if not votes:
            print("暂无投票记录")
            print("您可以通过创建'投票交易'来参与治理")
            return

        # 排序并显示
        sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)

        print(f"{'候选人':<20} {'票数':<15} {'占比':<10} {'进度条':<20}")
        print("-" * 60)

        max_votes = max(votes.values()) if votes else 1

        for candidate, vote_count in sorted_votes:
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            bar_length = int((vote_count / max_votes) * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)

            print(f"{candidate:<20} {vote_count:<15.2f} {percentage:<10.1f}% [{bar}]")

        print("-" * 60)
        print(f"总投票数: {total_votes}")
        print(f"候选人数量: {len(votes)}")

        # 显示领先者
        if sorted_votes:
            leader, leader_votes = sorted_votes[0]
            leader_percentage = (leader_votes / total_votes * 100) if total_votes > 0 else 0
            print(f"当前领先: {leader} ({leader_percentage:.1f}%)")

        print("=" * 60)

    def database_menu(self):
        """数据库功能菜单"""
        if not self.database_connected:
            print("❌ 数据库未连接")
            return

        while True:
            print("\n" + "=" * 60)
            print("数据库管理")
            print("=" * 60)
            print("1. 查看系统统计")
            print("2. 查看富豪榜")
            print("3. 查看交易历史")
            print("4. 搜索交易")
            print("5. 数据库健康检查")
            print("6. 备份数据库")
            print("7. 导出数据")
            print("8. 返回主菜单")
            print("=" * 60)

            choice = input("请选择操作 (1-8): ").strip()

            if choice == '1':
                self.show_database_stats()
            elif choice == '2':
                self.show_rich_list()
            elif choice == '3':
                self.show_transaction_history()
            elif choice == '4':
                self.search_transaction()
            elif choice == '5':
                db.check_database_health()
            elif choice == '6':
                self.backup_database()
            elif choice == '7':
                self.export_data()
            elif choice == '8':
                break
            else:
                print("无效选择")

    def show_database_stats(self):
        """显示数据库统计"""
        stats = db.get_system_stats()

        print("\n" + "=" * 60)
        print("数据库系统统计")
        print("=" * 60)

        print(f"👥 用户统计:")
        print(f"  活跃用户: {stats.get('active_users', 0)}")
        print(f"  今日活跃: {stats.get('active_addresses_today', 0)}")

        print(f"\n💰 经济统计:")
        print(f"  总余额: {stats.get('total_balance', 0):.2f} BPC")
        print(f"  活跃地址: {stats.get('active_addresses', 0)}")

        print(f"\n⛓️  区块链统计:")
        print(f"  区块数量: {stats.get('block_count', 0)}")
        print(f"  最新区块: #{stats.get('latest_block', 0)}")
        print(f"  最新哈希: {stats.get('latest_block_hash', '无')}")

        print(f"\n📊 交易统计:")
        print(f"  总交易数: {stats.get('total_transactions', 0)}")
        print(f"  已确认交易: {stats.get('confirmed_transactions', 0)}")

        print("=" * 60)

    def show_rich_list(self):
        """显示富豪榜"""
        limit = input("显示前多少名？(默认10): ").strip()
        limit = int(limit) if limit.isdigit() else 10

        rich_list = db.get_rich_list(limit=limit)

        print(f"\n" + "=" * 80)
        print(f"🏆 富豪榜 (前{limit}名)")
        print("=" * 80)
        print(f"{'排名':<5} {'地址/昵称':<30} {'余额(BPC)':<15} {'所有者':<15} {'占比':<10}")
        print("-" * 80)

        total_balance = sum(item['balance'] for item in rich_list)

        for i, rich in enumerate(rich_list, 1):
            balance = rich['balance']
            percentage = (balance / total_balance * 100) if total_balance > 0 else 0
            nickname = rich['nickname'] if rich['nickname'] else rich['address'][:10] + "..."
            owner = rich.get('owner_name', '未知')

            print(f"{i:<5} {nickname:<30} {balance:<15.2f} {owner:<15} {percentage:<10.1f}%")

        print("-" * 80)
        print(f"总计: {total_balance:.2f} BPC")
        print("=" * 80)

    def show_transaction_history(self):
        """显示交易历史"""
        address = input("请输入要查询的地址 (留空查看所有): ").strip()
        limit = input("显示多少条记录？(默认20): ").strip()
        limit = int(limit) if limit.isdigit() else 20

        if address:
            transactions = db.get_transaction_history(address, limit=limit)
            print(f"\n📜 {address} 的交易历史 (最近{len(transactions)}条):")
        else:
            # 这里需要添加一个获取所有交易的方法
            print("获取所有交易...")
            # 简化实现：获取最新交易
            transactions = []
            print("获取所有交易功能待实现")
            return

        if not transactions:
            print("暂无交易记录")
            return

        print(f"\n" + "=" * 100)
        print(f"{'时间':<20} {'方向':<8} {'对方地址':<35} {'金额':<12} {'状态':<10} {'交易哈希':<20}")
        print("-" * 100)

        for tx in transactions:
            time_str = tx.get('time_str', '未知')
            direction = tx.get('direction', '未知')
            counterparty = tx.get('counterparty', '未知')
            if len(counterparty) > 30:
                counterparty = counterparty[:27] + "..."
            amount = f"{tx.get('amount', 0):.8f}"
            status = tx.get('status', '未知')
            tx_hash = tx.get('transaction_hash', '未知')
            if len(tx_hash) > 20:
                tx_hash = tx_hash[:17] + "..."

            print(f"{time_str:<20} {direction:<8} {counterparty:<35} {amount:<12} {status:<10} {tx_hash:<20}")

        print("=" * 100)

    def search_transaction(self):
        """搜索交易"""
        tx_hash = input("请输入交易哈希: ").strip()

        if not tx_hash:
            print("交易哈希不能为空")
            return

        tx_info = db.get_transaction_by_hash(tx_hash)

        if not tx_info:
            print(f"未找到交易 {tx_hash}")
            return

        print(f"\n" + "=" * 60)
        print("交易详情")
        print("=" * 60)

        print(f"交易哈希: {tx_info.get('transaction_hash')}")
        print(f"发送方: {tx_info.get('from_address')}")
        print(f"接收方: {tx_info.get('to_address')}")
        print(f"金额: {tx_info.get('amount'):.8f} BPC")
        print(f"手续费: {tx_info.get('fee', 0):.8f} BPC")
        print(f"类型: {tx_info.get('transaction_type', 'transfer')}")
        print(f"状态: {tx_info.get('status')}")
        print(f"区块号: {tx_info.get('block_number', '未确认')}")
        print(f"确认数: {tx_info.get('confirmations', 0)}")
        print(f"时间: {tx_info.get('time_str', tx_info.get('timestamp'))}")
        print(f"创建时间: {tx_info.get('created_at')}")

        if tx_info.get('data'):
            print(f"附加数据: {tx_info.get('data')}")
        if tx_info.get('memo'):
            print(f"备注: {tx_info.get('memo')}")

        print("=" * 60)

    def backup_database(self):
        """备份数据库"""
        confirm = input("确定要备份数据库吗？这可能需要一些时间。(y/N): ").strip().lower()

        if confirm == 'y':
            backup_dir = input("备份目录 (默认: backups): ").strip() or "backups"
            print(f"正在备份数据库到 {backup_dir}...")
            db.backup_database(backup_dir)
        else:
            print("备份已取消")

    def export_data(self):
        """导出数据"""
        export_dir = input("导出目录 (默认: exports): ").strip() or "exports"
        print(f"正在导出数据到 {export_dir}...")
        db.export_data(export_dir)

    def advanced_menu(self):
        """高级功能菜单"""
        while True:
            print("\n" + "=" * 60)
            print("高级功能")
            print("=" * 60)
            print("1. P2P网络功能")
            print("2. 智能合约功能")
            print("3. 安全功能")
            print("4. 系统演示")
            print("5. 返回主菜单")
            print("=" * 60)

            choice = input("请选择操作 (1-5): ").strip()

            if choice == '1':
                self.network_menu()
            elif choice == '2':
                self.smart_contract_menu()
            elif choice == '3':
                self.security_menu()
            elif choice == '4':
                self.run_demo()
            elif choice == '5':
                break
            else:
                print("无效选择")

    # 以下方法保持原有实现，但可以添加数据库集成
    def network_menu(self):
        """网络功能菜单（原有实现）"""
        print("\n网络功能（需要启动P2P节点）")
        # ... 原有代码 ...

    def smart_contract_menu(self):
        """智能合约菜单（原有实现）"""
        print("\n智能合约功能")
        # ... 原有代码 ...

    def security_menu(self):
        """安全功能菜单（原有实现）"""
        print("\n安全功能")
        # ... 原有代码 ...

    def run_demo(self):
        """运行系统演示（原有实现）"""
        print("\n运行系统演示...")
        # ... 原有代码 ...

    def run(self):
        """运行主程序"""
        print("BuptCoin 系统启动完成！")

        while True:
            self.print_menu()

            try:
                choice = input("\n请选择操作: ").strip()

                if choice == '1':
                    self.view_blockchain()
                elif choice == '2':
                    self.view_all_balances()
                elif choice == '3':
                    self.check_balance()
                elif choice == '4':
                    self.create_transaction()
                elif choice == '5':
                    self.mine_block()
                elif choice == '6':
                    self.validate_blockchain()
                elif choice == '7':
                    self.view_stake_ranking()
                elif choice == '8':
                    self.view_vote_results()
                elif choice == '9':
                    self.system_info()
                elif choice == '10':
                    self.advanced_menu()
                elif choice == '11' and self.database_connected:
                    self.database_menu()
                elif choice == '0':
                    print("\n感谢使用 BuptCoin！再见！")

                    # 关闭数据库连接
                    if self.database_connected and hasattr(db, 'close'):
                        db.close()

                    break
                else:
                    if choice == '11' and not self.database_connected:
                        print("❌ 数据库未连接，无法使用此功能")
                    else:
                        print("❌ 请选择有效的选项")

            except KeyboardInterrupt:
                print("\n\n程序被中断")
                confirm = input("确定要退出吗？(y/N): ").strip().lower()
                if confirm == 'y':
                    if self.database_connected and hasattr(db, 'close'):
                        db.close()
                    break
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                import traceback
                traceback.print_exc()


# 以下函数保持原有实现，但可以添加数据库检查
def run_cli_interface():
    """运行命令行界面"""
    print("=" * 60)
    print("启动命令行界面...")
    print("=" * 60)

    try:
        cli = SimpleCoinCLI()
        cli.run()
    except Exception as e:
        print(f"命令行界面启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_gui_interface():
    """运行图形界面"""
    print("=" * 60)
    print("启动图形界面...")
    print("=" * 60)

    try:
        # 导入 PyQt5
        from PyQt5.QtWidgets import QApplication

        print("PyQt5 导入成功，正在启动图形界面...")

        # 【关键修改】改为导入 gui_enhanced 模块
        from gui_enhanced import BlockchainGUIEnhanced

        app = QApplication(sys.argv)
        gui = BlockchainGUIEnhanced()
        gui.show()

        print("图形界面启动成功！")
        print("提示：关闭窗口退出程序")

        sys.exit(app.exec_())

    except ImportError as e:
        print(f"错误：无法导入所需模块 - {e}")
        print("\n请先安装 PyQt5:")
        print("pip install PyQt5")
        print("\n现在将使用命令行界面...")
        run_cli_interface()

    except Exception as e:
        print(f"图形界面启动失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n现在将使用命令行界面...")
        run_cli_interface()


def choose_interface():
    """让用户选择界面"""
    print("\n请选择界面模式:")
    print("1. 图形界面 (GUI) - 可视化操作，推荐使用")
    print("2. 命令行界面 (CLI) - 文本交互，适合调试")
    print("3. 数据库管理工具")
    print("4. 退出程序")

    try:
        choice = input("\n请选择 (1-4): ").strip()

        if choice == '1':
            run_gui_interface()
        elif choice == '2':
            run_cli_interface()
        elif choice == '3':
            run_database_admin()
        elif choice == '4':
            print("程序退出")
            sys.exit(0)
        else:
            print("无效选择，默认使用图形界面")
            run_gui_interface()

    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)


def run_database_admin():
    """运行数据库管理工具"""
    print("=" * 60)
    print("BuptCoin 数据库管理工具")
    print("=" * 60)

    try:
        from database import db, run_database_admin as run_admin

        if db and db.is_connected:
            run_admin()
        else:
            print("❌ 数据库未连接")
            print("请先运行 init_database.py 初始化数据库")

    except ImportError:
        print("❌ 数据库模块不可用")
    except Exception as e:
        print(f"❌ 运行数据库管理工具失败: {e}")


def show_help():
    """显示帮助信息"""
    print("\nBuptCoin 使用说明:")
    print("=" * 50)
    print("命令行选项:")
    print("  python main.py               # 交互式选择界面")
    print("  python main.py --cli         # 强制使用命令行界面")
    print("  python main.py --gui         # 强制使用图形界面")
    print("  python main.py --help        # 显示帮助信息")
    print("\n新增功能:")
    print("  - 数据库持久化存储")
    print("  - 用户注册登录系统")
    print("  - 完整的交易历史记录")
    print("  - 数据备份和导出功能")
    print("\n快捷键:")
    print("  命令行界面中按 Ctrl+C 可退出程序")
    print("  图形界面中关闭窗口即可退出")
    print("=" * 50)


def main():
    """主函数，根据参数选择界面"""
    print("=" * 60)
    print("欢迎使用 BuptCoin 数字货币系统")
    print("=" * 60)
    print("版本: 3.0 (数据库集成版)")
    print("作者: 北邮区块链项目")
    print("=" * 60)

    # 检查数据库配置文件
    db_config_file = "db_config.json"
    if not os.path.exists(db_config_file):
        print("\n⚠️  未找到数据库配置文件")
        print("首次使用请先运行数据库初始化工具")
        print("=" * 40)
        print("选择操作:")
        print("1. 运行数据库初始化工具")
        print("2. 以内存模式运行（数据不会保存）")
        print("3. 退出")
        print("=" * 40)

        choice = input("请选择 (1-3): ").strip()

        if choice == '1':
            try:
                import subprocess
                print("正在启动数据库初始化工具...")
                subprocess.run([sys.executable, "init_database.py"])
                # 初始化后继续启动
                print("\n数据库初始化完成，正在启动系统...")
            except Exception as e:
                print(f"运行初始化工具失败: {e}")
                print("请手动运行: python init_database.py")
                sys.exit(1)
        elif choice == '2':
            print("以内存模式运行...")
            # 继续执行
        elif choice == '3':
            print("程序退出")
            sys.exit(0)
        else:
            print("无效选择，以内存模式运行")

    # 检查命令行参数
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ['--cli', '-c', '/c', 'cli']:
            # 强制使用命令行界面
            run_cli_interface()
        elif arg in ['--gui', '-g', '/g', 'gui']:
            # 强制使用图形界面
            run_gui_interface()
        elif arg in ['--help', '-h', '/h', '/?', 'help']:
            # 显示帮助信息
            show_help()
            sys.exit(0)
        elif arg in ['--init', 'init', '--setup']:
            # 初始化数据库
            print("运行数据库初始化...")
            try:
                import subprocess
                subprocess.run([sys.executable, "init_database.py"])
            except Exception as e:
                print(f"运行初始化失败: {e}")
                print("请确保 init_database.py 文件存在")
            sys.exit(0)
        elif arg in ['--test', 'test']:
            # 测试模式
            print("测试模式...")
            test_database_connection()
            sys.exit(0)
        else:
            print(f"未知参数: {arg}")
            show_help()
            sys.exit(1)
    else:
        # 没有参数，让用户选择
        choose_interface()


if __name__ == "__main__":
    main()
