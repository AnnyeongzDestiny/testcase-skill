"""
Apifox 输出格式化器
生成 Apifox 可导入的 Postman Collection 兼容格式。

说明：Apifox 支持导入 Postman Collection。这里优先生成稳定的
Postman Collection v2.1 兼容 JSON，并补充适合 Apifox 使用的变量、
用例描述和基础断言脚本。
"""

import json
from datetime import datetime
from typing import Dict, List


class ApifoxFormatter:
    """Apifox 格式化器（Postman Collection v2.1 兼容）"""

    def __init__(self, module_name: str = "TestModule", base_url: str = ""):
        self.module_name = module_name
        self.base_url = base_url.rstrip("/")
        self.timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def format(self, testcases: List[Dict]) -> Dict:
        """
        格式化测试用例为 Apifox 可导入的集合。

        Args:
            testcases: 测试用例列表

        Returns:
            Postman Collection v2.1 兼容字典，可导入 Apifox
        """
        collection = {
            "info": {
                "_postman_id": self._generate_id(),
                "name": f"{self.module_name} Apifox Import Collection",
                "description": (
                    f"Auto-generated import collection for {self.module_name}.\n\n"
                    "This JSON is for importing requests into Apifox/Postman and running basic API checks. "
                    "It is not the default manual test case table. "
                    "After import, configure environment variables such as baseUrl and authToken, "
                    "then adjust business assertions, authentication, scenarios and test data for your project."
                ),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [],
            "event": [
                {
                    "listen": "prerequest",
                    "script": {
                        "type": "text/javascript",
                        "exec": [
                            "// Apifox/Postman compatible pre-request script",
                            "// Configure baseUrl and authToken in the Apifox environment before running.",
                        ],
                    },
                }
            ],
            "variable": [
                {"key": "baseUrl", "value": self.base_url, "type": "string"},
                {"key": "authToken", "value": "", "type": "string"},
                {"key": "generationMode", "value": "import", "type": "string"},
            ],
        }

        grouped = self._group_api_cases(testcases)
        for interface, cases in grouped.items():
            collection["item"].append(self._create_folder(interface, cases))

        return collection

    def _group_api_cases(self, testcases: List[Dict]) -> Dict[str, List[Dict]]:
        """按接口名称分组 API 用例。"""
        grouped: Dict[str, List[Dict]] = {}
        for tc in testcases:
            if not tc.get("用例编号", "").startswith("API_"):
                continue
            interface = tc.get("接口名称") or self.module_name or "Unknown"
            grouped.setdefault(interface, []).append(tc)
        return grouped

    def _create_folder(self, folder_name: str, cases: List[Dict]) -> Dict:
        """创建 Apifox/Postman 文件夹。"""
        return {
            "name": folder_name,
            "description": f"{folder_name} generated API test cases",
            "item": [self._create_request(tc) for tc in cases],
        }

    def _create_request(self, tc: Dict) -> Dict:
        """创建单个可导入 Apifox 的请求用例。"""
        raw_url = self._build_raw_url(tc.get("请求URL", ""))
        method = tc.get("请求类型", "GET").upper()
        body_data = tc.get("请求数据", "")

        request = {
            "name": tc.get("用例标题", "Unnamed API Test"),
            "description": self._create_description(tc),
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "type": "text/javascript",
                        "exec": self._generate_test_script(tc),
                    },
                }
            ],
            "request": {
                "method": method,
                "header": self._parse_headers(tc.get("请求头", "")),
                "body": self._parse_body(method, body_data),
                "url": self._parse_url(raw_url),
            },
            "response": [],
        }
        return request

    def _create_description(self, tc: Dict) -> str:
        """生成导入后可在 Apifox 中查看的用例说明。"""
        return "\n".join(
            [
                f"用例编号: {tc.get('用例编号', '')}",
                f"优先级: {tc.get('模块/优先级', '').split('/')[-1]}",
                f"测试类型: {tc.get('测试类型', '')}",
                f"前置条件: {tc.get('前置条件', '')}",
                f"预期响应状态: {tc.get('预期响应状态', '')}",
                f"预期响应信息: {tc.get('预期响应信息', '')}",
                f"备注: {tc.get('备注', '')}",
                "",
                "导入 Apifox 后请根据项目实际情况补充环境变量、鉴权、测试数据和业务断言。",
            ]
        )

    def _build_raw_url(self, url: str) -> str:
        """构建使用 Apifox 环境变量的 URL。"""
        if not url:
            return "{{baseUrl}}"
        if url.startswith("http") or url.startswith("{{"):
            return url
        path = "/" + url.lstrip("/")
        return "{{baseUrl}}" + path

    def _parse_url(self, raw_url: str) -> Dict:
        """解析为 Postman Collection URL 对象。"""
        if raw_url.startswith("{{baseUrl}}"):
            path = raw_url.replace("{{baseUrl}}", "", 1).strip("/")
            return {
                "raw": raw_url,
                "host": ["{{baseUrl}}"],
                "path": path.split("/") if path else [],
            }

        return {
            "raw": raw_url,
            "host": [raw_url],
            "path": [],
        }

    def _parse_headers(self, header_str: str) -> List[Dict]:
        """解析请求头，并将 Bearer token 标准化为环境变量。"""
        headers = []
        has_authorization = False

        for line in header_str.split("\n"):
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if key.lower() == "authorization":
                has_authorization = True
                if value.lower().startswith("bearer"):
                    value = "Bearer {{authToken}}"
            headers.append({"key": key, "value": value, "type": "text"})

        if not any(h["key"].lower() == "content-type" for h in headers):
            headers.append({"key": "Content-Type", "value": "application/json", "type": "text"})

        if has_authorization and not any(h["key"].lower() == "authorization" for h in headers):
            headers.append({"key": "Authorization", "value": "Bearer {{authToken}}", "type": "text"})

        return headers

    def _parse_body(self, method: str, body_str: str) -> Dict:
        """解析请求体。"""
        if method in ["GET", "HEAD"]:
            return {"mode": "raw", "raw": "", "options": {"raw": {"language": "json"}}}

        if not body_str or body_str == "{}":
            return {"mode": "raw", "raw": "{}", "options": {"raw": {"language": "json"}}}

        try:
            body_obj = json.loads(body_str)
            raw = json.dumps(body_obj, ensure_ascii=False, indent=2)
        except (TypeError, json.JSONDecodeError):
            raw = str(body_str)

        return {"mode": "raw", "raw": raw, "options": {"raw": {"language": "json"}}}

    def _generate_test_script(self, tc: Dict) -> List[str]:
        """生成 Apifox/Postman 兼容的基础断言脚本。"""
        expected_status = tc.get("预期响应状态", 200)
        expected_response = tc.get("预期响应信息", "{}")

        script = [
            f"// 用例: {tc.get('用例标题', '')}",
            f"// 编号: {tc.get('用例编号', '')}",
            f"// 类型: {tc.get('测试类型', '')}",
            "",
            f"pm.test('状态码为 {expected_status}', function () {{",
            f"    pm.response.to.have.status({expected_status});",
            "});",
            "",
            "pm.test('响应是 JSON 格式', function () {",
            "    pm.response.to.be.json;",
            "});",
        ]

        try:
            expected_obj = json.loads(expected_response)
            if isinstance(expected_obj, dict):
                for key, value in list(expected_obj.items())[:5]:
                    script.extend(
                        [
                            "",
                            f"pm.test('响应包含字段 {key}', function () {{",
                            "    var jsonData = pm.response.json();",
                            f"    pm.expect(jsonData).to.have.property('{key}');",
                            "});",
                        ]
                    )
                    if key in ("code", "status") and not isinstance(value, (dict, list)):
                        script.extend(
                            [
                                "",
                                f"pm.test('字段 {key} 符合预期', function () {{",
                                "    var jsonData = pm.response.json();",
                                f"    pm.expect(jsonData.{key}).to.eql({json.dumps(value, ensure_ascii=False)});",
                                "});",
                            ]
                        )
        except (TypeError, json.JSONDecodeError):
            script.extend(
                [
                    "",
                    "// 预期响应不是 JSON 对象，请在 Apifox 中补充业务断言:",
                    f"// {expected_response}",
                ]
            )

        return script

    def _generate_id(self) -> str:
        """生成随机 ID。"""
        import uuid

        return str(uuid.uuid4())

    def save(self, collection: Dict, filepath: str):
        """保存 Apifox 可导入集合文件。"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(collection, f, ensure_ascii=False, indent=2)
        return filepath


# 便捷函数
def format_apifox(testcases: List[Dict], module_name: str, base_url: str = "") -> Dict:
    """格式化测试用例为 Apifox 可导入集合。"""
    return ApifoxFormatter(module_name, base_url).format(testcases)
