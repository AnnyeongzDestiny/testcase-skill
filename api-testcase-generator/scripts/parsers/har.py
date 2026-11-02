"""
HAR (HTTP Archive) 格式解析器
支持解析浏览器网络请求导出的 HAR 文件
"""

import json
from typing import Dict, List, Any, Optional


class HarParser:
    """HAR 格式解析器"""

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
        """解析并返回请求列表"""
        apis = []

        entries = self.raw_data.get('log', {}).get('entries', [])

        for entry in entries:
            request = entry.get('request', {})
            response = entry.get('response', {})

            url = request.get('url', '')
            method = request.get('method', 'GET')

            # 解析请求头
            headers = self._parse_headers(request.get('headers', []))

            # 解析查询参数
            query_string = request.get('queryString', [])

            # 解析请求体
            post_data = request.get('postData', {})
            if post_data:
                body = {
                    'type': post_data.get('mimeType', 'text/plain'),
                    'content': post_data.get('text', '')
                }
            else:
                body = {'type': 'none', 'content': ''}

            # 解析响应
            status = response.get('status', 0)
            response_headers = self._parse_headers(response.get('headers', []))

            # 解析 cookie
            cookies = self._parse_cookies(response.get('cookies', []))

            apis.append({
                'name': f"{method} {url.split('?')[0][:50]}",
                'method': method,
                'url': url,
                'path': url.split('?')[0],
                'description': f"Status: {status}",
                'headers': headers,
                'query_params': query_string,
                'body': body,
                'response': {
                    'status': status,
                    'headers': response_headers,
                    'cookies': cookies
                }
            })

        return apis

    def _parse_headers(self, headers: List) -> List[Dict]:
        """解析请求/响应头"""
        return [{'name': h.get('name', ''), 'value': h.get('value', '')}
                for h in headers if isinstance(h, dict)]

    def _parse_cookies(self, cookies: List) -> List[Dict]:
        """解析 Cookie"""
        return [{'name': c.get('name', ''), 'value': c.get('value', '')}
                for c in cookies if isinstance(c, dict)]

    def get_info(self) -> Dict:
        """获取信息"""
        return {
            'title': self.raw_data.get('log', {}).get('creator', {}).get('name', 'Unknown'),
            'request_count': len(self.raw_data.get('log', {}).get('entries', []))
        }


# 便捷函数
def parse_har(content: str) -> List[Dict]:
    """解析 HAR 格式"""
    return HarParser(content).parse()
