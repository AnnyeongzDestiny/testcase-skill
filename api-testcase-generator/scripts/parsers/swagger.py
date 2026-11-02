"""
Swagger/OpenAPI 解析器
支持解析 OpenAPI 2.0 (Swagger) 和 3.0 格式
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin


class SwaggerParser:
    """Swagger/OpenAPI 解析器"""

    def __init__(self, content: str):
        """
        初始化解析器

        Args:
            content: OpenAPI/Swagger JSON/YAML 内容或文件路径
        """
        self.raw_data = self._load_data(content)
        self.spec_version = self._detect_version()

    def _load_data(self, content: str) -> Dict:
        """加载数据"""
        if isinstance(content, str) and os.path.exists(content):
            with open(content, 'r', encoding='utf-8') as f:
                content = f.read()

        try:
            # 尝试作为 JSON 解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试作为 YAML 解析
            import yaml
            return yaml.safe_load(content)

    def _detect_version(self) -> str:
        """检测 OpenAPI 版本"""
        if 'openapi' in self.raw_data:
            return self.raw_data['openapi'][:3]  # 3.0, 3.1
        if 'swagger' in self.raw_data:
            return '2.0'
        return 'unknown'

    def parse(self) -> List[Dict[str, Any]]:
        """解析并返回接口列表"""
        if self.spec_version.startswith('3'):
            return self._parse_openapi3()
        elif self.spec_version == '2.0':
            return self._parse_swagger2()
        else:
            return self._parse_openapi3()  # 默认尝试 3.0 解析

    def _parse_openapi3(self) -> List[Dict]:
        """解析 OpenAPI 3.x"""
        apis = []

        # 获取基础信息
        info = self.raw_data.get('info', {})
        servers = self.raw_data.get('servers', [])
        base_path = self._extract_base_path(servers)

        # 解析 paths
        paths = self.raw_data.get('paths', {})
        components = self.raw_data.get('components', {})
        schemas = components.get('schemas', {})
        security_schemes = components.get('securitySchemes', {})

        for path, path_item in paths.items():
            if not path_item:
                continue

            # 解析每个 HTTP 方法
            for method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                if method not in path_item:
                    continue

                operation = path_item[method]
                full_url = self._build_url(base_path, path, servers)

                api = self._parse_operation(
                    operation=operation,
                    method=method,
                    path=path,
                    full_url=full_url,
                    path_params=path_item.get('parameters', []),
                    tags=operation.get('tags', []),
                    summary=operation.get('summary', ''),
                    description=operation.get('description', ''),
                    deprecated=operation.get('deprecated', False),
                    schemas=schemas,
                    security_schemes=security_schemes
                )
                if api:
                    apis.append(api)

        return apis

    def _parse_swagger2(self) -> List[Dict]:
        """解析 Swagger 2.0"""
        apis = []

        info = self.raw_data.get('info', {})
        base_path = self.raw_data.get('basePath', '')
        servers = self.raw_data.get('host', '')
        schemes = self.raw_data.get('schemes', ['https'])

        paths = self.raw_data.get('paths', {})

        for path, path_item in paths.items():
            if not path_item:
                continue

            for method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                if method not in path_item:
                    continue

                operation = path_item[method]
                full_url = f"{schemes[0] if schemes else 'https'}://{servers}{base_path}{path}".rstrip('/')

                api = self._parse_operation(
                    operation=operation,
                    method=method,
                    path=path,
                    full_url=full_url,
                    path_params=path_item.get('parameters', []),
                    tags=operation.get('tags', []),
                    summary=operation.get('summary', ''),
                    description=operation.get('description', ''),
                    deprecated=operation.get('deprecated', False),
                    schemas=self.raw_data.get('definitions', {}),
                    security_schemes=self.raw_data.get('securityDefinitions', {})
                )
                if api:
                    apis.append(api)

        return apis

    def _parse_operation(self, operation: Dict, method: str, path: str,
                         full_url: str, path_params: List, tags: List,
                         summary: str, description: str, deprecated: bool,
                         schemas: Dict, security_schemes: Dict) -> Optional[Dict]:
        """解析单个操作"""

        # 提取参数
        parameters = self._extract_parameters(operation.get('parameters', []), path_params)

        # 提取请求体
        request_body = self._extract_request_body(operation.get('requestBody', {}), schemas)

        # 提取响应
        responses = self._extract_responses(operation.get('responses', {}), schemas)

        # 提取安全要求
        security = self._extract_security(operation.get('security', []), security_schemes)

        # 解析标签
        tag = tags[0] if tags else 'Default'

        return {
            'name': summary or f"{method.upper()} {path}",
            'method': method.upper(),
            'url': full_url,
            'path': path,
            'tag': tag,
            'deprecated': deprecated,
            'description': description or summary,
            'parameters': parameters,
            'request_body': request_body,
            'responses': responses,
            'security': security,
            'operation_id': operation.get('operationId', ''),
            'tags': tags
        }

    def _extract_base_path(self, servers: List[Dict]) -> str:
        """提取基础路径"""
        if not servers:
            return ''
        first_server = servers[0]
        url = first_server.get('url', '')
        # 移除变量部分
        return re.sub(r'\{[^}]+\}', '', url).rstrip('/')

    def _build_url(self, base_path: str, path: str, servers: List[Dict]) -> str:
        """构建完整 URL"""
        if not servers:
            return f"{base_path}{path}".rstrip('/')

        first_server = servers[0]
        base_url = first_server.get('url', '{baseUrl}')

        # 替换路径变量
        if '{baseUrl}' in base_url:
            base_url = base_url.replace('{baseUrl}', '')

        return f"{base_url.rstrip('/')}{path}".rstrip('/')

    def _extract_parameters(self, parameters: List, path_params: List) -> List[Dict]:
        """提取参数列表"""
        all_params = []

        # 合并 path 和 operation 参数
        seen = set()

        for p in path_params:
            if isinstance(p, dict) and p.get('name'):
                param = {
                    'name': p.get('name', ''),
                    'in': p.get('in', 'query'),
                    'required': p.get('required', p.get('in') == 'path'),
                    'type': p.get('type', 'string'),
                    'description': p.get('description', ''),
                    'default': p.get('default', ''),
                    'enum': p.get('enum', [])
                }
                seen.add(p.get('name'))
                all_params.append(param)

        for p in parameters:
            if isinstance(p, dict) and p.get('name') and p.get('name') not in seen:
                param = {
                    'name': p.get('name', ''),
                    'in': p.get('in', 'query'),
                    'required': p.get('required', False),
                    'type': p.get('schema', {}).get('type', p.get('type', 'string')),
                    'description': p.get('description', ''),
                    'default': p.get('schema', {}).get('default', p.get('default', '')),
                    'enum': p.get('schema', {}).get('enum', p.get('enum', []))
                }
                seen.add(p.get('name'))
                all_params.append(param)

        return all_params

    def _extract_request_body(self, request_body: Dict, schemas: Dict) -> Dict:
        """提取请求体定义"""
        if not request_body:
            return {'type': 'none', 'content': None}

        content = request_body.get('content', {})
        for content_type, content_schema in content.items():
            schema = content_schema.get('schema', {})
            return {
                'type': 'object',
                'content_type': content_type,
                'schema': self._resolve_schema(schema, schemas)
            }

        return {'type': 'none', 'content': None}

    def _resolve_schema(self, schema: Dict, schemas: Dict) -> Dict:
        """解析 schema 引用"""
        if not schema:
            return {}

        # 处理 $ref
        if '$ref' in schema:
            ref = schema['$ref']
            ref_path = ref.replace('#/', '').split('/')
            for part in ref_path:
                if part in schemas:
                    return self._resolve_schema(schemas[part], schemas)
            return {'$ref': ref}

        # 递归处理嵌套 schema
        resolved = {}
        for key, value in schema.items():
            if key == 'properties' and isinstance(value, dict):
                resolved[key] = {
                    k: self._resolve_schema(v, schemas)
                    for k, v in value.items()
                }
            elif key == 'items' and isinstance(value, dict):
                resolved[key] = self._resolve_schema(value, schemas)
            else:
                resolved[key] = value

        return resolved

    def _extract_responses(self, responses: Dict, schemas: Dict) -> Dict:
        """提取响应定义"""
        result = {}
        for status, response in responses.items():
            content = response.get('content', {})
            description = response.get('description', '')

            schemas_list = []
            for content_type, content_schema in content.items():
                schema = content_schema.get('schema', {})
                if schema:
                    schemas_list.append({
                        'content_type': content_type,
                        'schema': self._resolve_schema(schema, schemas)
                    })

            result[status] = {
                'description': description,
                'schemas': schemas_list
            }

        return result

    def _extract_security(self, security: List, security_schemes: Dict) -> List[str]:
        """提取安全要求"""
        requirements = []
        for req in security:
            for scheme_name in req.keys():
                if scheme_name not in requirements:
                    requirements.append(scheme_name)
        return requirements

    def get_api_info(self) -> Dict:
        """获取 API 信息"""
        info = self.raw_data.get('info', {})
        return {
            'title': info.get('title', 'Unknown'),
            'version': info.get('version', 'Unknown'),
            'description': info.get('description', ''),
            'spec_version': self.spec_version,
            'api_count': len(self.raw_data.get('paths', {}))
        }


# 便捷函数
def parse_swagger(content: str) -> List[Dict]:
    """解析 Swagger/OpenAPI 文档"""
    return SwaggerParser(content).parse()
