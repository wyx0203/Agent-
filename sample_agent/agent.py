from sample_agent.api_key import llm_key
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="Qwen/Qwen3-8B",         # 指定使用的模型，这里是 Qwen3 代的 8B（80亿参数）版本
    temperature=0,                 # 模型输出的“随机性”，0 表示完全确定性输出（适合问答、代码等确定任务）
    max_retries=2,                 # 如果请求失败，最多重试 2 次
    api_key=llm_key,               # 你的 API 密钥，用于鉴权
    base_url="https://api.siliconflow.cn/v1"  # 指定 API 服务地址，这里是 SiliconFlow 提供的 Qwen 接口
)

from langchain.tools import tool
import os

@tool
def open_file(file_path: str):
    """
    打开本地文件的工具。适用于 Windows 系统。
    
    参数：
        file_path: 要打开的文件完整路径，例如 C:\\Users\\Alice\\Documents\\example.pdf
    
    返回：
        成功或失败的提示信息。
    """
    try:
        print(f"正在打开文件：{file_path}")
        os.startfile(file_path)  # Windows 专用方法，默认用系统关联程序打开文件
        return f"成功打开文件：{file_path}"
    except Exception as e:
        return f"打开文件失败：{str(e)}"

from typing import List, TypedDict, Annotated
from langchain_core.messages import SystemMessage, AIMessage, AnyMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# 定义状态，一个消息对象的列表
class AgentState(TypedDict):
    
    # 使用 Annotated 给这个字段添加了运行时元信息 `add_messages` 用来追加新消息到历史中
    messages: Annotated[list[AnyMessage], add_messages]

# 开始节点和结束节点
from langgraph.graph import  END, START

# 定义工具节点
tools = [open_file]
tool_node = ToolNode(tools)

# 定义AI节点
model_with_tools = model.bind_tools(tools)
def ai_node(state: AgentState):
    # 系统消息
    system_message = SystemMessage(
        content=f"你是一个工作能力很强的助手。"
    )
    response = model_with_tools.invoke([system_message] + state["messages"])
    return {"messages": [response]}

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import tools_condition

## The graph
builder = StateGraph(AgentState)

# 添加节点
builder.add_node("ai_node", ai_node)
builder.add_node("tool_node", tool_node)

# 添加边：这些决定了控制流如何移动
builder.add_edge(START, "ai_node")
#添加条件边：根据 tools_condition 的返回决定下一步
builder.add_conditional_edges(
    "ai_node",         # 条件触发点：在 ai_node 完成后执行
    tools_condition,   # 条件函数：接收 state，返回一个 key（如 "tools" 或 "__end__"）
    {
        "tools": "tool_node",  # 若返回 "tools"，跳转到 tool_node
        "__end__": END         # 若返回 "__end__", 跳转至 END 节点并终止 
    }
)
builder.add_edge("tool_node", "ai_node")

# 在多轮对话中，通过MemorySaver保留上一轮的状态（多轮对话必须！）
from langgraph.checkpoint.memory import MemorySaver
react_graph = builder.compile(checkpointer=MemorySaver())
