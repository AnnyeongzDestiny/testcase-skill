# testcase-skill

面向 AI 助手的测试用例技能集合，覆盖普通业务用例设计、接口用例生成、游戏用例生成和用例质量评审。默认以中文 Markdown 交付人工可读、可执行的用例，按需导出 Excel 或接口工具集合。

仓库由 `SKILL.md` 工作流、参考规范和辅助 Python 脚本组成。业务和游戏用例的理解与设计由 AI 助手完成；脚本主要负责解析、校验和导出，不是完整的测试执行平台。

## 五个技能如何选择

| 技能目录 | 声明的技能名 | 主要用途 | 典型输入 | 主要输出 |
| --- | --- | --- | --- | --- |
| [prd-analysis](prd-analysis/SKILL.md) | `prd-analysis` | 写用例前进行结构化需求分析 | PRD、用户故事、需求描述 | BR 规则、等价类、边界值、风险及待澄清项 |
| [case-design](case-design/SKILL.md) | `case-design` | 非游戏业务的功能、业务流程及性能用例设计 | 需求文档、业务规则（BR）清单、性能指标 | 结构化用例表、增量变更、自检结果；按需 Excel |
| [api-testcase-generator](api-testcase-generator/SKILL.md) | `api-testcase-generator` | 接口层用例生成与格式转换 | OpenAPI/Swagger、Postman、Markdown API 文档等 | 默认 Markdown 手工接口用例；按需 Excel、Apifox/Postman JSON 等 |
| [testcase-generator](testcase-generator/SKILL.md) | `game-testcase-generator` | 游戏需求的用例生成、校验与完善 | 游戏需求、玩法规则、可选 BR 清单 | 按模块拆分的 Markdown、大纲、校验结果；按需 Excel |
| [case-review](case-review/SKILL.md) | `case-review` | 审查已有用例集的覆盖和质量 | 已有用例、可选需求及 BR 清单 | 评审报告、逐条问题与修改建议、执行结论 |

> 游戏技能统一以声明名 `game-testcase-generator` 调用；`testcase-generator/` 仅为存放目录，技能间引用已统一。

## 各技能的作用与边界

### prd-analysis：先把需求转换为可追溯规则

从 PRD、用户故事或需求描述中分析功能边界、角色权限、业务规则（BR-xxx）、数据与状态、等价类与边界值、风险（R-xxx）及待澄清项（Q-xxx）。支持首次全量分析和需求补充后的增量更新。

本阶段不生成测试用例；默认先分析再进入业务或游戏用例设计，用户明确要求跳过分析时尊重用户选择。接口文档、代码和日志不应直接套用业务需求分析模板。上传文档时使用运行环境的文件读取或文档解析能力，不要求另装名为 `file-reading` 的专用技能。

### case-design：从业务需求设计用例

适用于登录、订单、审批等非游戏业务。使用正向、反向、边界值、等价类、状态流转和场景法组织覆盖，要求测试数据具体、步骤可独立执行、预期结果可观察。

- 支持首次全量设计，以及新增、更新、废弃用例的增量输出。
- 有 BR 清单时在备注中关联规则编号，检查需求覆盖。
- 默认加载功能测试规范，按需追加性能测试规范和自动化候选筛选规范。
- 使用 P0～P3，要求 P0 占比不超过 20%。
- 不处理游戏需求或接口文档；自动化相关规范用于筛选候选用例，不代表自动生成完整执行脚本。

### api-testcase-generator：从接口文档生成接口用例

适用于依据接口路径、方法、参数和响应定义整理手工接口测试。Python 入口将文档解析为接口信息，生成用例后交给不同格式器输出。

- 默认输出 Markdown 手工接口用例表，包含正向、反向、安全等检查场景。
- 明确要求导入工具时，可输出 Apifox/Postman 集合；Apifox 使用 Postman Collection v2.1 兼容格式。
- 还提供 Excel、原始 JSON、pytest 脚手架和 JMeter 计划输出。
- 生成结果需要结合实际接口补充鉴权、环境变量、业务数据和断言；生成集合或测试计划不代表已执行测试或已验证业务正确性。
- 普通业务需求和游戏玩法需求分别交给另外两个生成技能处理。

