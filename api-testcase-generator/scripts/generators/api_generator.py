"""
API 测试用例生成器
根据 API 定义生成全面的接口测试用例
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class APITestGenerator:
    """API 测试用例生成器"""

    # HTTP 状态码分类
    STATUS_CODES = {
        'success': [200, 201, 204],
        'client_error': [400, 401, 403, 404, 405, 422],
        'server_error': [500, 502, 503, 504]
    }

    def __init__(self, base_url: str = "", module_name: str = "API"):
        self.base_url = base_url
        self.module_name = module_name
        self.testcase_id = 1
        self.testcases = []

    def generate(self, api: Dict[str, Any]) -> List[Dict]:
        """
        根据 API 定义生成测试用例

        Args:
            api: API 定义字典，包含 method, url, parameters, request_body 等

        Returns:
            测试用例列表
        """
        self.testcases = []
        api_name = api.get('name', self.module_name)
        method = api.get('method', 'GET')
        path = api.get('path', api.get('url', ''))
        full_url = api.get('url', path)
        parameters = api.get('parameters', [])
        request_body = api.get('request_body', {})
        responses = api.get('responses', {})

        # 生成正向测试用例
        self._generate_positive_tests(api_name, method, full_url, parameters, request_body, responses)

        # 生成反向测试用例
        self._generate_negative_tests(api_name, method, full_url, parameters, request_body)

        # 生成安全测试用例
        self._generate_security_tests(api_name, method, full_url, request_body)

        # 生成性能测试用例
        self._generate_performance_tests(api_name, method, full_url)

        return self.testcases

    def _generate_positive_tests(self, api_name: str, method: str, url: str,
                                  parameters: List, request_body: Dict, responses: Dict):
        """生成正向测试用例"""
        # P0: 正常请求
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}正常请求成功",
            priority="P0",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data=self._sample_body(request_body),
            expected_status=200,
            expected=self._sample_response(responses),
            category="正向"
        ))

        # P0: 必填参数
        required_params = [p for p in parameters if p.get('required', False)]
        if required_params:
            params = {p.get('name', ''): self._sample_value(p) for p in required_params}
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}仅传必填参数",
                priority="P0",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=json.dumps(params, ensure_ascii=False) if method in ['POST', 'PUT', 'PATCH'] else "",
                expected_status=200,
                expected='{"code": 0}',
                category="正向"
            ))

        # P1: 可选参数
        optional_params = [p for p in parameters if not p.get('required', False)]
        if optional_params:
            all_params = {p.get('name', ''): self._sample_value(p) for p in parameters}
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}传递全部参数",
                priority="P1",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=json.dumps(all_params, ensure_ascii=False) if method in ['POST', 'PUT', 'PATCH'] else "",
                expected_status=200,
                expected='{"code": 0, "data": {...}}',
                category="正向"
            ))

        # P1: 响应字段验证
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}响应字段完整性",
            priority="P1",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data=self._sample_body(request_body),
            expected_status=200,
            expected="响应包含所有预期字段",
            category="正向",
            remark="验证响应数据结构"
        ))

    def _generate_negative_tests(self, api_name: str, method: str, url: str,
                                  parameters: List, request_body: Dict):
        """生成反向测试用例"""
        # P0: 缺少必填参数
        required_params = [p for p in parameters if p.get('required', False)]
        if required_params:
            param = required_params[0]
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}缺少必填参数【{param.get('name', '')}】",
                priority="P0",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=self._body_without_field(request_body, param.get('name', '')),
                expected_status=400,
                expected='{"code": 40001, "message": "参数错误"}',
                category="反向"
            ))

        # P1: 参数类型错误
        if parameters:
            param = parameters[0]
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}参数类型错误",
                priority="P1",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=json.dumps({param.get('name', ''): "string_instead_of_int"}, ensure_ascii=False),
                expected_status=400,
                expected='{"code": 40002, "message": "参数类型错误"}',
                category="反向"
            ))

        # P1: 无效 JSON
        if method in ['POST', 'PUT', 'PATCH']:
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}无效JSON格式",
                priority="P1",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data="{invalid json: true}",
                expected_status=400,
                expected='{"error": "invalid json"}',
                category="反向"
            ))

        # P1: 数值越界
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}数值参数越界",
            priority="P1",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data=json.dumps({"page": -1}, ensure_ascii=False),
            expected_status=400,
            expected='{"code": 40003, "message": "参数值无效"}',
            category="反向"
        ))

        # P2: 空值处理
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}参数值为空字符串",
            priority="P2",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data=json.dumps({"name": ""}, ensure_ascii=False),
            expected_status=400,
            expected='{"code": 40004, "message": "参数不能为空"}',
            category="反向"
        ))

        # P2: 超长字符串
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}字符串参数超长",
            priority="P2",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data=json.dumps({"name": "x" * 10000}, ensure_ascii=False),
            expected_status=400,
            expected='{"code": 40005, "message": "参数过长"}',
            category="反向"
        ))

        # P1: 方法不允许
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        wrong_method = [m for m in allowed_methods if m != method.upper() and m in allowed_methods]
        if wrong_method:
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}不允许的请求方法",
                priority="P1",
                preconditions="无",
                url=url,
                method=wrong_method[0],
                headers={"Content-Type": "application/json"},
                params_type="json",
                data="{}",
                expected_status=405,
                expected='{"error": "method not allowed"}',
                category="反向"
            ))

    def _generate_security_tests(self, api_name: str, method: str, url: str, request_body: Dict):
        """生成安全测试用例"""
        # P0: SQL 注入
        sql_injections = [
            ("单引号", "'"),
            ("OR 1=1", "' OR '1'='1"),
            ("UNION查询", "' UNION SELECT * FROM users--"),
        ]

        for name, value in sql_injections[:1]:
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}SQL注入攻击【{name}】",
                priority="P0",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=json.dumps({"keyword": value}, ensure_ascii=False),
                expected_status=400,
                expected='{"code": 40003, "message": "参数包含非法字符"}',
                category="安全"
            ))

        # P1: XSS 注入
        xss_injections = [
            ("script标签", "<script>alert('xss')</script>"),
            ("img标签", "<img src=x onerror=alert('xss')>"),
        ]

        for name, value in xss_injections[:1]:
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}XSS注入攻击【{name}】",
                priority="P1",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=json.dumps({"content": value}, ensure_ascii=False),
                expected_status=400,
                expected='{"code": 40003, "message": "参数包含非法字符"}',
                category="安全"
            ))

        # P0: 未授权访问
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}未授权访问",
            priority="P0",
            preconditions="无 Token",
            url=url,
            method=method,
            headers={},
            params_type="json",
            data="{}",
            expected_status=401,
            expected='{"detail": "Not authenticated"}',
            category="安全"
        ))

        # P1: Token 过期
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}Token过期",
            priority="P1",
            preconditions="Token 已过期",
            url=url,
            method=method,
            headers={"Authorization": "Bearer expired_token"},
            params_type="json",
            data="{}",
            expected_status=401,
            expected='{"detail": "Token expired"}',
            category="安全"
        ))

        # P1: 权限不足
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}权限不足",
            priority="P1",
            preconditions="使用普通用户 Token",
            url=url,
            method=method,
            headers={"Authorization": "Bearer normal_user_token"},
            params_type="json",
            data="{}",
            expected_status=403,
            expected='{"detail": "Permission denied"}',
            category="安全"
        ))

    def _generate_performance_tests(self, api_name: str, method: str, url: str):
        """生成性能测试用例"""
        # P1: 响应时间
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}响应时间小于1秒",
            priority="P1",
            preconditions="网络环境正常",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data="{}",
            expected_status=200,
            expected="响应时间 < 1000ms",
            category="性能"
        ))

        # P2: 并发请求
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}10并发请求",
            priority="P2",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data="{}",
            expected_status=200,
            expected="10个请求成功率 100%，平均响应时间 < 2s",
            category="性能",
            remark="需要使用 JMeter 或 Locust 执行"
        ))

        # P2: 负载测试
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}100并发负载",
            priority="P2",
            preconditions="服务器已准备",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data="{}",
            expected_status=200,
            expected="100个请求成功率 > 95%，无系统崩溃",
            category="性能",
            remark="需要使用压力测试工具"
        ))

    def _create_testcase(self, title: str, priority: str, preconditions: str,
                         url: str, method: str, headers: Dict, params_type: str,
                         data: str, expected_status: int, expected: str,
                         category: str = "接口", remark: str = "") -> Dict:
        """创建单个测试用例"""
        tc = {
            "用例编号": f"API_{self.module_name.upper()}_{self.testcase_id:03d}",
            "用例标题": title,
            "模块/优先级": f"{self.module_name}/{priority}",
            "接口名称": self.module_name,
            "前置条件": preconditions,
            "请求URL": url,
            "请求类型": method,
            "请求头": self._format_headers(headers),
            "请求参数类型": params_type,
            "请求数据": data,
            "预期响应状态": expected_status,
            "预期响应信息": expected,
            "实际响应信息": "",
            "是否通过": "待执行",
            "测试类型": category,
            "备注": remark
        }
        self.testcase_id += 1
        return tc

    def _format_headers(self, headers: Dict) -> str:
        """格式化请求头"""
        return '\n'.join([f"{k}: {v}" for k, v in headers.items()])

    def _sample_body(self, request_body: Dict) -> str:
        """生成示例请求体"""
        if request_body.get('type') == 'none':
            return ""
        content = request_body.get('content', {})
        if isinstance(content, dict):
            return json.dumps(content, ensure_ascii=False, indent=2)
        return content if content else "{}"

    def _sample_value(self, param: Dict) -> Any:
        """生成示例参数值"""
        param_type = param.get('type', 'string').lower()
        default = param.get('default', '')

        if default:
            return default

        if 'int' in param_type or 'number' in param_type:
            return 1
        elif 'bool' in param_type:
            return True
        elif 'array' in param_type or 'list' in param_type:
            return []
        elif 'object' in param_type:
            return {}
        else:
            return "sample_value"

    def _body_without_field(self, request_body: Dict, field_name: str) -> str:
        """生成移除指定字段的请求体"""
        content = request_body.get('content', {})
        if isinstance(content, dict) and field_name in content:
            del content[field_name]
            return json.dumps(content, ensure_ascii=False)
        return "{}"

    def _sample_response(self, responses: Dict) -> str:
        """生成示例响应"""
        success_response = responses.get('200', responses.get('201', {}))
        if success_response:
            schemas = success_response.get('schemas', [])
            if schemas:
                return json.dumps(schemas[0].get('schema', {}), ensure_ascii=False)
        return '{"code": 0, "message": "success", "data": {...}}'


# 便捷函数
def generate_api_testcases(base_url: str, module_name: str, apis: List[Dict]) -> List[Dict]:
    """生成 API 测试用例"""
    generator = APITestGenerator(base_url, module_name)
    all_cases = []
    for api in apis:
        all_cases.extend(generator.generate(api))
    return all_cases
