# network.py - 创建新文件
import socket
import threading
import json
import time

class P2PNode:
    def __init__(self, host='127.0.0.1', port=5000, bootstrap_nodes=None):
        self.host = host
        self.port = port
        self.peers = bootstrap_nodes or []
        self.server_socket = None
        self.running = False
        self.message_handlers = {}
        self.peer_manager = PeerManager()  # <-- 添加这行

        # 从 blockchain.py 导入
        from blockchain import Blockchain
        self.blockchain = Blockchain()

        # 注册消息处理器 <-- 添加这行
        self.register_handlers()  # <-- 添加这行

    def register_handlers(self):
        """注册消息处理器"""
        self.message_handlers = {
            'hello': self.handle_hello,
            'transaction': self.handle_transaction,
            'get_chain': self.handle_get_chain,
            'new_block': self.handle_new_block,
            'get_peers': self.handle_get_peers,
            'stake': self.handle_stake,
            'vote': self.handle_vote,
            'contract': self.handle_contract
        }

    def handle_new_block(self, message, client_socket):
        """处理新区块消息"""
        block_data = message.get('block', {})
        from blockchain import Block, Transaction

        # 重构区块对象
        transactions = []
        for tx_data in block_data.get('transactions', []):
            tx = Transaction(
                tx_data['sender'],
                tx_data['receiver'],
                tx_data['amount'],
                tx_data.get('type', 'transfer'),
                tx_data.get('data', '')
            )
            transactions.append(tx)

        new_block = Block(
            block_data['index'],
            transactions,
            block_data['previous_hash'],
            block_data['timestamp'],
            block_data['nonce']
        )
        new_block.hash = block_data['hash']

        # 验证并添加新区块
        if self.validate_and_add_block(new_block):
            print(f"新区块 #{new_block.index} 同步成功")
            # 广播给其他节点
            self.broadcast_block(new_block)

    def handle_get_peers(self, message, client_socket):
        """处理获取节点列表请求"""
        response = {
            'type': 'peers',
            'peers': self.peers
        }
        client_socket.send(json.dumps(response).encode('utf-8'))

    def handle_stake(self, message, client_socket):
        """处理质押交易"""
        stake_data = message.get('stake', {})
        print(f"收到质押交易: {stake_data}")

    def handle_vote(self, message, client_socket):
        """处理投票交易"""
        vote_data = message.get('vote', {})
        print(f"收到投票交易: {vote_data}")

    def handle_contract(self, message, client_socket):
        """处理合约交易"""
        contract_data = message.get('contract', {})
        print(f"收到合约交易: {contract_data}")

    def validate_and_add_block(self, block) -> bool:
        """验证并添加区块"""
        # 1. 验证工作量证明
        if block.hash[:self.blockchain.difficulty] != '0' * self.blockchain.difficulty:
            print(f"工作量证明验证失败")
            return False

        # 2. 验证区块哈希
        if block.hash != block.calculate_hash():
            print(f"区块哈希验证失败")
            return False

        # 3. 验证交易
        for tx in block.transactions:
            if not self.validate_transaction(tx):
                print(f"交易验证失败: {tx}")
                return False

        # 添加到区块链
        self.blockchain.chain.append(block)
        return True

    def validate_transaction(self, transaction) -> bool:
        """验证交易"""
        # 这里可以添加签名验证、余额检查等
        return True

    def broadcast_block(self, block):
        """广播新区块"""
        message = {
            'type': 'new_block',
            'block': block.to_dict()
        }
        self.broadcast(message)

    def discover_peers(self):
        """发现网络中的其他节点"""
        for peer_host, peer_port in self.peers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((peer_host, peer_port))

                # 发送发现请求
                discover_msg = {
                    'type': 'get_peers',
                    'peer': {
                        'host': self.host,
                        'port': self.port
                    }
                }
                sock.send(json.dumps(discover_msg).encode('utf-8'))

                # 接收响应
                response = sock.recv(4096).decode('utf-8')
                if response:
                    data = json.loads(response)
                    if data.get('type') == 'peers':
                        new_peers = data.get('peers', [])
                        for peer in new_peers:
                            if peer not in self.peers:
                                self.peers.append(peer)
                                print(f"发现新节点: {peer}")

                sock.close()
            except:
                continue

    def start(self):
        """启动节点服务器"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self.running = True
        print(f"P2P节点启动在 {self.host}:{self.port}")

        # 启动接受连接的线程
        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.start()

    def accept_connections(self):
        """接受其他节点的连接"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"新连接来自: {address}")

                # 为新连接创建处理线程
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.start()
            except:
                break

    def handle_client(self, client_socket, address):
        """处理客户端连接"""
        try:
            while True:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break

                message = json.loads(data)
                self.handle_message(message, client_socket)
        except:
            pass
        finally:
            client_socket.close()
            print(f"连接关闭: {address}")

    def handle_message(self, message, client_socket):
        """处理收到的消息"""
        msg_type = message.get('type')

        if msg_type == 'hello':
            self.handle_hello(message, client_socket)
        elif msg_type == 'transaction':
            self.handle_transaction(message)
        elif msg_type == 'get_chain':
            self.send_blockchain(client_socket)

    def handle_hello(self, message, client_socket):
        """处理新节点加入"""
        peer_info = message.get('peer', {})
        peer_host = peer_info.get('host', '')
        peer_port = peer_info.get('port', 0)

        if (peer_host, peer_port) not in self.peers:
            self.peers.append((peer_host, peer_port))
            print(f"新节点加入: {peer_host}:{peer_port}")

        # 发送响应
        response = {
            'type': 'welcome',
            'message': f'欢迎！当前有 {len(self.peers)} 个节点',
            'peers': self.peers
        }
        client_socket.send(json.dumps(response).encode('utf-8'))

    def handle_transaction(self, message):
        """处理新交易"""
        from blockchain import Transaction

        tx_data = message.get('transaction', {})
        tx = Transaction(
            tx_data.get('sender', ''),
            tx_data.get('receiver', ''),
            tx_data.get('amount', 0)
        )

        # 添加到本地区块链
        if self.blockchain.add_transaction(tx):
            print(f"收到并添加交易: {tx}")
            # 广播给其他节点
            self.broadcast(message)

    def connect_to_peer(self, host, port):
        """连接到其他节点"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))

            # 发送hello消息
            hello_msg = {
                'type': 'hello',
                'peer': {
                    'host': self.host,
                    'port': self.port
                }
            }
            sock.send(json.dumps(hello_msg).encode('utf-8'))

            # 接收响应
            response = sock.recv(4096).decode('utf-8')
            print(f"连接到 {host}:{port} 成功")

            sock.close()
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def broadcast(self, message):
        """广播消息给所有节点"""
        for peer_host, peer_port in self.peers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((peer_host, peer_port))
                sock.send(json.dumps(message).encode('utf-8'))
                sock.close()
            except:
                print(f"广播失败到 {peer_host}:{peer_port}")

    def send_blockchain(self, client_socket):
        """发送区块链数据"""
        chain_data = self.blockchain.to_dict()
        response = {
            'type': 'chain',
            'chain': chain_data
        }
        client_socket.send(json.dumps(response).encode('utf-8'))

    def sync_blockchain(self):
        """从其他节点同步区块链"""
        for peer in self.peers:
            try:
                # 请求最新区块链
                chain_data = self.request_chain_from_peer(peer)
                # 验证并合并区块链
                self.merge_blockchain(chain_data)
            except Exception as e:
                print(f"同步失败 {peer}: {e}")


class PeerManager:
    """节点管理器"""

    def __init__(self):
        self.peers = []
        self.active_connections = {}

    def add_peer(self, host, port):
        """添加节点"""
        if (host, port) not in self.peers:
            self.peers.append((host, port))
            return True
        return False

    def remove_peer(self, host, port):
        """移除节点"""
        if (host, port) in self.peers:
            self.peers.remove((host, port))
            return True
        return False

    def get_active_peers(self):
        """获取活跃节点"""
        return [peer for peer in self.peers if self.is_peer_active(peer)]

    def is_peer_active(self, peer):
        """检查节点是否活跃"""
        host, port = peer
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((host, port))
            sock.close()
            return True
        except:
            return False