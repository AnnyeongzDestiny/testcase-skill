# 测试用例模板示例

## 一、功能测试用例示例

### 1.1 用户登录模块

| 功能ID | 用例标题 | 功能模块 | 优先级 | 预置条件 | 测试数据 | 执行步骤 | 预期结果 | 测试结果 | 测试版本号 | 测试人员 | 备注 |
|--------|----------|----------|--------|----------|----------|----------|----------|----------|------------|----------|------|
| FUNC_LOGIN_001 | 验证正确账号密码登录成功 | 用户登录 | P0 | 用户已注册账号 test@example.com | 账号: test@example.com, 密码: Test123 | 1. 打开登录页面 2. 输入正确账号 3. 输入正确密码 4. 点击登录按钮 | 登录成功，跳转至首页，显示用户信息 | Pass | v1.0.0 | 张三 | |
| FUNC_LOGIN_002 | 验证错误密码登录失败 | 用户登录 | P0 | 用户已注册账号 test@example.com | 账号: test@example.com, 密码: Wrong123 | 1. 打开登录页面 2. 输入正确账号 3. 输入错误密码 4. 点击登录按钮 | 显示"密码错误"提示，停留在登录页 | Pass | v1.0.0 | 张三 | |
| FUNC_LOGIN_003 | 验证账号不存在 | 用户登录 | P0 | 无 | 账号: notexist@example.com, 密码: Test123 | 1. 打开登录页面 2. 输入未注册账号 3. 输入任意密码 4. 点击登录按钮 | 显示"账号不存在"提示 | Pass | v1.0.0 | 张三 | |
| FUNC_LOGIN_004 | 验证空账号登录 | 用户登录 | P0 | 无 | 账号: 空, 密码: Test123 | 1. 打开登录页面 2. 账号留空 3. 输入密码 4. 点击登录按钮 | 显示"请输入账号"提示 | Pass | v1.0.0 | 张三 | |
| FUNC_LOGIN_005 | 验证空密码登录 | 用户登录 | P0 | 用户已注册账号 test@example.com | 账号: test@example.com, 密码: 空 | 1. 打开登录页面 2. 输入账号 3. 密码留空 4. 点击登录按钮 | 显示"请输入密码"提示 | Pass | v1.0.0 | 张三 | |
| FUNC_LOGIN_006 | 验证SQL注入攻击 | 用户登录 | P0 | 无 | 账号: ' OR 1=1--, 密码: 任意 | 1. 打开登录页面 2. 输入SQL注入语句 3. 输入任意密码 4. 点击登录按钮 | 提示输入格式不正确，不执行注入 | Pass | v1.0.0 | 张三 | 安全测试 |
| FUNC_LOGIN_007 | 验证XSS攻击 | 用户登录 | P1 | 无 | 账号: <script>alert(1)</script>, 密码: 任意 | 1. 打开登录页面 2. 输入XSS脚本 3. 输入任意密码 4. 点击登录按钮 | 脚本被转义或拒绝，不弹窗 | Pass | v1.0.0 | 张三 | 安全测试 |
| FUNC_LOGIN_008 | 验证密码明文显示切换 | 用户登录 | P2 | 无 | 账号: test@example.com, 密码: Test123 | 1. 打开登录页面 2. 输入密码 3. 点击密码显示切换按钮 | 密码可切换显示/隐藏 | Pass | v1.0.0 | 张三 | 体验测试 |
| FUNC_LOGIN_009 | 验证登录后Session有效期 | 用户登录 | P1 | 用户已登录 | 无 | 1. 登录成功后等待超过Session有效期 2. 刷新页面 | 被要求重新登录 | Pass | v1.0.0 | 张三 | 性能测试 |
| FUNC_LOGIN_010 | 验证密码强度提示 | 用户登录 | P2 | 无 | 密码: 123456 | 1. 打开登录页面 2. 输入弱密码 | 显示密码强度提示 | Pass | v1.0.0 | 张三 | 体验测试 |
| FUNC_LOGIN_011 | 验证记住密码功能 | 用户登录 | P1 | 用户已开启记住密码 | 无 | 1. 关闭浏览器重新打开 2. 进入登录页 | 自动填充账号密码 | Pass | v1.0.0 | 张三 | 功能测试 |
| FUNC_LOGIN_012 | 验证多设备登录限制 | 用户登录 | P1 | 用户已在一台设备登录 | 无 | 1. 在另一设备使用相同账号登录 | 原设备被踢下线 | Pass | v1.0.0 | 张三 | 功能测试 |

