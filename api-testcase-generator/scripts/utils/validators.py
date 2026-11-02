"""
工具函数
"""

import re
from typing import Dict, List, Any


def validate_testcase(tc: Dict) -> tuple:
    """
    验证测试用例格式

    Args:
        tc: 测试用例字典

    Returns:
        (is_valid, errors)
    """
    errors = []

    # 必填字段检查
    if not tc.get('用例编号') and not tc.get('功能ID'):
        errors.append("缺少用例标识")

    if not tc.get('用例标题'):
        errors.append("缺少用例标题")

    # URL 格式检查
    if tc.get('请求URL'):
        url = tc.get('请求URL')
        if not url.startswith('/') and not url.startswith('http'):
            errors.append(f"请求URL格式错误: {url}")

    # 方法检查
    valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']
    if tc.get('请求类型') and tc.get('请求类型').upper() not in valid_methods:
        errors.append(f"请求方法无效: {tc.get('请求类型')}")

    return (len(errors) == 0, errors)


def parse_priority(priority_str: str) -> int:
    """
    解析优先级字符串为数字

    Args:
        priority_str: 优先级字符串 (P0, P1, P2, P3, High, Medium, Low)

    Returns:
        优先级数值 (0=最高, 3=最低)
    """
    priority_map = {
        'p0': 0, 'high': 0, '高': 0,
        'p1': 1, 'medium': 1, '中': 1,
        'p2': 2, 'low': 2, '低': 2,
        'p3': 3, ' lowest': 3
    }

    return priority_map.get(priority_str.lower(), 1)


def format_url(base_url: str, path: str) -> str:
    """
    格式化 URL

    Args:
        base_url: 基础 URL
        path: 路径

    Returns:
        完整的 URL
    """
    # 移除多余斜杠
    base = base_url.rstrip('/')
    path = path.strip('/')

    if path.startswith('http'):
        return path

    return f"{base}/{path}"


def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ""
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_json_string(s: str) -> Dict:
    """解析 JSON 字符串"""
    try:
        return __import__('json').loads(s)
    except:
        return {}


def generate_id(prefix: str = "") -> str:
    """生成唯一 ID"""
    import uuid
    return f"{prefix}{uuid.uuid4().hex[:8]}"


class Colors:
    """终端颜色"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

    @classmethod
    def print(cls, text: str, color: str = GREEN):
        print(f"{color}{text}{cls.RESET}")
