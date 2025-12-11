# gui_enhanced.py - 增强版GUI，拥有更美观的可视化和更高的代码健壮性
import sys
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QTableWidget, QTableWidgetItem, QDialog, QMessageBox, QTabWidget,
    QFrame, QInputDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QIcon, QBrush, QPixmap
import os
import sys

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blockchain import Blockchain, Transaction
from wallet import Wallet


class MiningWorker(QThread):
    """挖矿工作线程 - 改进版"""
    mining_finished = pyqtSignal(bool, str)
    mining_progress = pyqtSignal(str)
    mining_error = pyqtSignal(str)

    def __init__(self, blockchain: Blockchain, miner_address: str):
        super().__init__()
        self.blockchain = blockchain
        self.miner_address = miner_address
        self.is_running = True

    def run(self):
        """执行挖矿"""
        try:
            self.mining_progress.emit("⛏️ 开始挖矿，计算工作量证明...")
            time.sleep(0.1)

            success = self.blockchain.mine_pending_transactions(self.miner_address)

            if success:
                latest_block = self.blockchain.get_latest_block()
                msg = f"✅ 挖矿成功！\n新区块 #{latest_block.index}\n矿工 {self.miner_address[:20]}... 获得奖励"
                self.mining_finished.emit(True, msg)
            else:
                self.mining_finished.emit(False, "⚠️ 没有待处理交易")

        except Exception as e:
            self.mining_error.emit(str(e))

    def stop(self):
        """停止挖矿"""
        self.is_running = False


