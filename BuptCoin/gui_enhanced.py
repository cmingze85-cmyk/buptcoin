# gui_enhanced.py - 增强版GUI，拥有更美观的可视化和更高的代码健壮性
import sys
import threading
import time
import hashlib
from datetime import datetime
from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QTableWidget, QTableWidgetItem, QDialog, QMessageBox, QTabWidget,
    QFrame, QInputDialog, QProgressBar, QCheckBox, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QIcon, QBrush, QPalette
import os

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blockchain import Blockchain, Transaction
from wallet import Wallet

# 尝试导入数据库模块
try:
    from database import db
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    db = None


class UserAuthDialog(QDialog):
    """用户认证对话框 - 超大窗口，完全消除重叠"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_data = None
        self.database_connected = False
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("BuptCoin 用户认证")
        # 🔥 超大窗口：800×900
        self.setFixedSize(800, 900)
        
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
            QLabel#title_label { 
                color: white; 
                font-size: 48px; 
                font-weight: bold; 
                margin: 0px;
                padding: 15px;
                letter-spacing: 3px;
            }
            QLabel#subtitle_label { 
                color: rgba(255,255,255,0.98); 
                font-size: 18px; 
                margin: 0px;
                padding: 10px;
                letter-spacing: 2px;
            }
            QLabel#db_status { 
                font-size: 15px;
                padding: 12px;
                border-radius: 8px;
                margin: 5px;
            }
            QLabel.field_label { 
                color: white; 
                font-size: 16px;
                font-weight: bold;
                margin: 0px;
                padding: 5px 0px;
            }
            QLineEdit {
                padding: 18px;
                border: 2px solid rgba(255,255,255,0.9);
                border-radius: 10px;
                background-color: white;
                color: #333;
                font-size: 16px;
                min-height: 55px;
                max-height: 55px;
            }
            QLineEdit:focus {
                border: 3px solid #3a7bd5;
                background-color: #f8f9fa;
            }
            QPushButton {
                padding: 18px;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 18px;
                min-height: 60px;
                max-height: 60px;
            }
            QPushButton:hover {
                transform: scale(1.02);
            }
            QCheckBox { 
                color: white; 
                font-size: 15px;
                spacing: 10px;
                padding: 8px;
            }
            QTabWidget::pane { 
                border: 2px solid rgba(255,255,255,0.4); 
                border-radius: 12px; 
                background: rgba(255,255,255,0.15);
            }
            QTabBar::tab { 
                background: rgba(255,255,255,0.3); 
                color: white; 
                padding: 16px 40px;
                margin-right: 10px;
                border-top-left-radius: 10px; 
                border-top-right-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
            }
            QTabBar::tab:selected { 
                background: rgba(255,255,255,0.5); 
                font-weight: bold;
            }
        """)
        
        # 主布局 - 使用固定间距
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(60, 40, 60, 40)
        
        # 标题区域
        title = QLabel("💰 BuptCoin")
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(80)
        main_layout.addWidget(title)
        
        main_layout.addSpacing(10)
        
        # 副标题
        subtitle = QLabel("区块链数字货币系统")
        subtitle.setObjectName("subtitle_label")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFixedHeight(40)
        main_layout.addWidget(subtitle)
        
        main_layout.addSpacing(20)
        
        # 数据库状态
        if DATABASE_AVAILABLE and db and hasattr(db, 'is_connected') and db.is_connected:
            self.database_connected = True
            db_status = QLabel("✅ 数据库已连接")
            db_status.setStyleSheet("""
                color: #4ade80; 
                font-weight: bold; 
                font-size: 15px;
                padding: 12px;
                background: rgba(74, 222, 128, 0.2);
                border-radius: 8px;
            """)
        else:
            db_status = QLabel("⚠️ 内存模式（数据不保存）")
            db_status.setStyleSheet("""
                color: #fbbf24; 
                font-weight: bold; 
                font-size: 15px;
                padding: 12px;
                background: rgba(251, 191, 36, 0.2);
                border-radius: 8px;
            """)
        
        db_status.setObjectName("db_status")
        db_status.setAlignment(Qt.AlignCenter)
        db_status.setFixedHeight(50)
        main_layout.addWidget(db_status)
        
        main_layout.addSpacing(25)
        
        # 标签页 - 固定大尺寸
        self.tab_widget = QTabWidget()
        self.tab_widget.setFixedHeight(520)
        
        login_widget = self.create_login_tab()
        self.tab_widget.addTab(login_widget, "🔐 登录")
        
        if self.database_connected:
            register_widget = self.create_register_tab()
            self.tab_widget.addTab(register_widget, "📝 注册")
        
        main_layout.addWidget(self.tab_widget)
        
        main_layout.addSpacing(25)
        
        # 访客按钮 - 固定高度和位置
        guest_btn = QPushButton("👤 以访客身份继续")
        guest_btn.setStyleSheet("""
            background: rgba(255,255,255,0.35); 
            color: white; 
            border: 3px solid rgba(255,255,255,0.8);
            min-height: 60px;
            max-height: 60px;
            font-size: 18px;
            font-weight: bold;
        """)
        guest_btn.setFixedHeight(60)
        guest_btn.clicked.connect(self.guest_login)
        main_layout.addWidget(guest_btn)
    
    def create_login_tab(self) -> QWidget:
        """创建登录标签页 - 超大布局"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(40, 35, 40, 35)
        
        # 用户名
        username_label = QLabel("📧 用户名:")
        username_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        username_label.setFixedHeight(30)
        layout.addWidget(username_label)
        
        layout.addSpacing(10)
        
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("请输入您的用户名")
        self.login_username.setFixedHeight(55)
        layout.addWidget(self.login_username)
        
        layout.addSpacing(25)
        
        # 密码
        password_label = QLabel("🔒 密码:")
        password_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        password_label.setFixedHeight(30)
        layout.addWidget(password_label)
        
        layout.addSpacing(10)
        
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("请输入您的密码")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setFixedHeight(55)
        self.login_password.returnPressed.connect(self.do_login)
        layout.addWidget(self.login_password)
        
        layout.addSpacing(20)
        
        # 记住我
        self.remember_checkbox = QCheckBox("记住我的登录状态")
        self.remember_checkbox.setFixedHeight(35)
        layout.addWidget(self.remember_checkbox)
        
        # 弹性空间 - 将按钮推到底部
        layout.addStretch()
        
        # 登录按钮
        login_btn = QPushButton("🚀 登  录")
        login_btn.setStyleSheet("""
            background: #10b981; 
            color: white; 
            font-size: 19px;
            font-weight: bold;
            min-height: 60px;
            max-height: 60px;
        """)
        login_btn.setFixedHeight(60)
        login_btn.clicked.connect(self.do_login)
        layout.addWidget(login_btn)
        
        return widget
    
    def create_register_tab(self) -> QWidget:
        """创建注册标签页 - 使用滚动区域"""
        widget = QWidget()
        
        # 使用滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(0)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # 用户名
        username_label = QLabel("👤 用户名:")
        username_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        username_label.setFixedHeight(30)
        layout.addWidget(username_label)
        
        layout.addSpacing(10)
        
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("6-20个字符，支持字母数字")
        self.register_username.setFixedHeight(55)
        layout.addWidget(self.register_username)
        
        layout.addSpacing(20)
        
        # 密码
        password_label = QLabel("🔑 密码:")
        password_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        password_label.setFixedHeight(30)
        layout.addWidget(password_label)
        
        layout.addSpacing(10)
        
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("至少6位字符")
        self.register_password.setEchoMode(QLineEdit.Password)
        self.register_password.setFixedHeight(55)
        layout.addWidget(self.register_password)
        
        layout.addSpacing(20)
        
        # 确认密码
        confirm_label = QLabel("🔐 确认密码:")
        confirm_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        confirm_label.setFixedHeight(30)
        layout.addWidget(confirm_label)
        
        layout.addSpacing(10)
        
        self.register_confirm = QLineEdit()
        self.register_confirm.setPlaceholderText("再次输入相同的密码")
        self.register_confirm.setEchoMode(QLineEdit.Password)
        self.register_confirm.setFixedHeight(55)
        layout.addWidget(self.register_confirm)
        
        layout.addSpacing(20)
        
        # 邮箱
        email_label = QLabel("📮 邮箱 (可选):")
        email_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        email_label.setFixedHeight(30)
        layout.addWidget(email_label)
        
        layout.addSpacing(10)
        
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("example@email.com")
        self.register_email.setFixedHeight(55)
        layout.addWidget(self.register_email)
        
        layout.addSpacing(30)
        
        # 注册按钮
        register_btn = QPushButton("📝 立即注册")
        register_btn.setStyleSheet("""
            background: #3b82f6; 
            color: white; 
            font-size: 19px;
            font-weight: bold;
            min-height: 60px;
            max-height: 60px;
        """)
        register_btn.setFixedHeight(60)
        register_btn.clicked.connect(self.do_register)
        layout.addWidget(register_btn)
        
        # 添加底部空白
        layout.addSpacing(20)
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        return widget
    
    def do_login(self):
        if not self.database_connected:
            QMessageBox.warning(self, "警告", "数据库未连接，无法登录")
            return
        
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "错误", "请填写用户名和密码")
            return
        
        user = db.authenticate_user(username, password)
        if user:
            self.user_data = user
            QMessageBox.information(self, "成功", f"欢迎回来，{username}！")
            self.accept()
        else:
            QMessageBox.critical(self, "失败", "用户名或密码错误")
    
    def do_register(self):
        if not self.database_connected:
            QMessageBox.warning(self, "警告", "数据库未连接")
            return
        
        username = self.register_username.text().strip()
        password = self.register_password.text().strip()
        confirm = self.register_confirm.text().strip()
        email = self.register_email.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "错误", "用户名和密码不能为空")
            return
        if len(username) < 6 or len(username) > 20:
            QMessageBox.warning(self, "错误", "用户名6-20个字符")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "错误", "密码至少6位")
            return
        if password != confirm:
            QMessageBox.warning(self, "错误", "两次密码不一致")
            return
        
        user_id = db.create_user(username, password, email if email else None)
        if user_id:
            user = db.get_user_by_id(user_id)
            if user:
                self.user_data = user
                db.create_wallet_address(user_id, f"{username}的默认钱包")
                QMessageBox.information(self, "成功", f"账户创建成功！\n用户: {username}")
                self.accept()
        else:
            QMessageBox.critical(self, "失败", "用户名已存在")
    
    def guest_login(self):
        self.user_data = {'id': 0, 'username': 'guest', 'email': None}
        self.accept()


class MiningWorker(QThread):
    """挖矿线程"""
    mining_finished = pyqtSignal(bool, str)
    mining_progress = pyqtSignal(str)
    mining_error = pyqtSignal(str)

    def __init__(self, blockchain: Blockchain, miner_address: str):
        super().__init__()
        self.blockchain = blockchain
        self.miner_address = miner_address
        self.is_running = True

    def run(self):
        try:
            self.mining_progress.emit("⛏️ 开始挖矿...")
            time.sleep(0.1)
            success = self.blockchain.mine_pending_transactions(self.miner_address)
            
            if success:
                latest_block = self.blockchain.get_latest_block()
                msg = f"✅ 挖矿成功！\n新区块 #{latest_block.index}\n矿工获得奖励"
                self.mining_finished.emit(True, msg)
            else:
                self.mining_finished.emit(False, "⚠️ 没有待处理交易")
        except Exception as e:
            self.mining_error.emit(str(e))

    def stop(self):
        self.is_running = False


class BlockchainGUIEnhanced(QMainWindow):
    """增强版GUI - 含所有CLI功能"""

    def __init__(self):
        super().__init__()
        
        self.blockchain = None
        self.wallet = None
        self.database_connected = False
        self.current_user = None
        self.mining_worker = None
        self.db = None
        
        try:
            if self.show_startup_dialog():
                self.init_system_after_login()
                self.setup_styles()
                self.init_ui()
                self.setup_timers()
                self.update_display()
            else:
                self.close()
        except Exception as e:
            self.show_error("错误", f"初始化失败: {str(e)}")
            self.close()

    def show_startup_dialog(self) -> bool:
        """显示启动对话框"""
        auth_dialog = UserAuthDialog(self)
        
        if auth_dialog.exec_() == QDialog.Accepted:
            self.current_user = auth_dialog.user_data
            self.database_connected = auth_dialog.database_connected
            if self.database_connected:
                self.db = db
            return True
        return False

    def init_system_after_login(self):
        try:
            self.blockchain = Blockchain(difficulty=2)
            if self.current_user and self.current_user['id'] > 0 and self.database_connected:
                self.wallet = Wallet(f"User_{self.current_user['id']}_Wallet", user_id=self.current_user['id'])
            else:
                self.wallet = Wallet("BuptCoin Wallet")
        except Exception as e:
            raise Exception(f"系统初始化失败: {e}")

    def setup_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f7fa; }
            QGroupBox {
                font-size: 13px; font-weight: bold; border: 2px solid #3a7bd5;
                border-radius: 8px; margin-top: 12px; padding-top: 12px; background-color: white;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #3a7bd5; }
            QPushButton {
                font-size: 13px; font-weight: bold; padding: 10px 20px; border-radius: 6px;
                background-color: #3a7bd5; color: white; border: none; min-height: 35px;
            }
            QPushButton:hover { background-color: #2a6bc5; }
            QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 8px; border: 1px solid #d1d9e6; border-radius: 4px; background-color: white;
            }
            QTableWidget { border: 1px solid #d1d9e6; border-radius: 4px; gridline-color: #eaeaea; }
        """)

    def init_ui(self):
        self.setWindowTitle('💰 BuptCoin - 完整功能版 v5.0')
        self.setGeometry(50, 50, 1500, 950)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.create_header(layout)
        self.create_info_cards(layout)
        self.create_main_tabs(layout)
        
        self.statusBar().showMessage(f"欢迎 {self.current_user['username']} | 系统就绪")
        self.create_menubar()

    def create_header(self, layout):
        header = QHBoxLayout()
        
        title = QLabel("💰 BuptCoin 完整功能版")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1a237e;")
        header.addWidget(title)
        header.addStretch()
        
        user_label = QLabel(f"👤 {self.current_user['username']}")
        user_label.setStyleSheet("font-size: 14px; color: #666;")
        header.addWidget(user_label)
        
        layout.addLayout(header)

    def create_info_cards(self, layout):
        cards = QFrame()
        cards.setStyleSheet("QFrame { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 15px; }")
        cards_layout = QHBoxLayout(cards)
        
        self.balance_label = self.create_info_card("💰 总余额", "0.00 BPC", "#10b981")
        cards_layout.addWidget(self.balance_label['frame'])
        
        self.blocks_label = self.create_info_card("⛓️ 区块数", "0", "#3b82f6")
        cards_layout.addWidget(self.blocks_label['frame'])
        
        self.pending_label = self.create_info_card("📝 待处理", "0", "#f59e0b")
        cards_layout.addWidget(self.pending_label['frame'])
        
        user_id_text = str(self.current_user['id']) if self.current_user['id'] > 0 else "访客"
        self.user_label = self.create_info_card("👤 用户ID", user_id_text, "#8b5cf6")
        cards_layout.addWidget(self.user_label['frame'])
        
        cards_layout.addStretch()
        layout.addWidget(cards)

    def create_info_card(self, title, value, color):
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {color}15; border: 2px solid {color}; border-radius: 8px; padding: 15px; }}")
        layout = QVBoxLayout(frame)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        layout.addWidget(value_label)
        
        return {'frame': frame, 'value': value_label}

    def create_main_tabs(self, layout):
        tabs = QTabWidget()
        tabs.setFont(QFont("Microsoft YaHei", 11))
        
        tabs.addTab(self.create_transaction_tab(), "💸 交易")
        tabs.addTab(self.create_balance_tab(), "💰 余额")
        tabs.addTab(self.create_blockchain_tab(), "⛓️ 区块链")
        tabs.addTab(self.create_stake_tab(), "🏆 质押排名")
        tabs.addTab(self.create_vote_tab(), "🗳️ 投票结果")
        
        if self.database_connected:
            tabs.addTab(self.create_database_tab(), "💾 数据库")
        
        tabs.addTab(self.create_system_tab(), "ℹ️ 系统")
        
        layout.addWidget(tabs)

    def create_transaction_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("📤 创建交易")
        grid = QGridLayout()
        
        grid.addWidget(QLabel("发送方:"), 0, 0)
        self.sender_combo = QComboBox()
        grid.addWidget(self.sender_combo, 0, 1)
        
        grid.addWidget(QLabel("接收方:"), 1, 0)
        self.receiver_combo = QComboBox()
        self.receiver_combo.setEditable(True)
        grid.addWidget(self.receiver_combo, 1, 1)
        
        grid.addWidget(QLabel("金额:"), 2, 0)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 1000000)
        self.amount_spin.setDecimals(8)
        grid.addWidget(self.amount_spin, 2, 1)
        
        grid.addWidget(QLabel("类型:"), 3, 0)
        self.tx_type_combo = QComboBox()
        self.tx_type_combo.addItems(["transfer", "stake", "vote", "contract"])
        grid.addWidget(self.tx_type_combo, 3, 1)
        
        grid.addWidget(QLabel("备注:"), 4, 0)
        self.tx_data_edit = QLineEdit()
        grid.addWidget(self.tx_data_edit, 4, 1)
        
        send_btn = QPushButton("🚀 发送交易")
        send_btn.clicked.connect(self.send_transaction)
        grid.addWidget(send_btn, 5, 0, 1, 2)
        
        group.setLayout(grid)
        layout.addWidget(group)
        
        mine_group = QGroupBox("⛏️ 挖矿")
        mine_layout = QHBoxLayout()
        mine_layout.addWidget(QLabel("矿工:"))
        self.miner_combo = QComboBox()
        mine_layout.addWidget(self.miner_combo)
        mine_btn = QPushButton("🚀 开始挖矿")
        mine_btn.clicked.connect(self.start_mining)
        mine_layout.addWidget(mine_btn)
        self.mining_status = QLabel("等待中")
        mine_layout.addWidget(self.mining_status)
        mine_layout.addStretch()
        mine_group.setLayout(mine_layout)
        layout.addWidget(mine_group)
        
        history_group = QGroupBox("📊 最近交易")
        history_layout = QVBoxLayout()
        self.tx_table = QTableWidget()
        self.tx_table.setColumnCount(7)
        self.tx_table.setHorizontalHeaderLabels(["时间", "类型", "发送方", "接收方", "金额", "状态", "备注"])
        self.tx_table.horizontalHeader().setStretchLastSection(True)
        history_layout.addWidget(self.tx_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        return widget

    def create_balance_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("💰 地址余额")
        group_layout = QVBoxLayout()
        
        self.balance_table = QTableWidget()
        self.balance_table.setColumnCount(5)
        self.balance_table.setHorizontalHeaderLabels(["#", "地址", "昵称", "余额", "状态"])
        group_layout.addWidget(self.balance_table)
        
        total_frame = QFrame()
        total_frame.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2); border-radius: 8px; padding: 20px; }")
        total_layout = QHBoxLayout(total_frame)
        total_layout.addStretch()
        
        total_text = QLabel("💰 总余额:")
        total_text.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        total_layout.addWidget(total_text)
        
        self.total_balance = QLabel("0.00")
        self.total_balance.setStyleSheet("color: #fbbf24; font-size: 24px; font-weight: bold;")
        total_layout.addWidget(self.total_balance)
        
        total_unit = QLabel("BPC")
        total_unit.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        total_layout.addWidget(total_unit)
        
        sync_btn = QPushButton("🔄 同步数据库余额")
        sync_btn.setStyleSheet("background: white; color: #667eea; font-weight: bold; padding: 10px 20px; border-radius: 6px;")
        sync_btn.clicked.connect(self.sync_balances_to_database)
        total_layout.addWidget(sync_btn)
        
        group_layout.addWidget(total_frame)
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        return widget

    def create_blockchain_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("⛓️ 区块链信息")
        group_layout = QVBoxLayout()
        
        self.blockchain_text = QTextEdit()
        self.blockchain_text.setReadOnly(True)
        self.blockchain_text.setFont(QFont("Consolas", 10))
        group_layout.addWidget(self.blockchain_text)
        
        btn_layout = QHBoxLayout()
        validate_btn = QPushButton("✅ 验证区块链")
        validate_btn.clicked.connect(self.validate_blockchain)
        btn_layout.addWidget(validate_btn)
        btn_layout.addStretch()
        group_layout.addLayout(btn_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        return widget

    def create_stake_tab(self) -> QWidget:
        """新增: 质押排名标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("🏆 质押排名")
        group_layout = QVBoxLayout()
        
        self.stake_table = QTableWidget()
        self.stake_table.setColumnCount(4)
        self.stake_table.setHorizontalHeaderLabels(["排名", "地址", "质押金额", "占比"])
        group_layout.addWidget(self.stake_table)
        
        stats_layout = QHBoxLayout()
        self.stake_total_label = QLabel("总质押: 0.00 BPC")
        self.stake_total_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #3b82f6;")
        stats_layout.addWidget(self.stake_total_label)
        
        self.stake_count_label = QLabel("质押地址数: 0")
        self.stake_count_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #8b5cf6;")
        stats_layout.addWidget(self.stake_count_label)
        stats_layout.addStretch()
        group_layout.addLayout(stats_layout)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.update_stake_ranking)
        group_layout.addWidget(refresh_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        return widget

    def create_vote_tab(self) -> QWidget:
        """新增: 投票结果标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("🗳️ 投票结果")
        group_layout = QVBoxLayout()
        
        self.vote_table = QTableWidget()
        self.vote_table.setColumnCount(4)
        self.vote_table.setHorizontalHeaderLabels(["候选人", "得票数", "占比", "进度"])
        group_layout.addWidget(self.vote_table)
        
        leader_frame = QFrame()
        leader_frame.setStyleSheet("QFrame { background: #dcfce7; border: 2px solid #10b981; border-radius: 8px; padding: 15px; }")
        leader_layout = QHBoxLayout(leader_frame)
        
        self.vote_leader_label = QLabel("🏆 当前领先: 暂无")
        self.vote_leader_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #10b981;")
        leader_layout.addWidget(self.vote_leader_label)
        leader_layout.addStretch()
        
        group_layout.addWidget(leader_frame)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.update_vote_results)
        group_layout.addWidget(refresh_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        return widget

    def create_database_tab(self) -> QWidget:
        """新增: 数据库管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        stats_group = QGroupBox("📊 数据库统计")
        stats_layout = QVBoxLayout()
        self.db_stats_text = QTextEdit()
        self.db_stats_text.setReadOnly(True)
        self.db_stats_text.setMaximumHeight(200)
        stats_layout.addWidget(self.db_stats_text)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        rich_group = QGroupBox("💎 富豪榜")
        rich_layout = QVBoxLayout()
        self.rich_table = QTableWidget()
        self.rich_table.setColumnCount(4)
        self.rich_table.setHorizontalHeaderLabels(["排名", "地址/昵称", "余额", "占比"])
        rich_layout.addWidget(self.rich_table)
        rich_group.setLayout(rich_layout)
        layout.addWidget(rich_group)
        
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 刷新数据")
        refresh_btn.clicked.connect(self.update_database_info)
        btn_layout.addWidget(refresh_btn)
        backup_btn = QPushButton("💾 备份数据库")
        backup_btn.clicked.connect(self.backup_database)
        btn_layout.addWidget(backup_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget

    def create_system_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("ℹ️ 系统信息")
        group_layout = QVBoxLayout()
        self.system_text = QTextEdit()
        self.system_text.setReadOnly(True)
        self.system_text.setFont(QFont("Consolas", 10))
        group_layout.addWidget(self.system_text)
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        return widget

    def create_menubar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('📁 文件')
        file_menu.addAction('🆕 新建钱包地址', self.create_wallet_address)
        file_menu.addSeparator()
        file_menu.addAction('❌ 退出', self.close)
        
        tool_menu = menubar.addMenu('🛠️ 工具')
        tool_menu.addAction('🧪 测试交易', self.test_transaction)
        tool_menu.addAction('🔄 刷新所有', self.update_all_displays)
        if self.database_connected:
            tool_menu.addAction('💾 同步余额到数据库', self.sync_balances_to_database)
        
        help_menu = menubar.addMenu('❓ 帮助')
        help_menu.addAction('ℹ️ 关于', self.show_about)

    def send_transaction(self):
        try:
            sender = self.sender_combo.currentText()
            receiver = self.receiver_combo.currentText()
            amount = self.amount_spin.value()
            tx_type = self.tx_type_combo.currentText()
            data = self.tx_data_edit.text().strip()
            
            if not sender or not receiver:
                QMessageBox.warning(self, "错误", "请选择发送方和接收方")
                return
            
            balance = self.blockchain.get_balance(sender)
            if balance < amount + self.blockchain.transaction_fee:
                QMessageBox.warning(self, "余额不足", f"需要: {amount + self.blockchain.transaction_fee:.8f}\n余额: {balance:.8f}")
                return
            
            tx = Transaction(sender, receiver, amount, transaction_type=tx_type, data=data)
            
            if self.blockchain.add_transaction(tx):
                QMessageBox.information(self, "成功", f"交易已提交！\n类型: {tx_type}")
                self.update_all_displays()
            else:
                QMessageBox.critical(self, "失败", "交易提交失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发送交易失败: {str(e)}")

    def start_mining(self):
        if not self.blockchain.pending_transactions:
            QMessageBox.information(self, "提示", "没有待处理交易")
            return
        
        if self.mining_worker and self.mining_worker.isRunning():
            QMessageBox.warning(self, "警告", "正在挖矿中")
            return
        
        miner = self.miner_combo.currentText()
        self.mining_status.setText("⛏️ 挖矿中...")
        
        self.mining_worker = MiningWorker(self.blockchain, miner)
        self.mining_worker.mining_finished.connect(self.on_mining_finished)
        self.mining_worker.start()

    def on_mining_finished(self, success, msg):
        if success:
            self.mining_status.setText("✅ 完成")
            QMessageBox.information(self, "成功", msg)
        else:
            self.mining_status.setText("⚠️ 失败")
        self.update_all_displays()

    def validate_blockchain(self):
        if self.blockchain.is_chain_valid():
            QMessageBox.information(self, "验证结果", "✅ 区块链验证通过！")
        else:
            QMessageBox.critical(self, "验证结果", "❌ 区块链验证失败！")

    def sync_balances_to_database(self):
        """【新增】同步所有地址余额到数据库"""
        if not self.database_connected:
            QMessageBox.warning(self, "警告", "数据库未连接")
            return
        
        try:
            addresses = list(set(['genesis'] + self.wallet.addresses))
            synced_count = 0
            
            for address in addresses:
                balance = self.blockchain.get_balance(address)
                if self.db.update_address_balance(address, balance, 'set'):
                    synced_count += 1
            
            QMessageBox.information(self, "同步完成", 
                f"✅ 成功同步 {synced_count}/{len(addresses)} 个地址余额到数据库！")
            
            self.update_all_displays()
            if hasattr(self, 'db_stats_text'):
                self.update_database_info()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"同步失败: {str(e)}")

    def update_stake_ranking(self):
        """新增: 更新质押排名"""
        stake_amounts = {}
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.transaction_type == "stake":
                    addr = tx.sender
                    stake_amounts[addr] = stake_amounts.get(addr, 0) + tx.amount
        
        if not stake_amounts:
            self.stake_table.setRowCount(0)
            self.stake_total_label.setText("总质押: 0.00 BPC")
            self.stake_count_label.setText("质押地址数: 0")
            return
        
        sorted_stakes = sorted(stake_amounts.items(), key=lambda x: x[1], reverse=True)
        total = sum(stake_amounts.values())
        
        self.stake_table.setRowCount(min(10, len(sorted_stakes)))
        
        for i, (addr, amount) in enumerate(sorted_stakes[:10]):
            percent = (amount / total * 100) if total > 0 else 0
            self.stake_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.stake_table.setItem(i, 1, QTableWidgetItem(addr[:20]))
            self.stake_table.setItem(i, 2, QTableWidgetItem(f"{amount:.8f}"))
            self.stake_table.setItem(i, 3, QTableWidgetItem(f"{percent:.2f}%"))
        
        self.stake_total_label.setText(f"总质押: {total:.2f} BPC")
        self.stake_count_label.setText(f"质押地址数: {len(stake_amounts)}")

    def update_vote_results(self):
        """新增: 更新投票结果"""
        votes = {}
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.transaction_type == "vote":
                    candidate = tx.data if tx.data else tx.receiver
                    votes[candidate] = votes.get(candidate, 0) + tx.amount
        
        if not votes:
            self.vote_table.setRowCount(0)
            self.vote_leader_label.setText("🏆 当前领先: 暂无")
            return
        
        sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        total = sum(votes.values())
        max_votes = max(votes.values())
        
        self.vote_table.setRowCount(len(sorted_votes))
        
        for i, (candidate, vote_count) in enumerate(sorted_votes):
            percent = (vote_count / total * 100) if total > 0 else 0
            bar_len = int((vote_count / max_votes) * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            
            self.vote_table.setItem(i, 0, QTableWidgetItem(candidate))
            self.vote_table.setItem(i, 1, QTableWidgetItem(f"{vote_count:.2f}"))
            self.vote_table.setItem(i, 2, QTableWidgetItem(f"{percent:.1f}%"))
            self.vote_table.setItem(i, 3, QTableWidgetItem(bar))
        
        leader, leader_votes = sorted_votes[0]
        leader_percent = (leader_votes / total * 100) if total > 0 else 0
        self.vote_leader_label.setText(f"🏆 当前领先: {leader} ({leader_percent:.1f}%)")

    def update_database_info(self):
        """新增: 更新数据库信息"""
        if not self.database_connected:
            self.db_stats_text.setText("⚠️ 数据库未连接")
            return
        
        try:
            stats = self.db.get_system_stats()
            text = "📊 数据库系统统计\n" + "="*40 + "\n"
            text += f"活跃用户: {stats.get('active_users', 0)}\n"
            text += f"活跃地址: {stats.get('active_addresses', 0)}\n"
            text += f"区块数量: {stats.get('block_count', 0)}\n"
            text += f"总交易数: {stats.get('total_transactions', 0)}\n"
            text += f"总余额: {stats.get('total_balance', 0):.2f} BPC\n"
            self.db_stats_text.setText(text)
            
            rich_list = self.db.get_rich_list(limit=10)
            self.rich_table.setRowCount(len(rich_list))
            total_balance = sum(r['balance'] for r in rich_list)
            
            for i, rich in enumerate(rich_list):
                percent = (rich['balance'] / total_balance * 100) if total_balance > 0 else 0
                nickname = rich['nickname'] if rich['nickname'] else rich['address'][:20]
                self.rich_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
                self.rich_table.setItem(i, 1, QTableWidgetItem(nickname))
                self.rich_table.setItem(i, 2, QTableWidgetItem(f"{rich['balance']:.2f}"))
                self.rich_table.setItem(i, 3, QTableWidgetItem(f"{percent:.2f}%"))
        except Exception as e:
            self.db_stats_text.setText(f"❌ 获取数据失败: {str(e)}")

    def backup_database(self):
        """新增: 备份数据库"""
        if not self.database_connected:
            QMessageBox.warning(self, "警告", "数据库未连接")
            return
        
        reply = QMessageBox.question(self, "确认", "确定要备份数据库吗？")
        if reply == QMessageBox.Yes:
            try:
                self.db.backup_database("backups")
                QMessageBox.information(self, "成功", "数据库备份完成！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"备份失败: {str(e)}")

    def update_all_displays(self):
        """更新所有显示"""
        try:
            sender = self.sender_combo.currentText()
            receiver = self.receiver_combo.currentText()
            miner = self.miner_combo.currentText()
            
            addresses = list(set(['genesis'] + self.wallet.addresses))
            addresses.sort()
            
            self.sender_combo.blockSignals(True)
            self.receiver_combo.blockSignals(True)
            self.miner_combo.blockSignals(True)
            
            self.sender_combo.clear()
            self.receiver_combo.clear()
            self.miner_combo.clear()
            
            for addr in addresses:
                self.sender_combo.addItem(addr)
                self.receiver_combo.addItem(addr)
                self.miner_combo.addItem(addr)
            
            if sender:
                idx = self.sender_combo.findText(sender)
                if idx >= 0: self.sender_combo.setCurrentIndex(idx)
            if receiver:
                idx = self.receiver_combo.findText(receiver)
                if idx >= 0: self.receiver_combo.setCurrentIndex(idx)
                else: self.receiver_combo.setEditText(receiver)
            if miner:
                idx = self.miner_combo.findText(miner)
                if idx >= 0: self.miner_combo.setCurrentIndex(idx)
            
            self.sender_combo.blockSignals(False)
            self.receiver_combo.blockSignals(False)
            self.miner_combo.blockSignals(False)
            
            total = 0
            self.balance_table.setRowCount(len(addresses))
            for i, addr in enumerate(addresses):
                balance = self.blockchain.get_balance(addr)
                total += balance
                self.balance_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
                self.balance_table.setItem(i, 1, QTableWidgetItem(addr[:20]))
                self.balance_table.setItem(i, 2, QTableWidgetItem("-"))
                self.balance_table.setItem(i, 3, QTableWidgetItem(f"{balance:.8f}"))
                status = "✅ 富裕" if balance > 100 else "⚠️ 正常" if balance > 0 else "❌ 空"
                self.balance_table.setItem(i, 4, QTableWidgetItem(status))
            
            self.balance_label['value'].setText(f"{total:.2f} BPC")
            self.blocks_label['value'].setText(str(len(self.blockchain.chain)))
            self.pending_label['value'].setText(str(len(self.blockchain.pending_transactions)))
            self.total_balance.setText(f"{total:.2f}")
            
            text = f"📊 区块链状态\n{'='*50}\n"
            text += f"区块总数: {len(self.blockchain.chain)}\n"
            text += f"待处理交易: {len(self.blockchain.pending_transactions)}\n"
            text += f"挖矿难度: {self.blockchain.difficulty}\n"
            text += f"挖矿奖励: {self.blockchain.mining_reward} BPC\n\n"
            for block in self.blockchain.chain[-5:]:
                text += f"区块 #{block.index}\n  哈希: {block.hash[:20]}...\n  交易: {len(block.transactions)}\n\n"
            self.blockchain_text.setText(text)
            
            txs = []
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    txs.append({'time': tx.timestamp, 'type': tx.transaction_type,
                               'sender': tx.sender, 'receiver': tx.receiver,
                               'amount': tx.amount, 'status': '✅ 已确认', 'data': tx.data})
            for tx in self.blockchain.pending_transactions:
                txs.append({'time': tx.timestamp, 'type': tx.transaction_type,
                           'sender': tx.sender, 'receiver': tx.receiver,
                           'amount': tx.amount, 'status': '⏳ 待处理', 'data': tx.data})
            
            txs.sort(key=lambda x: x['time'], reverse=True)
            self.tx_table.setRowCount(min(20, len(txs)))
            for i, tx in enumerate(txs[:20]):
                time_str = datetime.fromtimestamp(tx['time']).strftime("%H:%M:%S")
                self.tx_table.setItem(i, 0, QTableWidgetItem(time_str))
                self.tx_table.setItem(i, 1, QTableWidgetItem(tx['type']))
                self.tx_table.setItem(i, 2, QTableWidgetItem(tx['sender'][:12]))
                self.tx_table.setItem(i, 3, QTableWidgetItem(tx['receiver'][:12]))
                self.tx_table.setItem(i, 4, QTableWidgetItem(f"{tx['amount']:.4f}"))
                self.tx_table.setItem(i, 5, QTableWidgetItem(tx['status']))
                self.tx_table.setItem(i, 6, QTableWidgetItem(tx['data'][:20] if tx['data'] else "-"))
            
            sys_text = f"BuptCoin 系统信息\n{'='*50}\n"
            sys_text += f"版本: 5.0 完美登录界面版\n"
            sys_text += f"用户: {self.current_user['username']}\n"
            sys_text += f"用户ID: {self.current_user['id']}\n"
            sys_text += f"数据库: {'已连接' if self.database_connected else '未连接'}\n"
            sys_text += f"区块数: {len(self.blockchain.chain)}\n"
            sys_text += f"难度: {self.blockchain.difficulty}\n"
            sys_text += f"奖励: {self.blockchain.mining_reward} BPC\n"
            sys_text += f"钱包地址数: {len(self.wallet.addresses)}\n"
            self.system_text.setText(sys_text)
            
            self.update_stake_ranking()
            self.update_vote_results()
            if self.database_connected:
                self.update_database_info()
        except Exception as e:
            print(f"更新失败: {e}")

    def update_display(self):
        """Alias for update_all_displays"""
        self.update_all_displays()

    def generate_new_address(self) -> str:
        """生成新地址（使用哈希算法）"""
        import random
        timestamp = str(time.time())
        random_str = str(random.randint(100000, 999999))
        hash_str = hashlib.sha256(f"{timestamp}{random_str}".encode()).hexdigest()
        return f"0x{hash_str[:40]}"

    def create_wallet_address(self):
        """修复: 创建新地址（不删除旧地址）+ 保存到数据库"""
        nickname, ok = QInputDialog.getText(self, "新建地址", "请输入地址昵称（可选）:")
        
        if ok:
            try:
                new_address = self.generate_new_address()
                self.wallet.addresses.append(new_address)
                
                saved_to_db = False
                if self.database_connected and self.current_user['id'] > 0:
                    try:
                        addr_nickname = nickname.strip() if nickname.strip() else f"地址{len(self.wallet.addresses)}"
                        result = self.db.create_wallet_address(self.current_user['id'], addr_nickname)
                        if result and 'address' in result:
                            self.wallet.addresses[-1] = result['address']
                            new_address = result['address']
                            saved_to_db = True
                    except Exception as e:
                        print(f"保存到数据库失败: {e}")
                
                self.update_all_displays()
                
                info_msg = f"✅ 新地址创建成功！\n\n"
                info_msg += f"🔑 地址:\n{new_address}\n\n"
                if nickname.strip():
                    info_msg += f"📝 昵称: {nickname}\n\n"
                info_msg += f"📦 当前总地址数: {len(self.wallet.addresses)}\n"
                
                if saved_to_db:
                    info_msg += f"\n💾 已保存到数据库"
                else:
                    info_msg += f"\n⚠️ 仅保存在内存中（未保存到数据库）"
                
                QMessageBox.information(self, "成功", info_msg)
                
                print(f"\n✅ 新地址创建成功！")
                print(f"🔑 地址: {new_address}")
                if nickname.strip():
                    print(f"📝 昵称: {nickname}")
                print(f"📦 当前总地址数: {len(self.wallet.addresses)}")
                if saved_to_db:
                    print(f"💾 已保存到数据库")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建地址失败:\n{str(e)}")
                print(f"❌ 创建地址失败: {e}")

    def test_transaction(self):
        if len(self.wallet.addresses) < 2:
            QMessageBox.warning(self, "警告", "需要至少2个地址")
            return
        sender = self.wallet.addresses[0]
        receiver = self.wallet.addresses[1]
        if self.blockchain.get_balance(sender) > 1:
            tx = Transaction(sender, receiver, 1.0)
            if self.blockchain.add_transaction(tx):
                QMessageBox.information(self, "成功", "测试交易创建成功！")
                self.update_all_displays()
        else:
            QMessageBox.warning(self, "余额不足", "发送方余额不足")

    def show_about(self):
        text = """
        <h2>💰 BuptCoin 完整功能版</h2>
        <p><b>版本:</b> 5.0 (完美登录界面版)</p>
        <p><b>功能特性:</b></p>
        <ul>
            <li>✅ 🔥 超大登录界面（800×900）</li>
            <li>✅ 🔥 彻底消除按钮重叠</li>
            <li>✅ 用户登录注册系统</li>
            <li>✅ 多种交易类型（转账/质押/投票/合约）</li>
            <li>✅ 质押排名榜</li>
            <li>✅ 投票结果展示</li>
            <li>✅ 数据库管理功能</li>
            <li>✅ 富豪榜</li>
            <li>✅ 区块链浏览器</li>
            <li>✅ 实时数据更新</li>
            <li>✅ 余额同步功能</li>
        </ul>
        <p><b>最新优化 v5.0:</b></p>
        <ul>
            <li>🔥 窗口超大化：800×900</li>
            <li>🔥 标题字体：48px</li>
            <li>🔥 输入框高度：55px</li>
            <li>🔥 按钮高度：60px</li>
            <li>🔥 标签页高度：520px</li>
            <li>🔥 所有元素固定高度</li>
            <li>🔥 完美间距布局</li>
            <li>🔥 绝对不会重叠！</li>
        </ul>
        <p><b>开发:</b> 北邮区块链项目组</p>
        """
        QMessageBox.about(self, "关于 BuptCoin", text)

    def setup_timers(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all_displays)
        self.timer.start(5000)

    def show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '确认', "确定要退出吗？")
        if reply == QMessageBox.Yes:
            self.timer.stop()
            if self.mining_worker and self.mining_worker.isRunning():
                self.mining_worker.stop()
                self.mining_worker.wait()
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    app.setApplicationName("BuptCoin Enhanced")
    app.setApplicationVersion("5.0")
    
    try:
        gui = BlockchainGUIEnhanced()
        gui.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "错误", f"启动失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
