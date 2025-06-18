## 环境配置

**前端：**

*    nodejs：<https://nodejs.cn/>

    下载教程：<https://blog.csdn.net/Goo_12138/article/details/103755492>

**python环境：**

*   第一步：安装conda(教程：<https://blog.csdn.net/ming12131342/article/details/140233867>)

<!---->

*   第二步：新建conda环境 `conda create -n myenv python=3.12`

<!---->

*   第三步：下载AGUI官方示例代码

    `git clone `[`https://github.com/CopilotKit/CopilotKit`](https://github.com/CopilotKit/CopilotKit)  \
    `cd CopilotKit/examples/coagents-starter/agent-py`  &#x20;

<!---->

*   第四步：下载poetry并安装AGUI官方给出的python环境依赖

    `pip install poetry    `

    `poetry install`

**大模型API：**

*    注册硅基流动账号，免费使用Qwen3-8B：<https://siliconflow.cn/>



### Agent\_server代码

```python
import os
from fastapi import FastAPI               # 引入 FastAPI，用于创建 Web 接口服务
import uvicorn                            # 引入 Uvicorn，用于运行 FastAPI 服务
from copilotkit.integrations.fastapi import add_fastapi_endpoint  # 将 CopilotKit 的 Agent 接入 FastAPI 的工具函数
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent   # 核心类：CopilotKit 的远程服务端 + LangGraph Agent

from sample_agent.agent import react_graph  # 导入我们之前定义的智能体流程图（LangGraph 编译结果）

# 初始化一个 FastAPI 应用
app = FastAPI()

# 创建 CopilotKit 服务端，封装了一个或多个 LangGraphAgent
sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAgent(
            name="sample_agent",            # 智能体的名字
            description="拥有打开文件功能的agent",  # 简要描述该智能体的功能
            graph=react_graph,             # 引入你定义好的 LangGraph 工作流程（StateGraph.compile() 的结果）
        )
    ],
)

# 将 CopilotKit 的智能体服务挂载到 FastAPI 应用的指定路由 `/copilotkit` 上
# use_thread_pool=False 表示在主线程中执行，不使用线程池（适用于异步服务）
add_fastapi_endpoint(app, sdk, "/copilotkit", use_thread_pool=False)

# 定义一个新的健康检查接口，方便监测服务是否正常运行
@app.get("/health")
def health():
    """健康检查接口：返回服务状态，供外部监控或测试调用"""
    return {"status": "ok"}

# 定义主函数：运行 Uvicorn 服务器
def main():
    """运行 uvicorn 服务，用于启动整个 API 服务"""
    port = int(os.getenv("PORT", "8080"))   # 从环境变量中读取端口号，默认是 8080
    uvicorn.run(
        "sample_agent.agent_server:app",    # 指定 FastAPI 应用的模块路径（模块名:变量名）
        host="0.0.0.0",                     # 监听所有外部 IP，允许外部访问
        port=port,                          # 使用指定端口
        reload=True,                        # 开发模式下自动热重载代码变化（生产环境推荐关掉）
    )

```

**启动命令**

```bash
uvicorn sample_agent.agent_server:app --reload --host 0.0.0.0 --port 8080
```



## 前端页面创建

### 1. 新建node.js项目

```bash
npx create-next-app@latest
```

### 2.下载相关依赖

```bash
npm install @copilotkit/react-ui @copilotkit/react-core
npm install @copilotkit/runtime class-validator
```

### 2.router.ts文件（放在.\src\app\api\copilotkit\route.ts路径下）

```typescript
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
  langGraphPlatformEndpoint
} from "@copilotkit/runtime";;
import { NextRequest } from "next/server";
 
// You can use any service adapter here for multi-agent support.
const serviceAdapter = new ExperimentalEmptyAdapter();
 
const runtime = new CopilotRuntime({
  remoteEndpoints: [
    // added in next step...
    { url: "http://127.0.0.1:8080/copilotkit" },
  ],
});
 
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
 
  return handleRequest(req);
};
```

### 3.layout.tsx文件

```typescript
import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import { ReactNode } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <CopilotKit
          runtimeUrl="/api/copilotkit"
          agent="sample_agent" // the name of the agent you want to use
        >
          <CopilotChat
            instructions={"You are assisting the user as best as you can. Answer in the best way possible given the data you have."}
            labels={{
              title: "Your Assistant",
              initial: "Hi! 👋 How can I assist you today?",
            }}
          />
        </CopilotKit>
      </body>
    </html>
  );
}
```

### 4.运行node.js

```shell
npm run dev
```

