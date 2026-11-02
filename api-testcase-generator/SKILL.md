---
name: api-testcase-generator
description: 接口测试用例生成 Skill。根据 OpenAPI/Swagger、Postman Collection、HAR、JSON Schema、Markdown API 文档生成接口测试用例；默认输出 Markdown 手工接口测试用例表，适合评审和手工执行。当用户明确要求“导入 Apifox/Postman”“可导入 JSON”“自动化集合”时，生成 Apifox/Postman Collection JSON。本 Skill 专注接口层测试；非接口业务功能用例请使用 case-design，游戏测试用例请使用 testcase-generator。
---

# 接口测试用例生成器

根据用户提供的接口文档，自动生成接口测试用例。默认生成 **Markdown 手工接口测试用例表**，适合测试评审、手工接口测试执行和提测后冒烟/回归整理；当用户明确要求导入 Apifox/Postman 时，也可以生成可导入 JSON。

## 技能触发

当用户要求：

- 生成接口测试用例
- 根据 API 文档生成测试用例
- 根据接口文档编写手工接口测试用例
- 输出 Markdown 接口测试用例表
- 导出测试用例为 Apifox/Postman 可导入 JSON

## 输入要求

**接口文档**：支持 Postman Collection (.json)、OpenAPI/Swagger (.json/.yaml)、HAR 格式 (.har)、Markdown API 文档 (.md)

**Markdown/TXT API 文档**：仅适用于写明接口路径、请求方法、参数、响应示例的接口文档；普通业务需求文档请使用 `case-design`。

用户需要提供：

- 输入文件路径
- 模块名称
- Base URL（可选，接口请求或导入 JSON 时建议提供）
- 输出模式/格式（可选，默认 manual Markdown）

## 两种主要模式

| 模式 | 默认 | 适用场景 | 输出 |
| ---- | ---- | -------- | ---- |
| manual 手工用例模式 | 是 | 编写、评审、手工执行接口测试用例 | Markdown 表格，核心内容是接口测试用例表 |
| import 导入 JSON 模式 | 否 | 导入 Apifox/Postman 后调试请求或搭建自动化场景 | Postman Collection v2.1 兼容 JSON |

### manual 手工用例模式

默认模式。用户只说“生成接口测试用例”“根据接口文档编写用例”时，优先输出 Markdown 手工接口测试用例表。

CLI 示例：

```bash
python main.py -i api.yaml -m UserAPI
python main.py -i api.yaml --manual -m UserAPI
```

### import 导入 JSON 模式

仅当用户明确要求“生成 Apifox 可导入 JSON”“导入 Postman/Apifox”“自动化集合”时使用。

CLI 示例：

```bash
python main.py -i api.yaml --import-json apifox -m UserAPI -b https://api.example.com
python main.py -i api.yaml --mode import -o apifox -m UserAPI -b https://api.example.com
```

## 执行流程

1. 使用 `parsers/` 模块解析输入文档
2. 使用 `generators/` 模块生成接口测试用例
3. 根据模式选择 formatter：
   - manual：输出手工接口测试用例 Markdown 表
   - import：输出 Apifox/Postman 可导入 JSON
4. 返回测试用例统计和生成的文件列表

## 飞书交付规则

当用户要求把**手工接口测试用例**保存到飞书时：

1. 默认只创建一个汇总飞书电子表格，不按接口、模块或批次生成多个独立飞书文档。
2. 概览/统计（适用时）及各接口模块分别放入同一工作簿的子 Sheet/Tab，保留手工用例所需的完整列结构。
3. 使用 `lark-sheets` 完成在线写入，并回读核验 Sheet 名称与数量、各模块用例数、总用例数、表头/列数、代表性首尾单元格及关键空值/状态字段，确认无截断和列错位。
4. 不自动修改或删除接口源文档、历史用例和参考资料。用户要求删除旧交付物时，必须按 `lark-drive` 先列出准确目标并另行取得明确确认。
5. 本规则只适用于目标明确为飞书的手工用例交付。用户明确要求 Apifox/Postman JSON、pytest、JMeter、原始 JSON、Markdown、本地文件、普通 Excel 或独立文档时，严格按指定格式输出，不得强制转换为飞书电子表格。

## 输出格式

### 默认输出

| 格式 | 说明 |
| ---- | ---- |
| markdown | 手工接口测试用例表，默认推荐，用于评审和手工执行 |
| excel | Excel 文件，适合手工测试执行管理 |

### 可选导入输出

| 格式 | 说明 |
| ---- | ---- |
| apifox | Apifox 可导入集合（Postman Collection v2.1 兼容） |
| postman | Postman Collection JSON |

### 其他扩展输出

| 格式 | 说明 |
| ---- | ---- |
| pytest | Python 测试代码脚手架 |
| jmeter | JMeter JMX 性能测试计划 |
| json | 原始测试用例 JSON 数据 |

## 测试用例类型

- 正向测试：正常参数、必填参数、响应验证
- 反向测试：缺少参数、类型错误、越界、无效数据
- 安全测试：SQL 注入、XSS、未授权、Token 验证
- 性能测试：响应时间、并发请求、负载测试
- 兼容性测试：浏览器/移动端兼容

## 使用示例

```
> 使用 api-testcase-generator，根据 ~/api.yaml 生成接口手工测试用例，模块叫 UserAPI

> 根据我的 postman.json 生成 Markdown 接口测试用例表，用于手工执行

> 根据 ~/api.yaml 生成 Apifox 可导入 JSON，模块叫 UserAPI
```

## 输出内容

默认返回 Markdown 手工接口测试用例表和用例统计（总数、优先级分布、测试类型）。

> 注意：仅当选择 import/apifox 输出时，Apifox 导出采用 Postman Collection v2.1 兼容格式；导入后可执行基础请求和状态码/JSON/字段存在性断言，但环境变量、鉴权 Token、业务链路数据和复杂业务断言仍需要按项目实际情况在 Apifox 中补充。