### 1.2 兼容性测试用例模板

| 功能ID | 用例标题 | 功能模块 | 优先级 | 预置条件 | 测试数据 | 执行步骤 | 预期结果 | 测试结果 | 测试版本号 | 测试人员 | 备注 |
|--------|----------|----------|--------|----------|----------|----------|----------|----------|------------|----------|------|
| FUNC_COMPAT_001 | 验证Chrome浏览器功能正常 | 兼容性 | P0 | 安装Chrome浏览器 | 标准测试数据 | 1. 在Chrome中执行功能测试 | 所有功能正常 | Pass | v1.0.0 | 李四 | 浏览器测试 |
| FUNC_COMPAT_002 | 验证Firefox浏览器功能正常 | 兼容性 | P0 | 安装Firefox浏览器 | 标准测试数据 | 1. 在Firefox中执行功能测试 | 所有功能正常 | Pass | v1.0.0 | 李四 | 浏览器测试 |
| FUNC_COMPAT_003 | 验证Safari浏览器功能正常 | 兼容性 | P0 | 安装Safari浏览器 | 标准测试数据 | 1. 在Safari中执行功能测试 | 所有功能正常 | Pass | v1.0.0 | 李四 | 浏览器测试 |
| FUNC_COMPAT_004 | 验证Edge浏览器功能正常 | 兼容性 | P1 | 安装Edge浏览器 | 标准测试数据 | 1. 在Edge中执行功能测试 | 所有功能正常 | Pass | v1.0.0 | 李四 | 浏览器测试 |
| FUNC_COMPAT_005 | 验证iOS移动端功能正常 | 兼容性 | P0 | iOS设备 | 标准测试数据 | 1. 在iPhone/iPad中执行功能测试 | 所有功能正常 | Pass | v1.0.0 | 李四 | 移动端测试 |
| FUNC_COMPAT_006 | 验证Android移动端功能正常 | 兼容性 | P0 | Android设备 | 标准测试数据 | 1. 在Android手机/平板中执行功能测试 | 所有功能正常 | Pass | v1.0.0 | 李四 | 移动端测试 |

## 二、接口测试用例示例

### 2.1 用户登录接口

