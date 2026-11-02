"""
JMeter 输出格式化器
生成 JMeter JMX 格式的测试计划
"""

import json
from datetime import datetime
from typing import Dict, List, Any


class JMeterFormatter:
    """JMeter 格式化器"""

    def __init__(self, module_name: str = "TestModule", base_url: str = ""):
        self.module_name = module_name
        self.base_url = base_url
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def format(self, testcases: List[Dict]) -> str:
        """
        格式化测试用例为 JMeter JMX

        Args:
            testcases: 测试用例列表

        Returns:
            JMeter JMX 格式的 XML 字符串
        """
        # 筛选性能测试用例
        perf_cases = [tc for tc in testcases if tc.get('测试类型', '') == '性能']

        xml = self._header()

        # 添加测试计划
        xml += self._test_plan()

        # 添加线程组
        xml += self._thread_group()

        # 添加 HTTP 请求默认值
        xml += self._http_defaults()

        # 添加 Cookie 管理器
        xml += self._cookie_manager()

        # 添加 HTTP 请求
        xml += self._http_requests(testcases)

        # 添加监听器
        xml += self._listeners()

        # 性能测试专用配置
        if perf_cases:
            xml += self._performance_config(perf_cases)

        xml += self._footer()

        return xml

    def _header(self) -> str:
        """生成 XML 头部"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="''' + f'''{self.module_name} Test Plan" enabled="true">
      <stringProp name="TestPlan.comments">Auto-generated test plan - {self.timestamp}</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>

'''

    def _test_plan(self) -> str:
        """测试计划配置"""
        return '''    <Arguments guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
      <collectionProp name="Arguments.arguments">
        <elementProp name="baseUrl" elementType="Argument">
          <stringProp name="Argument.name">baseUrl</stringProp>
          <stringProp name="Argument.value">''' + f'''{self.base_url}</stringProp>
          <stringProp name="Argument.metadata">=</stringProp>
        </elementProp>
      </collectionProp>
    </Arguments>
    <hashTree/>

'''

    def _thread_group(self) -> str:
        """线程组配置"""
        return '''    <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Main Thread Group" enabled="true">
      <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
      <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
        <boolProp name="LoopController.continue_forever">false</boolProp>
        <intProp name="LoopController.loops">1</intProp>
      </elementProp>
      <stringProp name="ThreadGroup.num_threads">1</stringProp>
      <stringProp name="ThreadGroup.ramp_time">1</stringProp>
      <longProp name="ThreadGroup.start_time">1704067200000</longProp>
      <longProp name="ThreadGroup.end_time">1704153600000</longProp>
      <boolProp name="ThreadGroup.scheduler">false</boolProp>
      <stringProp name="ThreadGroup.duration"></stringProp>
      <stringProp name="ThreadGroup.delay"></stringProp>
    </ThreadGroup>
    <hashTree>

'''

    def _http_defaults(self) -> str:
        """HTTP 请求默认值"""
        return '''      <ConfigTestElement guiclass="HttpDefaultsGui" testclass="ConfigTestElement" testname="HTTP Request Defaults" enabled="true">
        <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
          <collectionProp name="Arguments.arguments"/>
        </elementProp>
        <stringProp name="HTTPSampler.domain">${baseUrl}</stringProp>
        <stringProp name="HTTPSampler.port"></stringProp>
        <stringProp name="HTTPSampler.protocol">https</stringProp>
        <stringProp name="HTTPSampler.contentEncoding"></stringProp>
        <stringProp name="HTTPSampler.path"></stringProp>
      </ConfigTestElement>
      <hashTree/>

'''

    def _cookie_manager(self) -> str:
        """Cookie 管理器"""
        return '''      <CookieManager guiclass="CookiePanel" testclass="CookieManager" testname="HTTP Cookie Manager" enabled="true">
        <collectionProp name="CookieManager.cookies"/>
        <boolProp name="CookieManager.clearEachIteration">false</boolProp>
      </CookieManager>
      <hashTree/>

'''

    def _http_requests(self, testcases: List[Dict]) -> str:
        """生成 HTTP 请求"""
        xml = ""
        case_num = 1

        for tc in testcases:
            if not tc.get('用例编号', '').startswith('API_'):
                continue

            url = tc.get('请求URL', '')
            method = tc.get('请求类型', 'GET')
            name = tc.get('用例标题', f'Test_{case_num}')
            priority = tc.get('模块/优先级', 'P1').split('/')[-1]

            # 跳过低优先级测试以加快执行
            enabled = "true" if priority in ['P0', 'P1'] else "false"

            xml += f'''      <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{name}" enabled="{enabled}">
        <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
        <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
          <collectionProp name="Arguments.arguments">
            <elementProp name="" elementType="HTTPArgument">
              <boolProp name="HTTPArgument.always_encode">false</boolProp>
              <stringProp name="Argument.value">{tc.get('请求数据', '{}')}</stringProp>
              <stringProp name="Argument.metadata">=</stringProp>
            </elementProp>
          </collectionProp>
        </elementProp>
        <stringProp name="HTTPSampler.path">{url}</stringProp>
        <stringProp name="HTTPSampler.method">{method}</stringProp>
        <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
      </HTTPSamplerProxy>
      <hashTree>
        <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="View Results Tree" enabled="true">
          <boolProp name="ResultCollector.error_logging">false</boolProp>
          <objProp>
            <name>saveConfig</name>
            <value class="SampleSaveConfiguration">
              <time>true</time>
              <latency>true</latency>
              <timestamp>true</timestamp>
              <success>true</success>
              <label>true</label>
              <code>true</code>
              <message>true</message>
              <threadName>true</threadName>
              <dataType>true</dataType>
              <assertionResults>true</assertionResults>
              <subResults>true</subResults>
              <responseData>false</responseData>
              <samplerData>false</samplerData>
              <xml>true</responseData>
              <fieldNames>true</fieldNames>
              <responseHeaders>false</responseHeaders>
              <requestHeaders>false</responseHeaders>
              <responseDataOnError>false</responseDataOnError>
              <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
              <assertionsResultsToSave">0</assertionsResultsToSave>
              <bytes>true</bytes>
              <sentBytes>true</sentBytes>
              <url>true</url>
              <threadCounts>true</threadCounts>
              <sampleCount>true</sampleCount>
              <idleTime>true</idleTime>
              <connectTime>true</connectTime>
            </value>
          </objProp>
          <stringProp name="filename"></stringProp>
        </ResultCollector>
        <hashTree/>
      </hashTree>

'''
            case_num += 1

        return xml

    def _listeners(self) -> str:
        """监听器配置"""
        return '''      <ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="Summary Report" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <assertionResults>true</assertionResults>
            <subResults>true</subResults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>true</responseData>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave">0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <sampleCount>true</sampleCount>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="filename"></stringProp>
      </ResultCollector>
      <hashTree/>

'''

    def _performance_config(self, perf_cases: List[Dict]) -> str:
        """性能测试专用配置"""
        return '''      <kg.apc.jmeter.vizualizers.CorrectedResultCollector guiclass="kg.apc.jmeter.vizualizers.JmeterReporterGui" testclass="kg.apc.jmeter.vizualizers.CorrectedResultCollector" testname="jp@gc - Results Reporter" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <param name="filename">results/''' + f'''{self.module_name}_results.jtl</param>
        <param name="exportedStats">all</param>
      </kg.apc.jmeter.vizualizers.CorrectedResultCollector>
      <hashTree/>

'''

    def _footer(self) -> str:
        """XML 尾部"""
        return '''  </hashTree>
</jmeterTestPlan>
'''

    def save(self, xml: str, filepath: str):
        """保存 JMX 文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml)
        return filepath


# 便捷函数
def format_jmeter(testcases: List[Dict], module_name: str, base_url: str = "") -> str:
    """格式化测试用例为 JMeter JMX"""
    return JMeterFormatter(module_name, base_url).format(testcases)