class BlockchainGUIEnhanced(QMainWindow):
    """增强版区块链GUI - 提供更美观的可视化和更健壮的代码"""

    def __init__(self):
        super().__init__()
        
        # 初始化数据存储
        self.blockchain = None
        self.wallet = None
        self.database_connected = False
        self.current_user = None
        self.mining_worker = None
        self.mining_thread = None
        
        try:
            # 显示启动对话框
            if self.show_startup_dialog():
                self.init_system_after_login()
                self.setup_styles()
                self.init_ui()
                self.setup_timers()
                self.update_display()
            else:
                self.close()
        except Exception as e:
            self.show_error("初始化错误", f"系统初始化失败: {str(e)}")
            self.close()

    def show_startup_dialog(self) -> bool:
        """显示启动对话框 - 改进的错误处理"""
        dialog = QDialog(self, Qt.Dialog)
        dialog.setWindowTitle("BuptCoin 启动")
        dialog.setFixedSize(450, 350)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QLabel {
                color: #2c3e50;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel("🚀 欢迎使用 BuptCoin")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Microsoft YaHei", 16, QFont.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 状态检查
        db_status_label = QLabel("正在检查系统...")
        db_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(db_status_label)

        try:
            from database import db
            if hasattr(db, 'is_connected') and db.is_connected:
                self.database_connected = True
                self.db = db
                db_status_label.setText("✅ 数据库已连接")
                db_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.current_user = {'id': 1, 'username': 'test_user', 'email': None}
            else:
                db_status_label.setText("⚠️ 使用内存模式运行")
                db_status_label.setStyleSheet("color: #e67e22; font-weight: bold;")
                self.current_user = {'id': 0, 'username': 'guest', 'email': None}
        except Exception as e:
            db_status_label.setText(f"⚠️ 数据库连接失败: {str(e)[:30]}")
            db_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.current_user = {'id': 0, 'username': 'memory_mode', 'email': None}

        # 按钮
        button_layout = QHBoxLayout()
        
        start_btn = QPushButton("🚀 启动系统")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a7bd5;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2a6bc5;
            }
        """)
        start_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(start_btn)

        exit_btn = QPushButton("❌ 退出")
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        exit_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(exit_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

        return dialog.exec_() == QDialog.Accepted

    def init_system_after_login(self):
        """登录后初始化系统"""
        try:
            self.blockchain = Blockchain(difficulty=2)
            self.wallet = Wallet("Enhanced Wallet")
            print(f"✅ 系统初始化完成")
        except Exception as e:
            raise Exception(f"系统初始化失败: {e}")

    def setup_styles(self):
        """设置全局样式 - 现代化设计"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #3a7bd5;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #3a7bd5;
            }
            
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
            
            QLabel#titleLabel {
                font-size: 20px;
                font-weight: bold;
                color: #1a237e;
            }
            
            QPushButton {
                font-size: 13px;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
                background-color: #3a7bd5;
                color: white;
                border: none;
                min-height: 35px;
            }
            
            QPushButton:hover {
                background-color: #2a6bc5;
            }
            
            QPushButton:pressed {
                background-color: #1a5bb5;
            }
            
            QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
                font-size: 12px;
                padding: 8px;
                border: 1px solid #d1d9e6;
                border-radius: 4px;
                background-color: white;
                min-height: 32px;
            }
            
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #d1d9e6;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            
            QTableWidget {
                font-size: 11px;
                border: 1px solid #d1d9e6;
                border-radius: 4px;
                background-color: white;
                gridline-color: #eaeaea;
            }
        """)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('💰 BuptCoin - 区块链数字货币系统 [增强版-已修复]')
        self.setGeometry(50, 50, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. 顶部信息栏
        self.create_header_section(main_layout)

        # 2. 快速信息卡片
        self.create_info_cards_section(main_layout)

        # 3. 主要功能区（标签页）
        self.create_main_tabs_section(main_layout)

        # 4. 底部状态栏
        self.statusBar().showMessage("欢迎使用 BuptCoin | 系统就绪")

        # 5. 菜单栏
        self.create_menubar()

    def create_header_section(self, parent_layout: QVBoxLayout):
        """创建顶部头部区域"""
        header_layout = QHBoxLayout()

        title_label = QLabel("💰 BuptCoin 数字货币系统")
        title_label.setObjectName("titleLabel")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.status_label = QLabel("🟢 系统就绪")
        self.status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #27ae60;")
        header_layout.addWidget(self.status_label)

        parent_layout.addLayout(header_layout)

    def create_info_cards_section(self, parent_layout: QVBoxLayout):
        """创建信息卡片区域"""
        cards_frame = QFrame()
        cards_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #d1d9e6;
                border-radius: 8px;
            }
        """)
        cards_layout = QHBoxLayout(cards_frame)
        cards_layout.setSpacing(20)
        cards_layout.setContentsMargins(20, 15, 20, 15)

        # 余额卡片
        balance_card = self.create_info_card("💰 总余额", "0.00 BPC", "#27ae60")
        self.balance_label = balance_card['value']
        cards_layout.addWidget(balance_card['frame'])

        # 区块链卡片
        chain_card = self.create_info_card("⛓️ 区块数", "0", "#3498db")
        self.chain_label = chain_card['value']
        cards_layout.addWidget(chain_card['frame'])

        # 交易卡片
        tx_card = self.create_info_card("📝 待处理交易", "0", "#f39c12")
        self.pending_label = tx_card['value']
        cards_layout.addWidget(tx_card['frame'])

        # 用户卡片
        user_card = self.create_info_card("👤 当前用户", self.current_user['username'], "#9b59b6")
        cards_layout.addWidget(user_card['frame'])

        cards_layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.update_display)
        cards_layout.addWidget(refresh_btn)

        parent_layout.addWidget(cards_frame)

    def create_info_card(self, title: str, value: str, color: str) -> Dict:
        """创建信息卡片"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px;")
        layout.addWidget(value_label)

        return {'frame': frame, 'value': value_label}

    def create_main_tabs_section(self, parent_layout: QVBoxLayout):
        """创建主要标签页区域"""
        tabs = QTabWidget()
        tabs.setFont(QFont("Microsoft YaHei", 11))

        tabs.addTab(self.create_transaction_tab(), "💸 交易与挖矿")
        tabs.addTab(self.create_blockchain_tab(), "⛓️ 区块浏览器")
        tabs.addTab(self.create_balance_tab(), "💰 余额管理")
        tabs.addTab(self.create_system_info_tab(), "ℹ️ 系统信息")

        parent_layout.addWidget(tabs)

    def create_transaction_tab(self) -> QWidget:
        """创建交易标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 交易创建面板
        trans_group = QGroupBox("📤 创建新交易")
        trans_layout = QGridLayout()
        trans_layout.setSpacing(12)

        trans_layout.addWidget(QLabel("发送方地址:"), 0, 0)
        self.sender_combo = QComboBox()
        trans_layout.addWidget(self.sender_combo, 0, 1, 1, 2)

        # 接收方改为下拉框
        trans_layout.addWidget(QLabel("接收方地址:"), 1, 0)
        self.receiver_combo = QComboBox()
        self.receiver_combo.setEditable(True)  # 允许输入自定义地址
        trans_layout.addWidget(self.receiver_combo, 1, 1, 1, 2)

        trans_layout.addWidget(QLabel("转账金额 (BPC):"), 2, 0)
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0.01, 10000000)
        self.amount_spinbox.setDecimals(8)
        self.amount_spinbox.setValue(1.0)
        trans_layout.addWidget(self.amount_spinbox, 2, 1, 1, 2)

        trans_layout.addWidget(QLabel("交易类型:"), 3, 0)
        self.tx_type_combo = QComboBox()
        self.tx_type_combo.addItems(["transfer", "stake", "vote", "contract"])
        trans_layout.addWidget(self.tx_type_combo, 3, 1, 1, 2)

        trans_layout.addWidget(QLabel("交易备注:"), 4, 0)
        self.data_edit = QLineEdit()
        self.data_edit.setPlaceholderText("可选")
        trans_layout.addWidget(self.data_edit, 4, 1, 1, 2)

        self.send_btn = QPushButton("🚀 发送交易")
        self.send_btn.setFixedHeight(45)
        self.send_btn.clicked.connect(self.handle_send_transaction)
        trans_layout.addWidget(self.send_btn, 5, 0, 1, 3)

        trans_group.setLayout(trans_layout)
        layout.addWidget(trans_group)

        # 挖矿面板
        mine_group = QGroupBox("⛏️ 挖矿")
        mine_layout = QHBoxLayout()

        mine_layout.addWidget(QLabel("矿工地址:"))
        self.miner_combo = QComboBox()
        mine_layout.addWidget(self.miner_combo)

        self.mine_btn = QPushButton("🚀 开始挖矿")
        self.mine_btn.setFixedWidth(150)
        self.mine_btn.clicked.connect(self.handle_start_mining)
        mine_layout.addWidget(self.mine_btn)

        self.mining_progress = QProgressBar()
        self.mining_progress.setVisible(False)
        mine_layout.addWidget(self.mining_progress)

        self.mining_status = QLabel("🟡 等待中...")
        mine_layout.addWidget(self.mining_status)
        mine_layout.addStretch()

        mine_group.setLayout(mine_layout)
        layout.addWidget(mine_group)

        # 交易历史表格
        history_group = QGroupBox("📊 最近交易")
        history_layout = QVBoxLayout()

        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(7)
        self.transaction_table.setHorizontalHeaderLabels(["时间", "类型", "发送方", "→", "接收方", "金额 (BPC)", "状态"])
        self.transaction_table.horizontalHeader().setStretchLastSection(True)
        self.transaction_table.setAlternatingRowColors(True)
        self.transaction_table.setMaximumHeight(300)
        self.transaction_table.verticalHeader().setVisible(False)

        history_layout.addWidget(self.transaction_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        layout.addStretch()
        return widget

    def create_blockchain_tab(self) -> QWidget:
        """创建区块链浏览器标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_group = QGroupBox("🔗 区块链详情")
        info_layout = QVBoxLayout()

        self.blockchain_text = QTextEdit()
        self.blockchain_text.setReadOnly(True)
        self.blockchain_text.setFont(QFont("Consolas", 10))
        info_layout.addWidget(self.blockchain_text)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        button_layout = QHBoxLayout()
        view_full_btn = QPushButton("📜 查看完整区块链")
        view_full_btn.clicked.connect(self.show_full_blockchain)
        button_layout.addWidget(view_full_btn)
        button_layout.addStretch()
        validate_btn = QPushButton("✅ 验证区块链")
        validate_btn.clicked.connect(self.validate_blockchain_integrity)
        button_layout.addWidget(validate_btn)

        layout.addLayout(button_layout)
        return widget

    def create_balance_tab(self) -> QWidget:
        """创建余额管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        balance_group = QGroupBox("👛 钱包地址余额")
        balance_layout = QVBoxLayout()

        self.balance_table = QTableWidget()
        self.balance_table.setColumnCount(4)
        self.balance_table.setHorizontalHeaderLabels(["#", "地址", "余额 (BPC)", "状态"])
        self.balance_table.horizontalHeader().setStretchLastSection(True)
        self.balance_table.setAlternatingRowColors(True)
        self.balance_table.verticalHeader().setVisible(False)

        balance_layout.addWidget(self.balance_table)

        # 总余额显示
        total_frame = QFrame()
        total_frame.setStyleSheet("""
            QFrame {
                background: linear-gradient(135deg, #3a7bd5, #2a6bc5);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        total_layout = QHBoxLayout(total_frame)
        total_layout.addStretch()

        total_text = QLabel("💰 总计余额:")
        total_text.setStyleSheet("color: white; font-weight: bold;")
        total_layout.addWidget(total_text)

        self.total_balance_label = QLabel("0.00")
        self.total_balance_label.setStyleSheet("color: #ffeb3b; font-weight: bold; font-size: 18px;")
        total_layout.addWidget(self.total_balance_label)

        total_unit = QLabel("BPC")
        total_unit.setStyleSheet("color: white; font-weight: bold;")
        total_layout.addWidget(total_unit)

        balance_layout.addWidget(total_frame)
        balance_group.setLayout(balance_layout)
        layout.addWidget(balance_group)

        refresh_btn = QPushButton("🔄 刷新余额")
        refresh_btn.clicked.connect(self.update_balances)
        layout.addWidget(refresh_btn)

        return widget

    def create_system_info_tab(self) -> QWidget:
        """创建系统信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_group = QGroupBox("ℹ️ 系统信息")
        info_layout = QVBoxLayout()

        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        self.system_info_text.setFont(QFont("Consolas", 10))
        info_layout.addWidget(self.system_info_text)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        return widget

    def create_menubar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        file_menu = menubar.addMenu('📁 文件')
        new_wallet_action = file_menu.addAction('🆕 新建钱包')
        new_wallet_action.triggered.connect(self.create_new_wallet)
        file_menu.addSeparator()
        exit_action = file_menu.addAction('❌ 退出')
        exit_action.triggered.connect(self.close)

        tool_menu = menubar.addMenu('🛠️ 工具')
        test_action = tool_menu.addAction('🧪 测试交易')
        test_action.triggered.connect(self.test_transaction)
        debug_action = tool_menu.addAction('🐛 调试信息')
        debug_action.triggered.connect(self.show_debug_info)

        help_menu = menubar.addMenu('❓ 帮助')
        about_action = help_menu.addAction('ℹ️ 关于')
        about_action.triggered.connect(self.show_about_dialog)

    def handle_send_transaction(self):
        """处理发送交易"""
        try:
            sender = self.sender_combo.currentText()
            receiver = self.receiver_combo.currentText().strip()
            amount = self.amount_spinbox.value()

            if not receiver or not sender:
                self.show_warning("输入错误", "请填写所有必要字段")
                return

            if sender == receiver:
                self.show_warning("输入错误", "发送方和接收方不能相同")
                return

            sender_balance = self.blockchain.get_balance(sender)
            total_cost = amount + self.blockchain.transaction_fee

            if sender_balance < total_cost and sender != "0":
                self.show_warning("余额不足", f"需要: {total_cost:.8f}\n当前: {sender_balance:.8f}")
                return

            tx = Transaction(sender, receiver, amount)
            if self.blockchain.add_transaction(tx):
                self.status_label.setText("🟢 交易已发送")
                self.receiver_combo.setCurrentIndex(0)
                QApplication.beep()
                self.update_display()
            else:
                self.show_error("交易失败", "发送交易失败，请检查余额")

        except Exception as e:
            self.show_error("错误", f"发送交易时出错: {str(e)}")

    def handle_start_mining(self):
        """处理开始挖矿"""
        try:
            if not self.blockchain.pending_transactions:
                self.show_info("提示", "没有待处理交易，无需挖矿")
                return

            if self.mining_worker and self.mining_worker.isRunning():
                self.show_warning("挖矿中", "请等待当前挖矿完成")
                return

            miner_address = self.miner_combo.currentText()
            
            self.mine_btn.setEnabled(False)
            self.mining_status.setText("⛏️ 挖矿中...")
            self.status_label.setText("🟡 正在挖矿...")

            self.mining_worker = MiningWorker(self.blockchain, miner_address)
            self.mining_worker.mining_finished.connect(self.on_mining_finished)
            self.mining_worker.mining_error.connect(self.on_mining_error)
            self.mining_worker.start()

        except Exception as e:
            self.show_error("错误", f"启动挖矿失败: {str(e)}")
            self.mine_btn.setEnabled(True)

    def on_mining_finished(self, success: bool, message: str):
        """挖矿完成回调"""
        self.mine_btn.setEnabled(True)

        if success:
            self.mining_status.setText("✅ 挖矿完成")
            self.status_label.setText("🟢 新区块已添加")
            self.show_info("挖矿成功", message)
        else:
            self.mining_status.setText("⚠️ 挖矿失败")

        self.update_display()

    def on_mining_error(self, error_msg: str):
        """挖矿错误回调"""
        self.mine_btn.setEnabled(True)
        self.mining_status.setText("❌ 挖矿错误")
        self.status_label.setText("🔴 挖矿出错")
        self.show_error("挖矿错误", f"挖矿过程中出错: {error_msg}")

    def update_display(self):
        """
        更新整个界面显示
        【修复点】1：保存当前选中的地址，刷新后恢复
        """
        try:
            # 【关键修复】1：保存当前选中的地址
            sender_current = self.sender_combo.currentText()
            receiver_current = self.receiver_combo.currentText()
            miner_current = self.miner_combo.currentText()
            
            # 更新各个部分
            self.update_address_lists(sender_current, receiver_current, miner_current)
            self.update_balances()
            self.update_blockchain_info()
            self.update_transaction_table()
            self.update_system_info()
        except Exception as e:
            print(f"更新显示失败: {e}")

    def update_address_lists(self, sender_restore="", receiver_restore="", miner_restore=""):
        """
        更新地址下拉框
        【修复点】2：阻塞信号，防止触发 currentIndexChanged
        """
        # 获取所有唯一地址
        all_addresses = list(set(['genesis'] + self.wallet.addresses))
        all_addresses.sort()
        
        # 【关键修夏】2：阻塞信号，防止触发 currentIndexChanged
        self.sender_combo.blockSignals(True)
        self.receiver_combo.blockSignals(True)
        self.miner_combo.blockSignals(True)
        
        try:
            # 清空并重新填充发送方下拉框
            self.sender_combo.clear()
            for address in all_addresses:
                self.sender_combo.addItem(address)
            
            # 清空并重新填充接收方下拉框
            self.receiver_combo.clear()
            for address in all_addresses:
                self.receiver_combo.addItem(address)
            
            # 清空并重新填充矿工下拉框
            self.miner_combo.clear()
            for address in all_addresses:
                self.miner_combo.addItem(address)
            
            # 【关键修夏】3：恢复之前选中的地址
            if sender_restore:
                sender_index = self.sender_combo.findText(sender_restore)
                if sender_index >= 0:
                    self.sender_combo.setCurrentIndex(sender_index)
            
            if receiver_restore:
                receiver_index = self.receiver_combo.findText(receiver_restore)
                if receiver_index >= 0:
                    self.receiver_combo.setCurrentIndex(receiver_index)
                else:
                    # 如果找不到，可能是自定义输入，直接设置文本
                    self.receiver_combo.setEditText(receiver_restore)
            
            if miner_restore:
                miner_index = self.miner_combo.findText(miner_restore)
                if miner_index >= 0:
                    self.miner_combo.setCurrentIndex(miner_index)
        
        finally:
            # 【关键修夏】4：恢复信号
            self.sender_combo.blockSignals(False)
            self.receiver_combo.blockSignals(False)
            self.miner_combo.blockSignals(False)

    def update_balances(self):
        """更新余额显示"""
        total_balance = 0
        all_addresses = list(set(['genesis'] + self.wallet.addresses))
        all_addresses.sort()
        
        self.balance_table.setRowCount(len(all_addresses))

        for i, address in enumerate(all_addresses):
            balance = self.blockchain.get_balance(address)
            total_balance += balance

            self.balance_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.balance_table.setItem(i, 1, QTableWidgetItem(address if len(address) <= 20 else address[:20] + "..."))
            
            balance_item = QTableWidgetItem(f"{balance:.8f}")
            balance_item.setTextAlignment(Qt.AlignRight)
            self.balance_table.setItem(i, 2, balance_item)
            
            status = "✅ 富裕" if balance > 100 else "⚠️ 正常" if balance > 0 else "❌ 空"
            self.balance_table.setItem(i, 3, QTableWidgetItem(status))

        self.total_balance_label.setText(f"{total_balance:.8f}")
        self.balance_label.setText(f"{total_balance:.8f} BPC")
        self.chain_label.setText(f"{len(self.blockchain.chain)}")
        self.pending_label.setText(f"{len(self.blockchain.pending_transactions)}")

    def update_blockchain_info(self):
        """更新区块链信息显示"""
        text = f"📊 区块链状态\n{'=' * 60}\n"
        text += f"区块总数: {len(self.blockchain.chain)}\n"
        text += f"待处理交易: {len(self.blockchain.pending_transactions)}\n"
        text += f"挖矿难度: {self.blockchain.difficulty}\n"
        text += f"挖矿奖励: {self.blockchain.mining_reward} BPC\n"
        text += f"交易手续费: {self.blockchain.transaction_fee} BPC\n"
        text += f"{'=' * 60}\n\n"

        recent_blocks = self.blockchain.chain[-3:] if len(self.blockchain.chain) > 3 else self.blockchain.chain

        for block in recent_blocks:
            text += f"🔷 区块 #{block.index}\n"
            text += f"   哈希: {block.hash[:16]}...\n"
            text += f"   时间: {datetime.fromtimestamp(block.timestamp).strftime('%H:%M:%S')}\n"
            text += f"   交易: {len(block.transactions)}\n\n"

        self.blockchain_text.setText(text)

    def update_transaction_table(self):
        """更新交易表格"""
        transactions = []

        for block in self.blockchain.chain:
            for tx in block.transactions:
                transactions.append({
                    'time': tx.timestamp,
                    'type': tx.transaction_type,
                    'sender': tx.sender,
                    'receiver': tx.receiver,
                    'amount': tx.amount,
                    'status': '✅ 已确认'
                })

        for tx in self.blockchain.pending_transactions:
            transactions.append({
                'time': tx.timestamp,
                'type': tx.transaction_type,
                'sender': tx.sender,
                'receiver': tx.receiver,
                'amount': tx.amount,
                'status': '⏳ 待处理'
            })

        transactions.sort(key=lambda x: x['time'], reverse=True)
        self.transaction_table.setRowCount(min(len(transactions), 20))

        for i, tx in enumerate(transactions[:20]):
            time_str = datetime.fromtimestamp(tx['time']).strftime("%H:%M:%S")
            self.transaction_table.setItem(i, 0, QTableWidgetItem(time_str))
            self.transaction_table.setItem(i, 1, QTableWidgetItem(tx['type']))
            self.transaction_table.setItem(i, 2, QTableWidgetItem(tx['sender'][:12]))
            self.transaction_table.setItem(i, 3, QTableWidgetItem("→"))
            self.transaction_table.setItem(i, 4, QTableWidgetItem(tx['receiver'][:12]))
            
            amount_item = QTableWidgetItem(f"{tx['amount']:.8f}")
            amount_item.setTextAlignment(Qt.AlignRight)
            self.transaction_table.setItem(i, 5, amount_item)
            
            self.transaction_table.setItem(i, 6, QTableWidgetItem(tx['status']))

    def update_system_info(self):
        """更新系统信息"""
        text = f"BuptCoin 系统信息\n{'=' * 60}\n"
        text += f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += f"系统版本: 3.3 (增强版-已修复)\n"
        text += f"用户: {self.current_user['username']}\n"
        text += f"区块数: {len(self.blockchain.chain)}\n"
        text += f"待处理交易: {len(self.blockchain.pending_transactions)}\n"
        text += f"难度: {self.blockchain.difficulty}\n"
        text += f"奖励: {self.blockchain.mining_reward} BPC\n"
        self.system_info_text.setText(text)

    def show_full_blockchain(self):
        """显示完整区块链"""
        dialog = QDialog(self)
        dialog.setWindowTitle("完整区块链")
        dialog.setGeometry(200, 200, 900, 700)
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))

        text = f"完整区块链 (共 {len(self.blockchain.chain)} 个区块)\n"
        for block in self.blockchain.chain:
            text += f"区块 #{block.index}: {len(block.transactions)} 笔交易\n"

        text_edit.setText(text)
        layout.addWidget(text_edit)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec_()

    def validate_blockchain_integrity(self):
        """验证区块链完整性"""
        if self.blockchain.is_chain_valid():
            self.show_info("验证结果", "✅ 区块链验证通过！")
            self.status_label.setText("🟢 区块链有效")
        else:
            self.show_error("验证结果", "❌ 区块链验证失败！")
            self.status_label.setText("🔴 区块链无效")

    def create_new_wallet(self):
        """创建新钱包"""
        name, ok = QInputDialog.getText(self, "创建新钱包", "请输入钱包名称:")
        if ok and name:
            self.wallet = Wallet(name)
            self.update_display()
            self.show_info("成功", f"新钱包 '{name}' 创建成功！")

    def test_transaction(self):
        """测试交易"""
        try:
            if len(self.wallet.addresses) < 2:
                self.show_warning("信息不足", "需要至少2个地址")
                return

            sender = self.wallet.addresses[0]
            receiver = self.wallet.addresses[1]
            balance = self.blockchain.get_balance(sender)

            if balance > 1:
                tx = Transaction(sender, receiver, 1.0)
                if self.blockchain.add_transaction(tx):
                    self.show_info("成功", "测试交易创建成功！")
                    self.update_display()
            else:
                self.show_warning("余额不足", f"发送方余额: {balance}")
        except Exception as e:
            self.show_error("错误", str(e))

    def show_debug_info(self):
        """显示调试信息"""
        info = f"""
        调试信息:
        --------
        钱包: {self.wallet.name}
        地址数: {len(self.wallet.addresses)}
        区块数: {len(self.blockchain.chain)}
        待处理交易: {len(self.blockchain.pending_transactions)}
        数据库连接: {'是' if self.database_connected else '否'}
        """
        self.show_info("调试信息", info)

    def show_about_dialog(self):
        """显示关于对话框"""
        about_text = """
        <h2>BuptCoin 增强版</h2>
        <p><b>版本:</b> 3.3 (已修复)</p>
        <p><b>功能:</b></p>
        <ul>
            <li>完整的区块链实现</li>
            <li>数字货币交易系统</li>
            <li>工作量证明挖矿</li>
            <li>增强的可视化界面</li>
            <li>多种交易类型支持</li>
        </ul>
        <p><b>修复内容:</b></p>
        <ul>
            <li>✅ 接收方改为下拉选择框</li>
            <li>✅ 去除重复的genesis地址</li>
            <li>✅ 刷新时保持地址选择不被重置</li>
        </ul>
        """
        self.show_info("关于", about_text)

    def setup_timers(self):
        """设置定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(5000)  # 每5秒自动刷新

    # 辅助消息框方法
    def show_info(self, title: str, message: str):
        QMessageBox.information(self, title, message)

    def show_warning(self, title: str, message: str):
        QMessageBox.warning(self, title, message)

    def show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(self, '确认退出', "确定要退出吗?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.timer.stop()
            if self.mining_worker and self.mining_worker.isRunning():
                self.mining_worker.stop()
                self.mining_worker.wait()
            event.accept()
        else:
            event.ignore()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    app.setApplicationName("BuptCoin Enhanced")
    app.setApplicationVersion("3.3")

    try:
        gui = BlockchainGUIEnhanced()
        gui.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "启动错误", f"应用启动失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()