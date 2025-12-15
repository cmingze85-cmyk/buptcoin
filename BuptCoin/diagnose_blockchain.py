#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区块链诊断工具
用于深度检查区块链验证失败的原因
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blockchain import Blockchain
from utils import Utils
import json

def diagnose_blockchain():
    print("\n" + "="*80)
    print("🔍 区块链深度诊断工具")
    print("="*80 + "\n")
    
    # 创建区块链实例
    print("步骤 1: 创建区块链实例...")
    blockchain = Blockchain(difficulty=2)
    print(f"✅ 区块链创建完成，当前区块数: {len(blockchain.chain)}\n")
    
    # 检查每个区块
    print("步骤 2: 逐个检查区块...\n")
    
    for i, block in enumerate(blockchain.chain):
        print(f"\n{'='*80}")
        print(f"🔷 区块 #{block.index}")
        print(f"{'='*80}")
        
        # 基本信息
        print(f"\n📊 基本信息:")
        print(f"  索引: {block.index}")
        print(f"  时间戳: {block.timestamp}")
        print(f"  Nonce: {block.nonce}")
        print(f"  交易数: {len(block.transactions)}")
        
        # 哈希信息
        print(f"\n🔑 哈希信息:")
        print(f"  存储的哈希: {block.hash}")
        print(f"  前驱哈希:   {block.previous_hash}")
        
        # 重新计算哈希
        calculated_hash = block.calculate_hash()
        print(f"  计算的哈希: {calculated_hash}")
        
        # 对比哈希
        if block.hash == calculated_hash:
            print(f"  ✅ 哈希匹配")
        else:
            print(f"  ❌ 哈希不匹配！")
            print(f"  \n  差异分析:")
            print(f"    存储: {block.hash[:40]}...")
            print(f"    计算: {calculated_hash[:40]}...")
        
        # 检查工作量证明
        print(f"\n⛏️ 工作量证明:")
        required_prefix = '0' * blockchain.difficulty
        actual_prefix = block.hash[:blockchain.difficulty]
        print(f"  要求前缀: {required_prefix}")
        print(f"  实际前缀: {actual_prefix}")
        
        if actual_prefix == required_prefix:
            print(f"  ✅ 工作量证明有效")
        else:
            print(f"  ❌ 工作量证明无效！")
        
        # 检查前驱哈希
        if i > 0:
            print(f"\n🔗 链接验证:")
            previous_block = blockchain.chain[i-1]
            print(f"  前一个区块的哈希: {previous_block.hash}")
            print(f"  当前区块的前驱: {block.previous_hash}")
            
            if block.previous_hash == previous_block.hash:
                print(f"  ✅ 前驱哈希匹配")
            else:
                print(f"  ❌ 前驱哈希不匹配！")
        
        # 打印交易信息
        print(f"\n💸 交易列表:")
        for j, tx in enumerate(block.transactions):
            print(f"  [{j}] {tx.sender} -> {tx.receiver}: {tx.amount} ({tx.transaction_type})")
        
        # 打印原始数据（用于调试）
        print(f"\n📦 原始数据结构:")
        block_data = {
            'index': block.index,
            'timestamp': block.timestamp,
            'transactions': [tx.to_dict() for tx in block.transactions],
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
            'merkle_root': block.merkle_tree.get_root()
        }
        print(f"  {json.dumps(block_data, indent=2, ensure_ascii=False)[:300]}...")
    
    # 执行官方验证
    print(f"\n\n{'='*80}")
    print("步骤 3: 执行官方验证...")
    print(f"{'='*80}\n")
    
    is_valid = blockchain.is_chain_valid()
    
    print(f"\n\n{'='*80}")
    print("📊 诊断总结")
    print(f"{'='*80}")
    print(f"区块总数: {len(blockchain.chain)}")
    print(f"验证结果: {'\u2705 通过' if is_valid else '\u274c 失败'}")
    print(f"{'='*80}\n")
    
    # 如果验证失败，给出建议
    if not is_valid:
        print("💡 问题解决建议:")
        print("\n1. 删除数据库重新开始:")
        print("   cd D:\\pyqt5\\BuptCoin")
        print("   del buptcoin.db  # Windows")
        print("   rm buptcoin.db   # Linux/Mac")
        print("   python BuptCoin/main.py")
        print("\n2. 检查是否修改过难度值")
        print("\n3. 检查是否手动修改过数据库")
        print("\n4. 查看上面的详细诊断信息，找出具体哪个区块有问题\n")

if __name__ == "__main__":
    try:
        diagnose_blockchain()
    except Exception as e:
        print(f"\n\u274c 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()
