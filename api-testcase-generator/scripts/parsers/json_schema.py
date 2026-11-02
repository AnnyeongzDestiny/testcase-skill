"""
JSON Schema 解析器
支持解析 JSON Schema 格式的接口定义
"""

import json
from typing import Dict, List, Any, Optional


class JsonSchemaParser:
    """JSON Schema 解析器"""

    def __init__(self, content: str):
        self.raw_data = self._load_data(content)

    def _load_data(self, content: str) -> Dict:
        """加载数据"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            with open(content, 'r', encoding='utf-8') as f:
                return json.load(f)

    def parse(self) -> List[Dict[str, Any]]:
        """解析并返回接口定义列表"""
        apis = []

        # 检查是否为 API 集合格式
        if 'paths' in self.raw_data:
            # OpenAPI 兼容格式
            for path, methods in self.raw_data.get('paths', {}).items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        apis.append({
                            'name': details.get('summary', f"{method.upper()} {path}"),
                            'method': method.upper(),
                            'url': path,
                            'path': path,
                            'description': details.get('description', ''),
                            'parameters': details.get('parameters', []),
                            'request_body': details.get('requestBody', {}),
                            'responses': details.get('responses', {})
                        })

        # 检查是否为单接口定义
        elif 'type' in self.raw_data:
            apis.append({
                'name': self.raw_data.get('title', 'Unknown'),
                'method': self.raw_data.get('method', 'GET').upper(),
                'url': self.raw_data.get('path', self.raw_data.get('endpoint', '')),
                'path': self.raw_data.get('path', ''),
                'description': self.raw_data.get('description', ''),
                'schema': self.raw_data
            })

        return apis

    def get_info(self) -> Dict:
        """获取信息"""
        return {
            'title': self.raw_data.get('title', 'Unknown'),
            'version': self.raw_data.get('version', 'Unknown'),
            'api_count': len(self.raw_data.get('paths', {})) if 'paths' in self.raw_data else 1
        }


# 便捷函数
def parse_json_schema(content: str) -> List[Dict]:
    """解析 JSON Schema 格式"""
    return JsonSchemaParser(content).parse()
