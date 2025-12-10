# gui.py - 修正版
import sys
import threading
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor
import os
import sys

# 添加当前目录到 Python 路径，确保可以导入本地模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blockchain import Blockchain, Transaction
from wallet import Wallet


class MiningThread(QObject):
    """挖矿线程类"""
    mining_finished = pyqtSignal(bool, str)
    mining_progress = pyqtSignal(str)

    def __init__(self, blockchain, miner_address):
        super().__init__()
        self.blockchain = blockchain
        self.miner_address = miner_address
        self._is_running = True

    def run(self):
        """执行挖矿"""
        try:
            self.mining_progress.emit("开始挖矿...")
            time.sleep(0.5)  # 模拟挖矿延迟

            # 执行挖矿
            success = self.blockchain.mine_pending_transactions(self.miner_address)

            if success:
                self.mining_finished.emit(True, f"挖矿成功！矿工 {self.miner_address} 获得奖励")
            else:
                self.mining_finished.emit(False, "挖矿失败：没有待处理交易")

        except Exception as e:
            self.mining_finished.emit(False, f"挖矿出错: {str(e)}")


# 在 BlockchainGUI 类中添加以下方法
class BlockchainGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # 显示启动界面
        self.show_startup_dialog()

        # 设置样式
        self.setup_styles()

        # 只有在用户登录后才初始化UI
        if hasattr(self, 'blockchain'):
            self.init_ui()
            self.update_display()
            self.debug_info()
        else:
            # 如果没有区块链对象，关闭窗口
            self.close()

    def show_startup_dialog(self):
        """显示启动对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout

        self.startup_dialog = QDialog()
        self.startup_dialog.setWindowTitle("BuptCoin 启动")
        self.startup_dialog.setFixedSize(400, 300)

        layout = QVBoxLayout(self.startup_dialog)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("欢迎使用 BuptCoin")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Microsoft YaHei", 14, QFont.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 数据库状态
        db_status_label = QLabel("正在检查数据库连接...")
        db_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(db_status_label)

        # 尝试连接数据库
        self.database_connected = False
        self.current_user = None

        try:
            from database import db
            if hasattr(db, 'is_connected') and db.is_connected:
                self.database_connected = True
                self.db = db
                db_status_label.setText("✅ 数据库连接成功")
                db_status_label.setStyleSheet("color: green;")

                # 显示登录界面
                self.show_login_interface(layout)
            else:
                db_status_label.setText("❌ 数据库连接失败，使用内存模式")
                db_status_label.setStyleSheet("color: red;")
                self.show_memory_mode_option(layout)

        except ImportError as e:
            db_status_label.setText("❌ 数据库模块加载失败")
            db_status_label.setStyleSheet("color: red;")
            self.show_memory_mode_option(layout)
        except Exception as e:
            db_status_label.setText(f"❌ 数据库连接错误: {str(e)[:50]}")
            db_status_label.setStyleSheet("color: orange;")
            self.show_memory_mode_option(layout)

        self.startup_dialog.exec_()

    def show_login_interface(self, layout):
        """显示登录界面"""
        # 用户名
        username_label = QLabel("用户名:")
        layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setText("test_user")  # 默认测试用户
        layout.addWidget(self.username_input)

        # 密码
        password_label = QLabel("密码:")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setText("test123")  # 默认测试密码
        layout.addWidget(self.password_input)

        # 按钮
        btn_layout = QHBoxLayout()

        login_btn = QPushButton("登录")
        login_btn.clicked.connect(self.handle_startup_login)
        login_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        btn_layout.addWidget(login_btn)

        register_btn = QPushButton("注册")
        register_btn.clicked.connect(self.handle_startup_register)
        register_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        btn_layout.addWidget(register_btn)

        guest_btn = QPushButton("访客模式")
        guest_btn.clicked.connect(self.handle_startup_guest)
        guest_btn.setStyleSheet("background-color: #9E9E9E; color: white; padding: 8px;")
        btn_layout.addWidget(guest_btn)

        layout.addLayout(btn_layout)

    def show_memory_mode_option(self, layout):
        """显示内存模式选项"""
        info_label = QLabel("数据库不可用，将以内存模式运行。\n数据不会保存到数据库。")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        memory_btn = QPushButton("继续使用内存模式")
        memory_btn.clicked.connect(self.handle_memory_mode)
        memory_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 10px; font-size: 14px;")
        layout.addWidget(memory_btn)

        retry_btn = QPushButton("重试数据库连接")
        retry_btn.clicked.connect(self.handle_retry_database)
        retry_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-size: 14px;")
        layout.addWidget(retry_btn)

    def handle_startup_login(self):
        """处理启动界面的登录"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self.startup_dialog, "输入错误", "用户名和密码不能为空")
            return

        try:
            user = self.db.authenticate_user(username, password)
            if user:
                self.current_user = user
                print(f"✅ 登录成功！欢迎 {username}")

                # 初始化系统
                self.init_system_after_login()
                self.startup_dialog.accept()
            else:
                QMessageBox.warning(self.startup_dialog, "登录失败", "用户名或密码错误")
        except Exception as e:
            QMessageBox.critical(self.startup_dialog, "登录错误", f"登录时出错: {str(e)}")

    def handle_startup_register(self):
        """处理启动界面的注册"""
        from PyQt5.QtWidgets import QInputDialog

        username, ok = QInputDialog.getText(self.startup_dialog, "用户注册", "请输入用户名:")
        if not ok or not username:
            return

        # 检查用户名是否已存在
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            QMessageBox.warning(self.startup_dialog, "注册失败", "用户名已存在")
            cursor.close()
            return
        cursor.close()

        password, ok = QInputDialog.getText(self.startup_dialog, "用户注册", "请输入密码:", QLineEdit.Password)
        if not ok or not password:
            return

        confirm_password, ok = QInputDialog.getText(self.startup_dialog, "用户注册", "请确认密码:", QLineEdit.Password)
        if not ok or confirm_password != password:
            QMessageBox.warning(self.startup_dialog, "注册失败", "两次输入的密码不一致")
            return

        email, ok = QInputDialog.getText(self.startup_dialog, "用户注册", "邮箱 (可选):")
        if not ok:
            email = ""

        try:
            user_id = self.db.create_user(username, password, email)
            if user_id:
                QMessageBox.information(self.startup_dialog, "注册成功",
                                        f"用户 {username} 注册成功！\n\n系统将自动为您创建钱包地址。")

                # 自动创建钱包
                address_info = self.db.create_wallet_address(user_id, f"{username}的默认钱包")
                if address_info:
                    # 分配初始余额
                    self.db.update_address_balance(address_info['address'], 100.0)

                    QMessageBox.information(self.startup_dialog, "钱包创建成功",
                                            f"钱包地址: {address_info['address']}\n"
                                            f"初始余额: 100.0 BPC\n\n"
                                            f"请使用新账号登录。")
        except Exception as e:
            QMessageBox.critical(self.startup_dialog, "注册失败", f"注册时出错: {str(e)}")

    def handle_startup_guest(self):
        """访客模式"""
        self.current_user = {
            'id': 0,
            'username': 'guest',
            'email': None
        }
        print("以访客身份继续")

        # 初始化系统
        self.init_system_after_login()
        self.startup_dialog.accept()

    def handle_memory_mode(self):
        """内存模式"""
        self.current_user = {
            'id': 0,
            'username': 'memory_mode',
            'email': None
        }
        self.database_connected = False
        self.db = None

        # 初始化系统
        self.init_system_after_login()
        self.startup_dialog.accept()

    def handle_retry_database(self):
        """重试数据库连接"""
        try:
            # 重新创建数据库管理器
            from database import create_db_manager
            new_db = create_db_manager()
            if new_db and new_db.is_connected:
                self.db = new_db
                self.database_connected = True
                QMessageBox.information(self.startup_dialog, "连接成功", "数据库连接成功！")
                self.startup_dialog.accept()
                # 重新显示登录界面
                self.show_startup_dialog()
            else:
                QMessageBox.warning(self.startup_dialog, "连接失败", "数据库连接失败")
        except Exception as e:
            QMessageBox.critical(self.startup_dialog, "连接错误", f"连接数据库时出错: {str(e)}")

    def init_system_after_login(self):
        """登录后初始化系统"""
        print("\n正在初始化系统...")

        try:
            # 初始化区块链
            self.blockchain = Blockchain(difficulty=2)
            print(f"✅ 区块链初始化完成，区块数: {len(self.blockchain.chain)}")

            # 初始化钱包
            if self.database_connected and self.current_user and self.current_user['id'] > 0:
                self.init_wallet_from_database()
            else:
                self.init_default_wallet()

            print("✅ 系统初始化完成")

        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            QMessageBox.critical(None, "初始化错误", f"系统初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def init_wallet_from_database(self):
        """从数据库初始化钱包"""
        try:
            # 从数据库加载用户的地址
            addresses = self.db.get_user_addresses(self.current_user['id'])

            # 创建钱包对象
            self.wallet = Wallet(f"User_{self.current_user['id']}_Wallet")

            # 清空默认地址
            self.wallet.addresses = []

            if addresses:
                for addr_info in addresses:
                    address = addr_info['address']
                    self.wallet.addresses.append(address)
                    # 显示地址信息
                    print(
                        f"加载地址: {addr_info['nickname']} ({address[:10]}...) - 余额: {addr_info['balance']:.8f} BPC")

            # 添加创世地址（如果不存在）
            if 'genesis' not in self.wallet.addresses:
                self.wallet.addresses.insert(0, 'genesis')

            print(f"✅ 钱包加载完成，共 {len(self.wallet.addresses)} 个地址")

        except Exception as e:
            print(f"❌ 从数据库加载钱包失败: {e}")
            self.init_default_wallet()

    def init_default_wallet(self):
        """初始化默认钱包"""
        self.wallet = Wallet("BuptCoin Wallet")
        print("✅ 使用默认钱包")

        # 初始化区块链和钱包
        try:
            self.blockchain = Blockchain(difficulty=2)
            self.wallet = Wallet("GUI Wallet")

            # 确保至少有一个地址有余额（创世区块奖励）
            if len(self.blockchain.chain) > 0:
                print("区块链初始化成功")
                print(f"创世区块地址余额: {self.blockchain.get_balance('genesis')}")
            else:
                print("警告：区块链没有区块")

        except Exception as e:
            print(f"初始化失败: {e}")
            # 创建空的区块链和钱包
            self.blockchain = Blockchain(difficulty=2)
            self.wallet = Wallet("GUI Wallet")

        # 设置挖矿线程
        self.mining_thread = None

        # 设置应用样式
        self.setup_styles()

        self.init_ui()
        self.update_display()

        # 打印调试信息
        self.debug_info()

    def debug_info(self):
        """打印调试信息"""
        print("\n=== 调试信息 ===")
        print(f"钱包地址数量: {len(self.wallet.addresses)}")
        for addr in self.wallet.addresses[:3]:  # 只显示前3个地址
            balance = self.blockchain.get_balance(addr)
            print(f"地址 {addr}: 余额 = {balance}")

        print(f"区块链长度: {len(self.blockchain.chain)}")
        print(f"待处理交易: {len(self.blockchain.pending_transactions)}")
        print("================\n")

    def setup_styles(self):
        """设置全局样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #3a7bd5;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #3a7bd5;
            }
            QLabel {
                font-size: 13px;
            }
            QLabel#titleLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
            }
            QLabel#statusLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
                border-radius: 4px;
                background-color: #e8f4fc;
            }
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
                background-color: #3a7bd5;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #2a6bc5;
            }
            QPushButton:pressed {
                background-color: #1a5bb5;
            }
            QPushButton#mineButton {
                background-color: #00b09b;
            }
            QPushButton#mineButton:hover {
                background-color: #009688;
            }
            QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
                font-size: 14px;
                padding: 6px;
                border: 1px solid #d1d9e6;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover, QLineEdit:hover {
                border: 1px solid #3a7bd5;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 2px solid #3a7bd5;
            }
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #d1d9e6;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            QTableWidget {
                font-size: 12px;
                border: 1px solid #d1d9e6;
                border-radius: 4px;
                background-color: white;
                gridline-color: #eaeaea;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #3a7bd5;
                color: white;
            }
            QHeaderView::section {
                background-color: #3a7bd5;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
            QTabWidget::pane {
                border: 1px solid #d1d9e6;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e8f4fc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3a7bd5;
                color: white;
            }
        """)

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('💰 BuptCoin - 区块链数字货币系统')
        self.setGeometry(100, 100, 1200, 800)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ========== 1. 顶部标题栏 ==========
        title_layout = QHBoxLayout()

        # 标题
        title_label = QLabel("BuptCoin 区块链系统")
        title_label.setObjectName("titleLabel")
        title_font = QFont("Microsoft YaHei", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 状态标签
        self.status_label = QLabel("🟢 系统就绪")
        self.status_label.setObjectName("statusLabel")
        status_font = QFont("Microsoft YaHei", 11)
        self.status_label.setFont(status_font)
        title_layout.addWidget(self.status_label)

        main_layout.addLayout(title_layout)

        # ========== 2. 快速信息栏 ==========
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        info_layout = QHBoxLayout(info_frame)

        # 余额显示
        self.balance_label = QLabel("💰 总余额: 0.0")
        balance_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        self.balance_label.setFont(balance_font)
        self.balance_label.setStyleSheet("color: #27ae60;")
        info_layout.addWidget(self.balance_label)

        info_layout.addWidget(QLabel("|"))

        # 区块链信息
        self.chain_label = QLabel("⛓️ 区块链: 0 个区块")
        info_layout.addWidget(self.chain_label)

        info_layout.addWidget(QLabel("|"))

        # 交易池信息
        self.pending_label = QLabel("📝 待处理交易: 0 笔")
        info_layout.addWidget(self.pending_label)

        info_layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.update_display)
        refresh_btn.setFixedWidth(100)
        info_layout.addWidget(refresh_btn)

        main_layout.addWidget(info_frame)

        # ========== 3. 主要功能区域（使用标签页） ==========
        tabs = QTabWidget()
        tabs.setFont(QFont("Microsoft YaHei", 11))
        main_layout.addWidget(tabs)

        # 标签页1：交易功能
        transaction_tab = QWidget()
        transaction_layout = QVBoxLayout(transaction_tab)
        transaction_layout.setSpacing(15)

        # 3.1 创建交易面板
        trans_group = QGroupBox("📤 创建新交易")
        trans_layout = QGridLayout()
        trans_layout.setSpacing(12)

        # 发送方
        trans_layout.addWidget(QLabel("发送方地址:"), 0, 0)
        self.sender_combo = QComboBox()
        self.sender_combo.setFixedHeight(35)
        trans_layout.addWidget(self.sender_combo, 0, 1, 1, 2)

        # 接收方
        trans_layout.addWidget(QLabel("接收方地址:"), 1, 0)
        self.receiver_edit = QLineEdit()
        self.receiver_edit.setPlaceholderText("输入接收方地址或从下拉框选择")
        self.receiver_edit.setFixedHeight(35)
        trans_layout.addWidget(self.receiver_edit, 1, 1, 1, 2)

        # 金额
        trans_layout.addWidget(QLabel("转账金额:"), 2, 0)
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0.01, 1000000)
        self.amount_spinbox.setDecimals(8)
        self.amount_spinbox.setValue(1.0)
        self.amount_spinbox.setPrefix("💰 ")
        self.amount_spinbox.setFixedHeight(35)
        trans_layout.addWidget(self.amount_spinbox, 2, 1, 1, 2)

        # 交易类型
        trans_layout.addWidget(QLabel("交易类型:"), 3, 0)
        self.tx_type_combo = QComboBox()
        self.tx_type_combo.addItems(["transfer", "stake", "vote", "contract"])
        self.tx_type_combo.setFixedHeight(35)
        trans_layout.addWidget(self.tx_type_combo, 3, 1, 1, 2)

        # 附加数据
        trans_layout.addWidget(QLabel("备注/数据:"), 4, 0)
        self.data_edit = QLineEdit()
        self.data_edit.setPlaceholderText("输入交易备注或附加数据")
        self.data_edit.setFixedHeight(35)
        trans_layout.addWidget(self.data_edit, 4, 1, 1, 2)

        # 发送按钮
        self.send_btn = QPushButton("🚀 发送交易")
        self.send_btn.clicked.connect(self.send_transaction)
        self.send_btn.setFixedHeight(45)
        trans_layout.addWidget(self.send_btn, 5, 0, 1, 3)

        trans_group.setLayout(trans_layout)
        transaction_layout.addWidget(trans_group)

        # 3.2 挖矿面板
        mine_group = QGroupBox("⛏️ 挖矿")
        mine_layout = QHBoxLayout()
        mine_layout.setSpacing(15)

        mine_layout.addWidget(QLabel("矿工地址:"))
        self.miner_combo = QComboBox()
        self.miner_combo.setFixedHeight(35)
        mine_layout.addWidget(self.miner_combo)

        self.mine_btn = QPushButton("开始挖矿")
        self.mine_btn.setObjectName("mineButton")
        self.mine_btn.setFixedHeight(40)
        self.mine_btn.setFixedWidth(150)
        self.mine_btn.clicked.connect(self.start_mining)
        mine_layout.addWidget(self.mine_btn)

        self.mining_status = QLabel("🟡 等待挖矿")
        mine_layout.addWidget(self.mining_status)
        mine_layout.addStretch()

        mine_group.setLayout(mine_layout)
        transaction_layout.addWidget(mine_group)

        # 3.3 交易历史表格
        history_group = QGroupBox("📊 交易历史")
        history_layout = QVBoxLayout()

        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(7)
        self.transaction_table.setHorizontalHeaderLabels(["时间戳", "类型", "发送方", "→", "接收方", "金额", "状态"])
        self.transaction_table.horizontalHeader().setStretchLastSection(True)
        self.transaction_table.setAlternatingRowColors(True)
        self.transaction_table.setSelectionBehavior(QTableWidget.SelectRows)

        # 设置列宽
        self.transaction_table.setColumnWidth(0, 120)  # 时间戳
        self.transaction_table.setColumnWidth(1, 80)  # 类型
        self.transaction_table.setColumnWidth(2, 120)  # 发送方
        self.transaction_table.setColumnWidth(3, 30)  # 箭头
        self.transaction_table.setColumnWidth(4, 120)  # 接收方
        self.transaction_table.setColumnWidth(5, 100)  # 金额
        self.transaction_table.setColumnWidth(6, 80)  # 状态

        history_layout.addWidget(self.transaction_table)

        # 清空交易按钮
        clear_btn = QPushButton("🗑️ 清空交易历史")
        clear_btn.clicked.connect(lambda: self.transaction_table.setRowCount(0))
        clear_btn.setFixedHeight(35)
        history_layout.addWidget(clear_btn)

        history_group.setLayout(history_layout)
        transaction_layout.addWidget(history_group)

        tabs.addTab(transaction_tab, "💸 交易与挖矿")

        # 标签页2：区块链浏览器
        blockchain_tab = QWidget()
        blockchain_layout = QVBoxLayout(blockchain_tab)

        # 区块信息显示
        block_group = QGroupBox("🔗 区块链详情")
        block_layout = QVBoxLayout()

        self.blockchain_text = QTextEdit()
        self.blockchain_text.setReadOnly(True)
        self.blockchain_text.setFont(QFont("Consolas", 10))
        block_layout.addWidget(self.blockchain_text)

        block_group.setLayout(block_layout)
        blockchain_layout.addWidget(block_group)

        # 操作按钮
        button_layout = QHBoxLayout()

        # 查看完整区块链按钮
        view_full_btn = QPushButton("📜 查看完整区块链")
        view_full_btn.clicked.connect(self.view_full_blockchain)
        view_full_btn.setFixedHeight(40)
        button_layout.addWidget(view_full_btn)

        button_layout.addStretch()

        # 验证按钮
        validate_btn = QPushButton("✅ 验证区块链")
        validate_btn.clicked.connect(self.validate_blockchain)
        validate_btn.setFixedHeight(40)
        button_layout.addWidget(validate_btn)

        blockchain_layout.addLayout(button_layout)

        tabs.addTab(blockchain_tab, "⛓️ 区块链浏览器")

        # 标签页3：地址余额
        balance_tab = QWidget()
        balance_layout = QVBoxLayout(balance_tab)

        balance_group = QGroupBox("👛 钱包地址余额")
        balance_main_layout = QVBoxLayout()

        # 创建余额表格
        self.balance_table = QTableWidget()
        self.balance_table.setColumnCount(4)
        self.balance_table.setHorizontalHeaderLabels(["序号", "地址", "余额 (BPC)", "状态"])
        self.balance_table.horizontalHeader().setStretchLastSection(True)
        self.balance_table.setAlternatingRowColors(True)
        self.balance_table.verticalHeader().setVisible(False)

        # 设置列宽
        self.balance_table.setColumnWidth(0, 60)  # 序号
        self.balance_table.setColumnWidth(1, 250)  # 地址
        self.balance_table.setColumnWidth(2, 120)  # 余额
        self.balance_table.setColumnWidth(3, 80)  # 状态

        balance_main_layout.addWidget(self.balance_table)

        # 总计行
        total_frame = QFrame()
        total_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        total_frame.setStyleSheet("background-color: #e8f4fc; border: 2px solid #3a7bd5;")
        total_layout = QHBoxLayout(total_frame)
        total_layout.setContentsMargins(20, 15, 20, 15)

        total_layout.addStretch()

        total_label = QLabel("💰 总计余额:")
        total_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        total_layout.addWidget(total_label)

        self.total_balance_label = QLabel("0.00")
        self.total_balance_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.total_balance_label.setStyleSheet("color: #e74c3c; padding: 0 10px;")
        total_layout.addWidget(self.total_balance_label)

        total_unit = QLabel("BPC")
        total_unit.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        total_unit.setStyleSheet("color: #e74c3c;")
        total_layout.addWidget(total_unit)

        balance_main_layout.addWidget(total_frame)
        balance_group.setLayout(balance_main_layout)
        balance_layout.addWidget(balance_group)

        # 刷新余额按钮
        refresh_balance_btn = QPushButton("🔄 刷新余额")
        refresh_balance_btn.clicked.connect(self.update_balances)
        refresh_balance_btn.setFixedHeight(35)
        balance_layout.addWidget(refresh_balance_btn)

        tabs.addTab(balance_tab, "💰 余额查询")

        # 标签页4：系统信息
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)

        info_group = QGroupBox("ℹ️ 系统信息")
        info_inner_layout = QVBoxLayout()

        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        self.system_info_text.setFont(QFont("Consolas", 10))
        info_inner_layout.addWidget(self.system_info_text)

        info_group.setLayout(info_inner_layout)
        info_layout.addWidget(info_group)

        tabs.addTab(info_tab, "ℹ️ 系统信息")

        # ========== 4. 底部状态栏 ==========
        self.statusBar().showMessage("欢迎使用 BuptCoin 区块链系统 | 就绪")

        # ========== 5. 菜单栏 ==========
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('📁 文件')

        new_wallet_action = QAction('🆕 新建钱包', self)
        new_wallet_action.triggered.connect(self.create_new_wallet)
        file_menu.addAction(new_wallet_action)

        file_menu.addSeparator()

        exit_action = QAction('❌ 退出', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tool_menu = menubar.addMenu('🛠️ 工具')

        test_action = QAction('🧪 测试交易', self)
        test_action.triggered.connect(self.test_transaction)
        tool_menu.addAction(test_action)

        debug_action = QAction('🐛 调试信息', self)
        debug_action.triggered.connect(self.debug_info)
        tool_menu.addAction(debug_action)

        # 帮助菜单
        help_menu = menubar.addMenu('❓ 帮助')
        about_action = QAction('ℹ️ 关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # ========== 6. 更新地址列表 ==========
        self.update_address_lists()

        # ========== 7. 定时器 ==========
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(3000)  # 每3秒刷新一次

    def update_address_lists(self):
        """更新地址下拉框"""
        self.sender_combo.clear()
        self.miner_combo.clear()

        # 添加创世地址
        all_addresses = ['genesis'] + self.wallet.addresses

        for address in all_addresses:
            self.sender_combo.addItem(address)
            self.miner_combo.addItem(address)

        # 添加一些常用地址到接收方建议
        self.receiver_edit.clear()

    def send_transaction(self):
        """发送交易"""
        sender = self.sender_combo.currentText()
        receiver = self.receiver_edit.text().strip()

        if not receiver:
            QMessageBox.warning(self, "输入错误", "请输入接收方地址！")
            return

        if sender == receiver:
            QMessageBox.warning(self, "输入错误", "发送方和接收方不能相同！")
            return

        amount = self.amount_spinbox.value()
        if amount <= 0:
            QMessageBox.warning(self, "输入错误", "金额必须大于0！")
            return

        tx_type = self.tx_type_combo.currentText()
        data = self.data_edit.text().strip()

        try:
            # 检查发送方余额
            sender_balance = self.blockchain.get_balance(sender)
            total_cost = amount + self.blockchain.transaction_fee

            if sender_balance < total_cost and sender != "0":  # 系统地址0不受限制
                QMessageBox.warning(self, "余额不足",
                                    f"余额不足！\n需要: {total_cost:.8f}\n当前余额: {sender_balance:.8f}")
                return

            # 创建交易
            transaction = Transaction(
                sender=sender,
                receiver=receiver,
                amount=amount,
                transaction_type=tx_type,
                data=data
            )

            if self.blockchain.add_transaction(transaction):
                self.status_label.setText("🟢 交易发送成功！")
                self.statusBar().showMessage(f"交易已发送: {sender} -> {receiver}: {amount:.8f}")

                # 清空输入框
                self.receiver_edit.clear()
                self.data_edit.clear()
                self.amount_spinbox.setValue(1.0)

                # 播放成功音效
                QApplication.beep()

                # 立即更新显示
                self.update_display()
            else:
                self.status_label.setText("🔴 交易发送失败")
                QMessageBox.critical(self, "交易失败", "交易发送失败，请检查余额！")

        except ValueError as e:
            QMessageBox.warning(self, "输入错误", f"请输入有效的金额！错误: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发送交易时出错: {str(e)}")

    def start_mining(self):
        """开始挖矿"""
        miner_address = self.miner_combo.currentText()

        if not self.blockchain.pending_transactions:
            QMessageBox.information(self, "提示", "没有待处理交易，无需挖矿")
            return

        self.mining_status.setText("⛏️ 挖矿中...")
        self.mine_btn.setEnabled(False)
        self.status_label.setText("🟡 正在挖矿...")

        # 在新线程中挖矿
        def mining_task():
            try:
                time.sleep(0.5)  # 模拟挖矿延迟

                success = self.blockchain.mine_pending_transactions(miner_address)

                # 使用 QTimer 在主线程中更新 UI
                QTimer.singleShot(0, lambda: self.on_mining_finished(success, miner_address))

            except Exception as e:
                QTimer.singleShot(0, lambda: self.on_mining_error(str(e)))

        thread = threading.Thread(target=mining_task, daemon=True)
        thread.start()

    def on_mining_finished(self, success, miner_address):
        """挖矿完成回调"""
        self.mine_btn.setEnabled(True)

        if success:
            self.mining_status.setText("✅ 挖矿完成！")
            self.status_label.setText("🟢 新区块已添加")
            self.statusBar().showMessage(f"挖矿成功！矿工 {miner_address} 获得奖励")

            # 显示挖矿奖励信息
            latest_block = self.blockchain.get_latest_block()
            if latest_block:
                QMessageBox.information(self, "挖矿成功",
                                        f"挖矿成功！\n新区块 #{latest_block.index} 已添加到区块链\n"
                                        f"矿工 {miner_address} 获得 {self.blockchain.mining_reward} BPC 奖励")
        else:
            self.mining_status.setText("⚠️ 挖矿失败")
            self.status_label.setText("🟡 没有待处理交易")

        # 更新显示
        self.update_display()

    def on_mining_error(self, error_msg):
        """挖矿错误回调"""
        self.mine_btn.setEnabled(True)
        self.mining_status.setText("❌ 挖矿错误")
        self.status_label.setText("🔴 挖矿出错")
        QMessageBox.critical(self, "挖矿错误", f"挖矿过程中出错: {error_msg}")

    def validate_blockchain(self):
        """验证区块链"""
        if self.blockchain.is_chain_valid():
            QMessageBox.information(self, "验证结果", "✅ 区块链验证通过！\n区块链完整性良好。")
            self.status_label.setText("🟢 区块链有效")
        else:
            QMessageBox.critical(self, "验证结果",
                                 "❌ 区块链验证失败！\n可能的原因：\n1. 区块链数据被篡改\n2. 工作量证明无效\n3. 区块哈希链断裂")
            self.status_label.setText("🔴 区块链无效")

    def update_display(self):
        """更新界面显示"""
        try:
            # 更新地址列表
            self.update_address_lists()

            # 更新余额
            self.update_balances()

            # 更新区块链信息
            self.chain_label.setText(f"⛓️ 区块链: {len(self.blockchain.chain)} 个区块")
            self.pending_label.setText(f"📝 待处理交易: {len(self.blockchain.pending_transactions)} 笔")

            # 更新交易历史表格
            self.update_transaction_table()

            # 更新区块链信息显示
            self.update_blockchain_text()

            # 更新系统信息
            self.update_system_info()

        except Exception as e:
            print(f"更新显示时出错: {e}")

    def update_balances(self):
        """更新余额显示"""
        total_balance = 0

        # 获取所有地址（包括创世地址）
        all_addresses = ['genesis'] + self.wallet.addresses

        # 更新余额表格
        self.balance_table.setRowCount(len(all_addresses))

        for i, address in enumerate(all_addresses):
            balance = self.blockchain.get_balance(address)
            total_balance += balance

            # 序号
            index_item = QTableWidgetItem(str(i + 1))
            index_item.setTextAlignment(Qt.AlignCenter)
            self.balance_table.setItem(i, 0, index_item)

            # 地址
            address_item = QTableWidgetItem(address)
            self.balance_table.setItem(i, 1, address_item)

            # 余额
            balance_item = QTableWidgetItem(f"{balance:.8f}")
            balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # 根据余额设置颜色
            if balance > 100:
                balance_item.setForeground(QColor('#27ae60'))  # 绿色
                status = "💰 富裕"
            elif balance > 0:
                balance_item.setForeground(QColor('#f39c12'))  # 橙色
                status = "💵 正常"
            else:
                balance_item.setForeground(QColor('#e74c3c'))  # 红色
                status = "💸 空"

            self.balance_table.setItem(i, 2, balance_item)

            # 状态
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.balance_table.setItem(i, 3, status_item)

        # 更新总余额
        self.total_balance_label.setText(f"{total_balance:.8f}")
        self.balance_label.setText(f"💰 总余额: {total_balance:.8f} BPC")

    def update_transaction_table(self):
        """更新交易表格"""
        transactions = []

        # 收集所有交易（包括区块中和待处理的）
        for block in self.blockchain.chain:
            for tx in block.transactions:
                transactions.append({
                    'time': tx.timestamp,
                    'type': tx.transaction_type,
                    'sender': tx.sender,
                    'receiver': tx.receiver,
                    'amount': tx.amount,
                    'status': '✅ 已确认',
                    'status_color': '#27ae60',
                    'block': block.index
                })

        # 添加待处理交易
        for tx in self.blockchain.pending_transactions:
            transactions.append({
                'time': tx.timestamp,
                'type': tx.transaction_type,
                'sender': tx.sender,
                'receiver': tx.receiver,
                'amount': tx.amount,
                'status': '⏳ 待处理',
                'status_color': '#f39c12',
                'block': None
            })

        # 按时间排序（最新的在前）
        transactions.sort(key=lambda x: x['time'], reverse=True)

        # 更新表格
        self.transaction_table.setRowCount(min(len(transactions), 50))  # 最多显示50条

        for i, tx in enumerate(transactions[:50]):
            # 时间戳（转换为可读格式）
            from datetime import datetime
            time_str = datetime.fromtimestamp(tx['time']).strftime("%Y-%m-%d %H:%M")
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.transaction_table.setItem(i, 0, time_item)

            # 类型
            type_item = QTableWidgetItem(tx['type'])
            type_item.setTextAlignment(Qt.AlignCenter)
            self.transaction_table.setItem(i, 1, type_item)

            # 发送方
            sender_item = QTableWidgetItem(tx['sender'][:20])
            self.transaction_table.setItem(i, 2, sender_item)

            # 箭头
            arrow_item = QTableWidgetItem("→")
            arrow_item.setTextAlignment(Qt.AlignCenter)
            arrow_item.setForeground(QColor('#3498db'))
            self.transaction_table.setItem(i, 3, arrow_item)

            # 接收方
            receiver_item = QTableWidgetItem(tx['receiver'][:20])
            self.transaction_table.setItem(i, 4, receiver_item)

            # 金额
            amount_item = QTableWidgetItem(f"{tx['amount']:.8f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if tx['amount'] > 0:
                amount_item.setForeground(QColor('#27ae60'))
            self.transaction_table.setItem(i, 5, amount_item)

            # 状态
            status_item = QTableWidgetItem(tx['status'])
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(tx['status_color']))
            self.transaction_table.setItem(i, 6, status_item)

    def update_blockchain_text(self):
        """更新区块链信息"""
        text = f"📊 区块链状态报告\n"
        text += f"{'=' * 60}\n"
        text += f"区块总数: {len(self.blockchain.chain)}\n"
        text += f"待处理交易: {len(self.blockchain.pending_transactions)}\n"
        text += f"挖矿难度: {self.blockchain.difficulty}\n"
        text += f"挖矿奖励: {self.blockchain.mining_reward} BPC\n"
        text += f"交易手续费: {self.blockchain.transaction_fee} BPC\n"
        text += f"{'=' * 60}\n\n"

        # 显示最近3个区块
        recent_blocks = self.blockchain.chain[-3:] if len(self.blockchain.chain) > 3 else self.blockchain.chain

        for block in recent_blocks:
            text += f"🔷 区块 #{block.index}\n"
            text += f"   哈希: {block.hash[:20]}...\n"
            text += f"   时间: {datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n"
            text += f"   交易数: {len(block.transactions)}\n"
            text += f"   前驱哈希: {block.previous_hash[:20]}...\n"
            text += f"   工作量证明: {block.nonce}\n"

            # 显示区块中的交易
            if len(block.transactions) > 0:
                text += f"   交易列表:\n"
                for tx in block.transactions:
                    if tx.sender == "0":
                        text += f"      🎯 [系统奖励] → {tx.receiver}: {tx.amount:.8f} BPC\n"
                    else:
                        text += f"      📨 {tx.sender[:10]}... → {tx.receiver[:10]}...: {tx.amount:.8f} BPC\n"

            text += "\n"

        self.blockchain_text.setText(text)

    def update_system_info(self):
        """更新系统信息"""
        from datetime import datetime

        text = f"BuptCoin 区块链系统\n"
        text += f"{'=' * 60}\n\n"
        text += f"📅 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += f"🏷️  系统版本: 3.0 (数据库集成版)\n"
        text += f"👤 钱包名称: {self.wallet.name}\n"
        text += f"👛 地址数量: {len(self.wallet.addresses)}\n"
        text += f"⛓️  区块数量: {len(self.blockchain.chain)}\n"
        text += f"📝 待处理交易: {len(self.blockchain.pending_transactions)}\n"
        text += f"⚙️  挖矿难度: {self.blockchain.difficulty}\n"
        text += f"💰 挖矿奖励: {self.blockchain.mining_reward} BPC\n"
        text += f"💸 交易手续费: {self.blockchain.transaction_fee} BPC\n\n"

        # 显示合约信息
        if hasattr(self.blockchain, 'contract_manager'):
            contracts = self.blockchain.contract_manager.contracts
            if contracts:
                text += f"📜 智能合约: {len(contracts)} 个\n"
                for i, (address, contract) in enumerate(list(contracts.items())[:2], 1):
                    text += f"   {i}. {address[:20]}... (余额: {contract.balance:.2f} BPC)\n"
            else:
                text += f"📜 智能合约: 0 个\n"

        text += f"\n💡 使用提示:\n"
        text += f"  1. 创世地址 'genesis' 有初始余额\n"
        text += f"  2. 发送交易前请确保余额充足\n"
        text += f"  3. 挖矿需要有待处理交易\n"
        text += f"  4. 系统每3秒自动刷新一次\n"

        self.system_info_text.setText(text)

    def view_full_blockchain(self):
        """查看完整区块链"""
        dialog = QDialog(self)
        dialog.setWindowTitle("完整区块链")
        dialog.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))

        text = f"完整区块链（共 {len(self.blockchain.chain)} 个区块）\n"
        text += "=" * 80 + "\n\n"

        for i, block in enumerate(self.blockchain.chain):
            text += f"区块 #{block.index}:\n"
            text += f"  哈希: {block.hash}\n"
            text += f"  时间戳: {block.timestamp}\n"
            text += f"  前驱哈希: {block.previous_hash}\n"
            text += f"  随机数: {block.nonce}\n"
            text += f"  交易数: {len(block.transactions)}\n"

            if len(block.transactions) > 0:
                text += f"  交易列表:\n"
                for tx in block.transactions:
                    text += f"    - {tx.sender} -> {tx.receiver}: {tx.amount} ({tx.transaction_type})\n"

            text += "\n" + "-" * 40 + "\n\n"

        text_edit.setText(text)
        layout.addWidget(text_edit)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec_()

    def create_new_wallet(self):
        """创建新钱包"""
        name, ok = QInputDialog.getText(self, "创建新钱包", "请输入钱包名称:")
        if ok and name:
            self.wallet = Wallet(name)
            self.update_address_lists()
            self.update_display()
            QMessageBox.information(self, "成功", f"新钱包 '{name}' 创建成功！")

    def test_transaction(self):
        """测试交易"""
        # 创建一笔测试交易
        if len(self.wallet.addresses) >= 2:
            sender = self.wallet.addresses[0]
            receiver = self.wallet.addresses[1]

            # 检查余额
            balance = self.blockchain.get_balance(sender)
            if balance > 1:
                amount = 1.0
                transaction = Transaction(sender, receiver, amount)

                if self.blockchain.add_transaction(transaction):
                    QMessageBox.information(self, "测试成功",
                                            f"测试交易创建成功！\n"
                                            f"发送方: {sender}\n"
                                            f"接收方: {receiver}\n"
                                            f"金额: {amount} BPC")
                    self.update_display()
                else:
                    QMessageBox.warning(self, "测试失败", "测试交易创建失败")
            else:
                QMessageBox.warning(self, "余额不足", f"发送方余额不足: {balance} BPC")
        else:
            QMessageBox.warning(self, "地址不足", "需要至少2个地址才能测试交易")

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>BuptCoin 区块链系统</h2>
        <p><b>版本:</b> 3.0 (数据库集成版)</p>
        <p><b>作者:</b> 北京邮电大学区块链项目组</p>
        <p><b>功能模块:</b></p>
        <ul>
            <li>完整的区块链实现</li>
            <li>数字货币交易系统</li>
            <li>工作量证明挖矿机制</li>
            <li>MySQL 数据库持久化</li>
            <li>用户管理系统</li>
            <li>多种交易类型（转账、质押、投票、合约）</li>
            <li>图形化用户界面</li>
        </ul>
        <p><b>说明:</b></p>
        <p>这是一个教学用的区块链数字货币系统，演示了区块链的核心概念和工作原理。</p>
        <hr>
        <p style="color: #666;">© 2023 BuptCoin Project - 北京邮电大学</p>
        """
        QMessageBox.about(self, "关于 BuptCoin", about_text)

    def closeEvent(self, event):
        """关闭窗口事件"""
        reply = QMessageBox.question(self, '确认退出',
                                     "确定要退出 BuptCoin 系统吗？",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.timer.stop()
            event.accept()
        else:
            event.ignore()

    # ======================== gui.py (在数据显示时使用映射) ========================
    def format_address_for_display(self, address: str) -> str:
        """格式化地址显示：尝试用用户名替换地址"""
        # 假设 db 实例是可用的
        from database import db
        username = db.get_username_by_address(address)

        if username:
            # 显示用户名 (地址哈希的后四位)
            return f"{username} ({address[-4:]})"
        else:
            # 如果是智能合约地址或外部地址，只显示部分哈希
            return f"地址...{address[-8:]}"



def main():
    app = QApplication(sys.argv)

    # 设置应用字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 设置应用程序名称
    app.setApplicationName("BuptCoin")
    app.setOrganizationName("BUPT")

    # 创建并显示主窗口
    gui = BlockchainGUI()
    gui.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    # 导入 datetime 用于时间格式化
    from datetime import datetime

    main()