### game-testcase-generator：专门处理游戏需求

适用于休闲、卡牌、SLG、RPG、FPS、模拟经营等游戏项目，重点关注玩法规则、状态交叉、边界异常及可观察的玩家反馈。需求未定义的预期必须标记“待确认”。

- 分为轻量（≤20 条）、标准（≤50 条）和完整档；标准、完整档先写大纲，再逐模块生成。
- 提供完整 13 列、轻量十列及带 BR 的轻量结构；实际结果留空，结果默认“未执行”。
- 配套脚本支持需求转 Markdown、用例结构与字段校验、BR 引用和覆盖检查、Excel 导出。
- Excel 可保留模板既有 Sheet，并将生成的用例 Sheet 追加到末尾。
- 使用 P0/P1/P2，每模块至少一条 P0，整体 P0 默认占比至少 30%。

### case-review：对已有用例做质量评审

从覆盖完整性、用例质量、优先级合理性和冗余四个维度审查，给出具体用例编号、问题位置及修改建议。

- 有 BR 清单时逐条对照；没有时使用经验检查清单，并说明覆盖判断的限制。
- 按量化规则输出“可直接执行”“修改后执行”或“需重新设计”。
- 适合在用例生成后、正式执行前使用；它评审用例设计，不执行被测系统。

**组合使用注意：** `case-design` 和 `case-review` 的 P0 上限为 20%，游戏技能的 P0 默认下限为 30%。评审游戏用例时，应明确按游戏规范调整优先级检查标准，否则会产生规则冲突。

## 推荐工作流

| 任务 | 建议流程 |
| --- | --- |
| 普通业务需求 | 需求 → prd-analysis → case-design → case-review → 修改后交付 |
| 接口文档 | 接口文档 → api-testcase-generator → 人工核对数据和断言 → 按需导入工具 |
| 游戏需求 | 游戏需求 → prd-analysis → game-testcase-generator → 分模块生成 → validate.py 校验 → 按需导出 |
| 已有用例检查 | 用例 + 可选需求 / BR 清单 → case-review → 补充和修订 |

`BR` 指业务规则（Business Rule）。`prd-analysis` 已包含在本仓库中，用于为生成和评审建立统一追溯依据；已有 BR 清单可直接作为输入，用户也可明确要求跳过分析。

## 获取与使用

```bash
git clone https://github.com/AnnyeongzDestiny/testcase-skill.git
cd testcase-skill
```

将所需技能目录配置到支持 `SKILL.md` 的 AI 助手中，并保留目录内的 `references/`、`scripts/` 和 `examples/`。具体安装位置和技能加载方式以使用的助手为准。

示例请求：

```text
使用 case-design，根据这份订单需求设计功能测试用例，备注关联 BR 编号。

使用 api-testcase-generator，根据 api.yaml 生成 UserAPI 的 Markdown 手工接口用例。

使用 game-testcase-generator，根据这份消除游戏需求生成轻量用例，总数不超过 20 条。

使用 case-review，检查这组用例的覆盖、预期结果和优先级，给出逐条修改建议。
```

## 辅助脚本

以下命令均从仓库根目录执行，输入路径仅为示例。只使用 AI 工作流和 Markdown 输出时，不必安装全部文档转换、Excel 或测试执行依赖。

### Python 环境

API 主入口使用了 `tuple[str, str]` 类型标注，建议使用 Python 3.9 或更高版本，并在独立虚拟环境中安装依赖。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r testcase-generator/scripts/requirements.txt
python -m pip install PyYAML
```

`requirements.txt` 包括 `openpyxl`、`python-docx`、`pdfplumber` 及 Windows 条件依赖。`PyYAML` 用于 API YAML 解析；执行生成的 pytest 脚手架时另需 `pytest` 和 `requests`。

### 业务用例导出 Excel

```bash
python case-design/scripts/export_to_excel.py ./cases/login.md ./outputs
```

输入包含多个表格时，脚本优先选择列数最多的表格，列数相同时选择行数最多的表格；不会将所有表格逐一导出。

### 接口用例生成

```bash
# 默认生成 Markdown 手工接口用例
python api-testcase-generator/scripts/main.py -i ./api.yaml -m UserAPI -d ./outputs

