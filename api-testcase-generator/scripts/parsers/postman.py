"""
Postman Collection 解析器
支持解析 Postman 导出的 JSON 格式接口集合
"""

import json
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin


class PostmanParser:
    """Postman 集合解析器"""

    SUPPORTED_VERSIONS = ['2.0', '2.1.0']

    def __init__(self, content: str):
        """
        初始化解析器

        Args:
            content: Postman JSON 内容或文件路径
        """
        self.raw_data = self._load_data(content)
        self.info = self.raw_data.get('info', {})
        self.items = self.raw_data.get('item', [])
        self.variables = self._extract_variables()

    def _load_data(self, content: str) -> Dict:
        """加载 JSON 数据"""
        try:
            # 尝试作为 JSON 字符串解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试作为文件路径读取
            with open(content, 'r', encoding='utf-8') as f:
                return json.load(f)

    def _extract_variables(self) -> Dict[str, str]:
        """提取环境变量"""
        variables = {}
        for item in self.items:
            if isinstance(item, dict) and 'variable' in item:
                for var in item['variable']:
                    if 'key' in var and 'value' in var:
                        variables[var['key']] = var['value']
        return variables

    def parse(self) -> List[Dict[str, Any]]:
        """
        解析并返回接口列表

        Returns:
            接口列表，每项包含 name, method, url, headers, body 等
        """
        apis = []
        self._parse_items(self.items, apis)
        return apis

    def _parse_items(self, items: List[Any], apis: List[Dict], base_path: str = ''):
        """递归解析接口项"""
        for item in items:
            if not isinstance(item, dict):
                continue

            # 处理文件夹
            if 'item' in item and len(item['item']) > 0:
                folder_name = item.get('name', '')
                new_base_path = f"{base_path}/{folder_name}".strip('/')
                self._parse_items(item['item'], apis, new_base_path)
                continue

            # 解析请求
            request = item.get('request', {})
            if not request:
                continue

            api = self._parse_request(request, item.get('name', ''), base_path)
            if api:
                apis.append(api)

    def _parse_request(self, request: Dict, name: str, base_path: str) -> Optional[Dict]:
        """解析单个请求"""
        method = request.get('method', 'GET')

        url_info = request.get('url', {})
        if isinstance(url_info, dict):
            raw_url = url_info.get('raw', '')
            path_parts = url_info.get('path', [])
            host = url_info.get('host', [])
            query = url_info.get('query', [])
        else:
            raw_url = url_info
            path_parts = []
            query = []

        # 构建完整 URL
        if raw_url:
            full_url = raw_url
        else:
            base_url = '/'.join(host) if host else ''
            path = '/'.join(path_parts) if path_parts else base_path
            full_url = f"{base_url}/{path}".strip('/')

        # 解析 headers
        headers = self._parse_headers(request.get('header', []))

        # 解析 body
        body = self._parse_body(request.get('body', {}))

        # 解析 query params
        query_params = []
        for q in query:
            if isinstance(q, dict):
                query_params.append({
                    'key': q.get('key', ''),
                    'value': q.get('value', ''),
                    'type': q.get('type', 'text'),
                    'required': q.get('description', '') == 'required'
                })

        # 解析前置/后置脚本
        test_script = self._parse_script(request.get('event', []), 'test')
        prequest_script = self._parse_script(request.get('event', []), 'prerequest')

        return {
            'name': name,
            'method': method,
            'url': full_url,
            'path': full_url,
            'headers': headers,
            'body': body,
            'query_params': query_params,
            'test_script': test_script,
            'prequest_script': prequest_script,
            'description': self.info.get('description', '')
        }

    def _parse_headers(self, headers: List[Dict]) -> List[Dict]:
        """解析请求头"""
        result = []
        for h in headers:
            if isinstance(h, dict) and not h.get('disabled', False):
                result.append({
                    'key': h.get('key', ''),
                    'value': h.get('value', ''),
                    'type': h.get('type', 'text'),
                    'description': h.get('description', '')
                })
        return result

    def _parse_body(self, body: Dict) -> Dict:
        """解析请求体"""
        mode = body.get('mode', '')

        if mode == 'formdata':
            fields = []
            for item in body.get('formdata', []):
                if isinstance(item, dict) and not item.get('disabled', False):
                    fields.append({
                        'key': item.get('key', ''),
                        'type': item.get('type', 'text'),
                        'value': item.get('value', ''),
                        'description': item.get('description', '')
                    })
            return {'type': 'form-data', 'fields': fields}

        elif mode == 'urlencoded':
            fields = []
            for item in body.get('urlencoded', []):
                if isinstance(item, dict) and not item.get('disabled', False):
                    fields.append({
                        'key': item.get('key', ''),
                        'value': item.get('value', ''),
                        'description': item.get('description', '')
                    })
            return {'type': 'x-www-form-urlencoded', 'fields': fields}

        elif mode == 'raw':
            raw_data = body.get('raw', '')
            options = body.get('options', {}).get('raw', {})
            language = options.get('language', 'text')
            return {
                'type': 'raw',
                'content': raw_data,
                'content_type': f"application/{language}" if language in ['json', 'xml'] else 'text/plain'
            }

        elif mode == 'file':
            return {
                'type': 'file',
                'src': body.get('src', ''),
                'content': body.get('content', '')
            }

        return {'type': 'none', 'fields': [], 'content': ''}

    def _parse_script(self, events: List[Dict], listen_type: str) -> str:
        """解析脚本"""
        for event in events:
            if event.get('listen') == listen_type:
                script = event.get('script', {})
                if isinstance(script, dict):
                    exec_list = script.get('exec', [])
                    if isinstance(exec_list, list):
                        return '\n'.join(exec_list)
                    return exec_list if isinstance(exec_list, str) else ''
                return script.get('exec', '')
        return ''

    def get_collection_info(self) -> Dict:
        """获取集合信息"""
        return {
            'name': self.info.get('name', 'Unknown'),
            'description': self.info.get('description', ''),
            'schema': self.info.get('schema', ''),
            'api_count': len(self.items),
            'variables': self.variables
        }


# 便捷函数
def parse_postman(content: str) -> List[Dict]:
    """解析 Postman 集合"""
    return PostmanParser(content).parse()
