import hashlib
import json
import time
from typing import Any, Dict


class Utils:
    """工具类，提供哈希计算、时间戳等功能"""

    @staticmethod
    def calculate_hash(data: Any) -> str:
        """
        计算数据的SHA256哈希值

        Args:
            data: 任意可JSON序列化的数据

        Returns:
            str: 十六进制哈希字符串
        """
        if isinstance(data, dict):
            # 确保字典有序，使哈希计算稳定
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        return hashlib.sha256(data_str.encode()).hexdigest()

    @staticmethod
    def get_current_timestamp() -> int:
        """获取当前时间戳（秒）"""
        return int(time.time())

    @staticmethod
    def format_data(data: Any) -> str:
        """格式化数据为可读字符串"""
        return json.dumps(data, indent=2, ensure_ascii=False)