import os
import graphviz
import platform

# 确保目标目录存在
os.makedirs('../assets/images', exist_ok=True)

# 根据操作系统选择合适的字体
system = platform.system()
if system == "Windows":
    chinese_font = "Microsoft YaHei"  # 微软雅黑
elif system == "Darwin":  # macOS
    chinese_font = "PingFang SC"
else:  # Linux 和其他系统
    chinese_font = "WenQuanYi Zen Hei"

# 创建有向图
dot = graphviz.Digraph(
    'synapse_architecture',
    comment='Synapse AI Architecture',
    format='png',
    engine='dot'
)

# 设置图形属性
dot.attr(rankdir='TB', size='12,10', dpi='300', bgcolor='white')
dot.attr('node', shape='box', style='filled', fillcolor='lightblue', fontname=chinese_font, fontsize='14')
dot.attr('edge', fontname=chinese_font, fontsize='12')

# 创建子图分组
with dot.subgraph(name='cluster_io_input') as c:
    c.attr(label='输入流', style='filled', color='lightgrey', fontname=chinese_font)
    c.node('web_in', 'Web输入')
    c.node('console_in', '控制台输入')
    c.node('api_in', 'API输入')
    c.node('custom_in', '自定义输入插件')

with dot.subgraph(name='cluster_triggers') as c:
    c.attr(label='触发器模块', style='filled', color='lightgrey', fontname=chinese_font)
    c.node('time_trigger', '时间触发器')
    c.node('event_trigger', '事件触发器')
    c.node('message_trigger', '消息触发器')

with dot.subgraph(name='cluster_preprocessing') as c:
    c.attr(label='前处理模块', style='filled', color='lightgrey', fontname=chinese_font)
    c.node('intent_recog', '意图识别')
    c.node('data_filter', '数据过滤')
    c.node('context_enhancer', '上下文增强')

with dot.subgraph(name='cluster_memory') as c:
    c.attr(label='记忆系统', style='filled', color='lightgrey', fontname=chinese_font)
    c.node('short_term', '短期记忆')
    c.node('medium_term', '中期记忆')
    c.node('long_term', '长期记忆')
    c.node('retrieval', '记忆检索')

# 核心处理单元
dot.node('core', 'Core核心处理单元', shape='box', style='filled', fillcolor='orange', fontname=chinese_font)

with dot.subgraph(name='cluster_output_control') as c:
    c.attr(label='输出抑制与反馈调节单元', style='filled', color='lightgrey', fontname=chinese_font)
    c.node('content_filter', '内容过滤')
    c.node('quality_control', '质量控制')
    c.node('feedback', '反馈调节')

# RAG数据库
dot.node('rag', 'RAG数据库', shape='cylinder', style='filled', fillcolor='lightgreen', fontname=chinese_font)

with dot.subgraph(name='cluster_io_output') as c:
    c.attr(label='输出流', style='filled', color='lightgrey', fontname=chinese_font)
    c.node('console_out', '控制台输出')
    c.node('api_out', 'API输出')
    c.node('web_out', 'Web输出')
    c.node('custom_out', '自定义输出插件')

# MCP工具
dot.node('mcp_tools', 'MCP外接工具', shape='component', style='filled', fillcolor='lightyellow', fontname=chinese_font)

# 添加连接关系
# 输入流 -> 触发器
dot.edge('console_in', 'message_trigger')
dot.edge('api_in', 'event_trigger')
dot.edge('web_in', 'message_trigger')
dot.edge('custom_in', 'event_trigger')

# 触发器 -> 前处理
dot.edge('time_trigger', 'intent_recog')
dot.edge('event_trigger', 'data_filter')
dot.edge('message_trigger', 'context_enhancer')

# 前处理 -> 核心
dot.edge('intent_recog', 'core')
dot.edge('data_filter', 'core')
dot.edge('context_enhancer', 'core')

# 记忆系统的连接
dot.edge('core', 'short_term', dir='both')
dot.edge('core', 'retrieval')
dot.edge('retrieval', 'medium_term')
dot.edge('retrieval', 'long_term')

# RAG连接
dot.edge('core', 'rag', dir='both')
dot.edge('rag', 'retrieval')

# 核心 -> 输出控制
dot.edge('core', 'content_filter')
dot.edge('content_filter', 'quality_control')
dot.edge('quality_control', 'feedback')
dot.edge('feedback', 'core', label='反馈')

# 输出控制 -> 输出流
dot.edge('feedback', 'console_out')
dot.edge('feedback', 'api_out')
dot.edge('feedback', 'web_out')
dot.edge('feedback', 'custom_out')

# MCP工具连接
dot.edge('core', 'mcp_tools', dir='both', label='调用外部工具')

try:
    # 移除encoding参数，因为render()方法不支持该参数
    # 保存图像
    dot.render('d:/Code/Synapse/assets/images/synapse_architecture', cleanup=True)
    
    print(f"架构图已生成保存到: d:/Code/Synapse/assets/images/synapse_architecture.png")
except Exception as e:
    print(f"生成架构图时出错: {e}")
    
    # 尝试使用简化版本生成图形
    print("尝试使用简化版本...")
    dot_simple = graphviz.Digraph(
        'synapse_architecture_simple',
        comment='Synapse AI Architecture (Simple)',
        format='png',
        engine='dot'
    )
    
    # 使用更简单的方式创建图形
    dot_simple.node('input', '输入流')
    dot_simple.node('trigger', '触发器模块')
    dot_simple.node('preprocess', '前处理模块')
    dot_simple.node('memory', '记忆系统')
    dot_simple.node('core', 'Core核心处理单元')
    dot_simple.node('output_control', '输出抑制与反馈调节单元')
    dot_simple.node('rag', 'RAG数据库')
    dot_simple.node('output', '输出流')
    dot_simple.node('mcp', 'MCP外接工具')
    
    # 添加连接
    dot_simple.edge('input', 'trigger')
    dot_simple.edge('trigger', 'preprocess')
    dot_simple.edge('preprocess', 'core')
    dot_simple.edge('core', 'memory', dir='both')
    dot_simple.edge('core', 'rag', dir='both')
    dot_simple.edge('core', 'output_control')
    dot_simple.edge('output_control', 'output')
    dot_simple.edge('output_control', 'core', label='反馈')
    dot_simple.edge('core', 'mcp', dir='both')
    
    # 保存简化版图像
    dot_simple.render('../assets/images/synapse_architecture_simple', cleanup=True)

    print(f"简化版架构图已生成保存到: ../assets/images/synapse_architecture_simple.png")
