"""
Markdown 文档解析器
支持解析 API 文档的 Markdown 格式，包括：
- 叙述性中文接口文档（请求路径/请求方法/业务参数/返回值 data/字段说明）
- Markdown 表格格式
- 简易 API 文档格式
"""

import re
import json
from typing import Dict, List, Any, Optional


class MarkdownParser:
    """Markdown API 文档解析器"""

    def __init__(self, content: str):
        self.raw_content = content
        self.lines = [line.rstrip() for line in content.split('\n')]

    def parse(self) -> List[Dict[str, Any]]:
        """解析并返回接口列表"""
        if self._is_narrative_api_doc():
            return self._parse_narrative()
        if self._is_api_doc_format():
            return self._parse_api_doc()
        return self._parse_markdown_table()

    # ---------- 格式检测 ----------

    def _is_narrative_api_doc(self) -> bool:
        """检测是否为叙述性中文接口文档"""
        content = self.raw_content
        markers = ['请求路径', '请求方法', '业务参数', '返回值 data', '字段说明',
                   '返回值Data', '请求路径：', '请求方法：']
        return any(m in content for m in markers)

    def _is_api_doc_format(self) -> bool:
        """检测是否为 API 文档格式"""
        content = self.raw_content.lower()
        api_markers = ['接口路径', '请求参数', '响应参数', '接口描述',
                       'method', 'endpoint', 'request body', 'response']
        return any(marker.lower() in content for marker in api_markers)

    # ---------- 叙述性格式解析 ----------

    def _parse_narrative(self) -> List[Dict]:
        """解析叙述性中文接口文档"""
        apis = []
        current = None
        i = 0
        n = len(self.lines)

        # 用于识别接口标题：以 ## 开头且包含数字点 或 常见 HTTP 方法
        section_re = re.compile(r'^#{2,4}\s*\d*[\.\、\s]*\s*(.*?)$')

        while i < n:
            line = self.lines[i]
            stripped = line.strip()

            # 检测接口标题（## / ### / #### 且看起来是接口标题）
            m = section_re.match(stripped)
            if m:
                title = m.group(1).strip().replace('\\', '')
                # 保存上一个
                if current and current.get('path'):
                    apis.append(self._finalize_api(current))
                current = self._new_api(title)
                i += 1
                continue

            if current is None:
                i += 1
                continue

            # 请求路径 / 接口路径
            path_match = re.search(r'(?:请求路径|接口路径|URL|Endpoint)\s*[：:]\s*(/[^\s（\(]*)', stripped, re.I)
            if path_match:
                current['path'] = path_match.group(1).strip()
                current['url'] = current['path']
                i += 1
                continue

            # 请求方法
            method_match = re.search(r'(?:请求方法|方法|Method)\s*[：:]\s*(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)', stripped, re.I)
            if method_match:
                current['method'] = method_match.group(1).upper()
                i += 1
                continue
            # 裸方法（如 "- 请求方法：GET" 没匹配到，再兜底）
            if not current.get('method'):
                bare_method = re.search(r'\b(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\b', stripped, re.I)
                if bare_method and ('请求' in stripped or '方法' in stripped or 'method' in stripped.lower()):
                    current['method'] = bare_method.group(1).upper()

            # 业务参数 / 请求参数 / 请求体
            if re.search(r'^(?:业务参数|请求参数|请求体|Request Body|入参)\s*[：:：]?', stripped, re.I):
                # 如果明确写“无/空/{}”，直接跳过
                if re.search(r'[：:]\s*(无|空|\\?\{\s*\\?\})', stripped, re.I):
                    i += 1
                    continue
                # 跳过当前行，读取后续 JSON 代码块或行内 JSON
                body_lines = []
                i += 1
                in_code = False
                while i < n:
                    l = self.lines[i]
                    if l.strip().startswith('```'):
                        in_code = not in_code
                        i += 1
                        continue
                    if in_code:
                        body_lines.append(l)
                        i += 1
                        continue
                    # 非代码块且遇到新章节则结束
                    if l.strip().startswith('#') or re.search(r'^(?:返回值|返回|响应|字段说明)', l.strip(), re.I):
                        break
                    # 只收集看起来像 JSON 或列表内容的行
                    if l.strip() and (l.strip().startswith('{') or l.strip().startswith('"') or l.strip().startswith('-')):
                        body_lines.append(l)
                    i += 1
                raw_body = '\n'.join(body_lines).strip()
                current['request_body'] = self._extract_json(raw_body) or raw_body
                continue

            # 返回值 data / 响应
            if re.search(r'^(?:返回值|返回|响应|Response)\s*(?:data|Data|值|参数)?\s*[：:：]?', stripped, re.I):
                resp_lines = []
                i += 1
                in_code = False
                while i < n:
                    l = self.lines[i]
                    if l.strip().startswith('```'):
                        in_code = not in_code
                        i += 1
                        continue
                    if in_code:
                        resp_lines.append(l)
                        i += 1
                        continue
                    if l.strip().startswith('#') or re.search(r'^(?:字段说明|响应参数|请求路径|请求方法|业务参数)', l.strip(), re.I):
                        break
                    i += 1
                raw_resp = '\n'.join(resp_lines).strip()
                current['response_example'] = self._extract_json(raw_resp)
                continue

            # 字段说明
            if re.search(r'^(?:字段说明|参数说明|响应字段|参数名)', stripped, re.I):
                params, i = self._parse_field_description(i)
                if params:
                    current['parameters'].extend(params)
                continue

            i += 1

        if current and current.get('path'):
            apis.append(self._finalize_api(current))

        return apis

    def _new_api(self, title: str) -> Dict:
        return {
            'name': title,
            'method': None,
            'path': None,
            'url': None,
            'description': title,
            'parameters': [],
            'request_body': None,
            'response_example': None,
            'responses': []
        }

    def _finalize_api(self, api: Dict) -> Dict:
        if not api.get('method'):
            api['method'] = 'GET'
        if not api.get('name') or api['name'] == api.get('path', ''):
            api['name'] = f"{api['method']} {api['path']}"
        api['description'] = api.get('description', api['name'])
        # responses 放一个 200 示例
        if api.get('response_example'):
            api['responses'] = {
                '200': {
                    'description': 'OK',
                    'schemas': [{'content_type': 'application/json', 'schema': api['response_example']}]
                }
            }
        # request_body 统一结构
        if api.get('request_body') and not isinstance(api['request_body'], dict):
            api['request_body'] = {
                'type': 'object',
                'content_type': 'application/json',
                'schema': api['request_body']
            }
        return api

    def _extract_json(self, text: str) -> Optional[Any]:
        """从文本中提取 JSON 对象"""
        text = text.strip()
        if not text:
            return None
        # 去除 ```json / ``` 标记
        text = re.sub(r'^```\w*', '', text)
        text = re.sub(r'```$', '', text)
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _parse_field_description(self, start_idx: int) -> (List[Dict], int):
        """解析字段说明段落（支持表格或列表）"""
        params = []
        i = start_idx + 1
        n = len(self.lines)

        # 先看是不是表格
        if i < n and '|' in self.lines[i]:
            return self._parse_param_table(i)

        # 否则按列表解析：- 字段名 (类型)：说明 或 - 字段名：说明
        while i < n:
            line = self.lines[i].strip()
            if not line or line.startswith('#') or re.search(r'^(?:请求路径|请求方法|业务参数|返回值)', line, re.I):
                break
            if line.startswith('-') or line.startswith('*'):
                content = line[1:].strip()
                # 字段名 (类型)：说明
                m = re.match(r'^([^\(（：:]+)\s*[\(（]([^\)）]+)[\)）]\s*[：:]?\s*(.*)$', content)
                if m:
                    params.append({
                        'name': m.group(1).strip(),
                        'type': m.group(2).strip(),
                        'description': m.group(3).strip(),
                        'required': '必填' in m.group(3) or '必须' in m.group(3)
                    })
                else:
                    # 字段名：说明
                    if '：' in content or ':' in content:
                        k, v = re.split(r'[：:]', content, 1)
                        params.append({
                            'name': k.strip(),
                            'type': 'string',
                            'description': v.strip(),
                            'required': '必填' in v or '必须' in v
                        })
            i += 1
        return params, i

    def _parse_param_table(self, start_idx: int) -> (List[Dict], int):
        """解析参数表格"""
        params = []
        i = start_idx
        n = len(self.lines)
        headers = []

        # 表头
        if i < n and '|' in self.lines[i]:
            headers = [h.strip().lower() for h in self.lines[i].split('|') if h.strip()]
            i += 1
        # 跳过分隔线
        if i < n and re.match(r'^\s*\|?[\s\-:|]+\|?\s*$', self.lines[i]):
            i += 1

        name_idx = self._find_header_index(headers, ['参数名', '字段名', '字段', '参数', 'name'])
        type_idx = self._find_header_index(headers, ['类型', 'type'])
        desc_idx = self._find_header_index(headers, ['说明', '描述', '含义', 'description'])
        req_idx = self._find_header_index(headers, ['必填', '是否必填', 'required'])

        while i < n:
            line = self.lines[i].strip()
            if not line or '|' not in line:
                break
            cells = [c.strip() for c in line.split('|')]
            if len(cells) < 2:
                i += 1
                continue
            param = {
                'name': cells[name_idx] if name_idx < len(cells) else '',
                'type': cells[type_idx] if type_idx < len(cells) else 'string',
                'description': cells[desc_idx] if desc_idx < len(cells) else '',
                'required': False
            }
            if req_idx < len(cells):
                param['required'] = cells[req_idx].lower() in ('是', 'true', '必填', 'yes')
            if param['name']:
                params.append(param)
            i += 1
        return params, i

    def _find_header_index(self, headers: List[str], candidates: List[str]) -> int:
        for c in candidates:
            for idx, h in enumerate(headers):
                if c in h:
                    return idx
        return 0

    # ---------- 旧版简易 API 文档解析 ----------

    def _parse_api_doc(self) -> List[Dict]:
        """解析 API 文档格式"""
        apis = []
        current_api = {}

        i = 0
        while i < len(self.lines):
            line = self.lines[i].strip()

            if line.startswith('## ') or line.startswith('### '):
                if current_api and current_api.get('method'):
                    apis.append(current_api)
                current_api = {'description': '', 'parameters': [], 'responses': []}
                title = line.replace('##', '').replace('###', '').strip()
                method_match = re.search(r'(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s*[-–]\s*(.+)', title, re.I)
                if method_match:
                    current_api['method'] = method_match.group(1).upper()
                    current_api['name'] = method_match.group(2).strip()
                else:
                    current_api['name'] = title
                    current_api['method'] = 'GET'

            path_match = re.search(r'[接口路径|Endpoint|URL]*[:：]?\s*(/[^\s]*)', line, re.I)
            if path_match:
                current_api['url'] = path_match.group(1)
                current_api['path'] = path_match.group(1)

            if '参数名' in line or '参数' in line and '|' in line:
                param_table, i = self._parse_param_table(i)
                if param_table:
                    current_api['parameters'] = param_table

            if '响应' in line and '|' in line:
                response_table, i = self._parse_param_table(i)
                if response_table:
                    current_api['responses'] = response_table

            i += 1

        if current_api and current_api.get('method'):
            apis.append(current_api)

        return apis

    def _parse_markdown_table(self) -> List[Dict]:
        """解析 Markdown 表格格式"""
        apis = []
        in_table = False
        headers = []
        current_row = {}

        for line in self.lines:
            line = line.strip()

            if '|' in line and not in_table:
                headers = [h.strip() for h in line.split('|') if h.strip()]
                in_table = True
                continue

            if in_table and re.match(r'^[\-| ]+$', line):
                continue

            if in_table and '|' not in line:
                if current_row:
                    apis.append(current_row)
                in_table = False
                current_row = {}
                continue

            if in_table and '|' in line:
                cells = [c.strip() for c in line.split('|')]
                for idx, header in enumerate(headers):
                    if idx < len(cells):
                        current_row[header.lower()] = cells[idx]
                if current_row.get('method') or current_row.get('url'):
                    apis.append(current_row)
                current_row = {}

        return apis

    def get_info(self) -> Dict:
        """获取文档信息"""
        return {
            'title': self._extract_title(),
            'api_count': len(self.parse()),
            'format': 'narrative' if self._is_narrative_api_doc() else ('api_doc' if self._is_api_doc_format() else 'table')
        }

    def _extract_title(self) -> str:
        """提取标题"""
        for line in self.lines[:10]:
            if line.startswith('# '):
                return line.replace('#', '').strip()
        return 'Unknown'


# 便捷函数
def parse_markdown(content: str) -> List[Dict]:
    """解析 Markdown API 文档"""
    return MarkdownParser(content).parse()