| 用例编号 | 用例标题 | 模块/优先级 | 接口名称 | 前置条件 | 请求URL | 请求类型 | 请求头 | 请求参数类型 | 请求数据 | 预期响应信息 | 实际响应信息 | 是否通过 |
|----------|----------|-------------|----------|----------|---------|----------|--------|--------------|----------|--------------|--------------|----------|
| API_LOGIN_001 | 验证正常登录 | 用户登录/P0 | 用户登录 | 无 | /api/v1/user/login | POST | Content-Type: application/json | application/json | {"username": "test@example.com", "password": "Test123"} | {"code": 0, "message": "success", "data": {"token": "xxx", "userId": 123}} | | Pass |
| API_LOGIN_002 | 验证密码错误 | 用户登录/P0 | 用户登录 | 无 | /api/v1/user/login | POST | Content-Type: application/json | application/json | {"username": "test@example.com", "password": "Wrong123"} | {"code": 10001, "message": "密码错误"} | | Pass |
| API_LOGIN_003 | 验证账号不存在 | 用户登录/P0 | 用户登录 | 无 | /api/v1/user/login | POST | Content-Type: application/json | application/json | {"username": "notexist@example.com", "password": "Test123"} | {"code": 10002, "message": "账号不存在"} | | Pass |
| API_LOGIN_004 | 验证缺少必填参数 | 用户登录/P0 | 用户登录 | 无 | /api/v1/user/login | POST | Content-Type: application/json | application/json | {"username": "test@example.com"} | {"code": 40001, "message": "参数不完整"} | | Pass |
| API_LOGIN_005 | 验证参数类型错误 | 用户登录/P1 | 用户登录 | 无 | /api/v1/user/login | POST | Content-Type: application/json | application/json | {"username": 123, "password": "Test123"} | {"code": 40002, "message": "参数类型错误"} | | Pass |
| API_LOGIN_006 | 验证请求方法错误 | 用户登录/P1 | 用户登录 | 无 | /api/v1/user/login | GET | Content-Type: application/json | application/json | {} | {"code": 405, "message": "不支持的请求方法"} | | Pass |
| API_LOGIN_007 | 验证未授权访问 | 用户登录/P0 | 用户信息 | 用户已登录 | /api/v1/user/profile | GET | Authorization: Bearer xxx | application/json | {} | {"code": 0, "data": {"userId": 123, "username": "test"}} | | Pass |
| API_LOGIN_008 | 验证Token过期 | 用户登录/P0 | 用户信息 | Token已过期 | /api/v1/user/profile | GET | Authorization: Bearer expired_token | application/json | {} | {"code": 40101, "message": "Token已过期"} | | Pass |
| API_LOGIN_009 | 验证Token无效 | 用户登录/P0 | 用户信息 | 无 | /api/v1/user/profile | GET | Authorization: Bearer invalid_token | application/json | {} | {"code": 40102, "message": "无效的Token"} | | Pass |
| API_LOGIN_010 | 验证并发登录限制 | 用户登录/P1 | 用户登录 | 用户已在一处登录 | /api/v1/user/login | POST | Content-Type: application/json | application/json | {"username": "test@example.com", "password": "Test123"} | {"code": 0, "message": "success", "data": {"token": "new_xxx"}} | | Pass |
| API_LOGIN_011 | 验证登录频率限制 | 用户登录/P1 | 用户登录 | 短时间内多次失败 | /api/v1/user/login | POST | Content-Type: application/json | application/json | {"username": "test@example.com", "password": "Wrong123"} | {"code": 429, "message": "请求过于频繁，请稍后再试"} | | Pass |
| API_LOGIN_012 | 验证SQL注入攻击 | 用户登录/P0 | 用户登录 | 无 | /api/v1/user/login | POST | Content-Type: application/json | application/json | {"username": "' OR 1=1--", "password": "任意"} | {"code": 40003, "message": "参数包含非法字符"} | | Pass |

### 2.2 性能测试接口用例

| 用例编号 | 用例标题 | 模块/优先级 | 接口名称 | 前置条件 | 请求URL | 请求类型 | 请求头 | 请求参数类型 | 请求数据 | 预期响应信息 | 实际响应信息 | 是否通过 |
|----------|----------|-------------|----------|----------|---------|----------|--------|--------------|----------|--------------|--------------|----------|
| API_PERF_001 | 验证登录接口响应时间 | 性能/P0 | 用户登录 | 无 | /api/v1/user/login | POST | Content-Type: application/json | application/json | {"username": "test@example.com", "password": "Test123"} | 响应时间 < 500ms | | Pass |
| API_PERF_002 | 验证10并发登录 | 性能/P1 | 用户登录 | 无 | /api/v1/user/login | POST | Content-Type: application/json | application/json | 标准测试数据 | 10个请求均成功，响应时间 < 1s | | Pass |
| API_PERF_003 | 验证50并发登录 | 性能/P1 | 用户登录 | 无 | /api/v1/user/login | POST | Content-Type: application/json | application/json | 标准测试数据 | 50个请求成功率 > 99% | | Pass |
| API_PERF_004 | 验证100并发登录 | 性能/P2 | 用户登录 | 无 | /api/v1/user/login | POST | Content-Type: application/json | application/json | 标准测试数据 | 100个请求成功率 > 95% | | Pass |

## 三、测试用例设计原则

### 3.1 正向测试要点
1. 主流程完整执行
2. 所有必填字段填写正确
3. 可选字段的组合测试
4. 正常业务场景覆盖

### 3.2 反向测试要点
1. 必填字段缺失
2. 数据类型错误
3. 数据长度超限
4. 特殊字符注入
5. 边界值测试
6. 权限越权测试
7. 并发冲突测试

### 3.3 优先级定义
| 优先级 | 说明 | 用例比例 |
|--------|------|----------|
| P0 | 核心功能，冒烟测试 | 10-15% |
| P1 | 重要功能，基本测试 | 40-50% |
| P2 | 一般功能，详细测试 | 30-40% |
| P3 | 边缘功能，探索测试 | 5-10% |