# 生成 Apifox 可导入 JSON
python api-testcase-generator/scripts/main.py -i ./api.yaml --import-json apifox -m UserAPI -b https://api.example.com -d ./outputs

# 导出 Excel
python api-testcase-generator/scripts/main.py -i ./api.yaml -o excel -m UserAPI -d ./outputs

# 生成 pytest 脚手架
python api-testcase-generator/scripts/main.py -i ./api.yaml -o pytest -m UserAPI -d ./outputs
```

### 游戏需求转换、校验与导出

```bash
# Markdown 需求直接读取；其他受支持格式先转换
python -B testcase-generator/scripts/convert_to_md.py ./requirements.docx --output-dir ./requirements

# 自动识别用例表结构并校验
python -B testcase-generator/scripts/validate.py ./cases --schema auto

# 校验完整 13 列及 BR 追溯
python -B testcase-generator/scripts/validate.py ./cases --schema full --br-source ./prd-analysis.md

# 明确需要 Excel 时导出
python -B testcase-generator/scripts/save_testcases.py ./cases --output-dir ./outputs
```

`.doc` 自动转换依赖 Windows、Microsoft Office 和 `pywin32`。macOS / Linux 可先使用 LibreOffice 或其他工具另存为 `.docx`。更多参数见 [游戏脚本说明](testcase-generator/scripts/README.md)。

## 飞书交付

三个用例生成技能和评审技能均约定：用户明确要求保存到飞书时，默认创建一个汇总电子表格，使用子 Sheet 区分大纲、模块或评审内容，写入后回读核验行列数、用例数及关键字段。

飞书能力由运行环境提供：`lark-sheets` 负责表格读写、导入和回读核验，`lark-drive` 负责云空间文件管理。两者不随本仓库分发；当前维护环境已集成这两个技能及 `lark-cli`（检查版本为 1.0.98），无需重复安装。其他环境需提供相应技能，或配置具备等价能力的 CLI / API 集成，并遵守原技能要求的核验及删除确认规则。实际在线操作仍需有效登录和目标资源权限；本次文档维护未执行飞书写入。明确要求 Markdown、本地 Excel 或接口 JSON 时，仍按指定格式交付。

## 目录结构

```text
.
├── prd-analysis/                # 需求分析与 BR、风险、疑问清单
├── case-design/                 # 非游戏业务用例设计
│   ├── SKILL.md
│   ├── references/              # 功能、性能、自动化等规范
│   └── scripts/                 # Markdown 转 Excel
├── api-testcase-generator/      # 接口用例生成
│   ├── SKILL.md
│   ├── references/
│   └── scripts/                 # 主入口、解析器、生成器、格式器
├── testcase-generator/          # 游戏技能，声明名 game-testcase-generator
│   ├── SKILL.md
│   ├── references/              # 写作规范、模板、测试数据字典
│   ├── scripts/                 # 转换、schema、校验、Excel 导出
│   └── tests/
└── case-review/                 # 用例质量评审
    ├── SKILL.md
    └── examples/                # 评审报告示例
```

## 当前限制

- API 技能说明列出了 HAR 和 JSON Schema，但当前主入口的格式自动识别不完整：`.har` 后缀未被识别，普通独立 JSON Schema 也可能返回未知格式。不能仅依据格式列表认定这些输入可直接运行。
- API 命令入口建议使用 `scripts/main.py`；旧兼容入口 `scripts/testcase_generator.py` 的同名接口生成函数存在递归调用问题。
- `case-design/SKILL.md` 引用的 `examples/login-testcases.md` 和 `prd-analysis/SKILL.md` 引用的 `examples/login-prd-analysis.md` 尚未随仓库提供；业务技能的用户自定义模板 `assets/` 目录也需要自行补充。
- `case-design` 中的 `/mnt/user-data/outputs/` 是环境相关路径；在本机使用时应替换为实际可写目录。
- 生成内容和结构校验不能代替需求确认及实际测试。鉴权、并发、性能和兼容性结论需要在真实测试环境中验证。
