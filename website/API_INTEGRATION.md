# New Report Page - API 集成说明

## 修改概述

已将 `new_report.html` 接到真实后端 API (默认端口 `7000`，路由 `/api/study/import_pgn`)。

## 主要修改

### 1. 新增 `generateReport()` 函数
这是连接真实API的核心函数,位于 `new_report.html:397-454`

**功能:**
- 读取用户上传的PGN文件或粘贴的PGN文本
- 通过 HTTP POST 发送到后端API
- 处理成功/失败响应
- 成功后重定向到 home.html 页面

### 2. 新增 `readFileContent()` 辅助函数
位于 `new_report.html:457-464`

**功能:**
- 异步读取用户选择的PGN文件内容

### 3. 按钮更新
现在有三个按钮:
- **"Generate report"** (绿色主按钮): 调用真实API
- **"Generate report (demo mode)"**: 保留的演示功能
- **"Use sample player: TestYuYaochen"**: 加载示例PGN数据

## 如何配置

### 步骤1: 修改API地址
在 `new_report.html` 顶部的 `resolveApiBase()`:

```javascript
const API_BASE_URL = resolveApiBase(); // 默认 http://localhost:7000
```

根据你的后端服务器地址修改:
- 本地开发: `http://localhost:7000`
- 生产环境: `https://your-domain.com`

### 步骤2: 确认API端点
当前代码调用的端点是:
```
POST /api/study/import_pgn
```

**请求格式:**
```json
{
  "pgn": "1. e4 e5 2. Nf3 Nc6..."
}
```

如果你的后端API端点不同,请修改第424行:
```javascript
const response = await fetch(`${API_BASE_URL}/api/study/import_pgn`, {
```

### 步骤3: 调整请求参数(可选)
在第429-434行,你可以添加更多参数:

```javascript
body: JSON.stringify({
  pgn: pgnContent,
  player_name: 'TestPlayer',        // 可选
  generate_style_report: true,      // 可选
  // 添加其他你的后端需要的参数
})
```

## 后端API要求

你的FastAPI后端需要提供以下端点:

### POST `/api/study/import_pgn`

**请求体:**
```json
{
  "pgn": "PGN内容字符串"
}
```

**成功响应 (200 OK):**
```json
{
  "report_id": "123",
  "status": "success",
  "message": "Report generated successfully"
}
```

**错误响应 (4xx/5xx):**
```json
{
  "detail": "错误描述信息"
}
```

## FastAPI后端示例代码

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class PGNImportRequest(BaseModel):
    pgn: str
    player_name: str | None = None

@app.post("/api/study/import_pgn")
async def import_pgn(request: PGNImportRequest):
    try:
        # 1. 解析PGN
        # 2. 运行引擎分析
        # 3. 生成风格标签
        # 4. 保存报告到数据库
        # 5. 返回成功响应

        return {
            "report_id": "generated_id",
            "status": "success",
            "message": "Report generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# CORS设置 (如果前后端分离)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 测试步骤

### 1. 启动后端服务器
```bash
uvicorn main:app --reload --port 7000
```

### 2. 打开前端页面
在浏览器中打开 `new_report.html`

### 3. 测试流程
1. 点击 "Use sample player: TestYuYaochen" 加载示例数据
2. 点击绿色的 "Generate report" 按钮
3. 观察状态行的变化
4. 检查浏览器控制台(F12)查看网络请求
5. 成功后应该自动跳转到 home.html

## 常见问题

### CORS 错误
如果在浏览器控制台看到 CORS 错误:
```
Access to fetch at 'http://localhost:7000/api/study/import_pgn'
from origin 'null' has been blocked by CORS policy
```

**解决方法:** 在FastAPI后端添加CORS中间件(见上面示例代码)

### 网络请求失败
检查:
- 后端服务是否正常运行
- API_BASE_URL 是否正确
- 网络连接是否正常
- 浏览器控制台的 Network 标签查看详细错误

### 文件读取失败
确保:
- 上传的是 .pgn 或 .txt 文件
- 文件不为空
- 文件编码为 UTF-8

## 下一步开发

1. **添加加载动画**: 在等待API响应时显示spinner
2. **更好的错误处理**: 显示用户友好的错误消息
3. **进度显示**: 如果分析时间较长,显示进度条
4. **结果预览**: 在重定向前显示生成的报告预览
5. **文件拖拽**: 支持拖拽文件上传
6. **多文件上传**: 同时上传多个PGN文件

## 文件修改记录

- `new_report.html:394` - 添加 API_BASE_URL 配置
- `new_report.html:397-454` - 添加 generateReport() 函数
- `new_report.html:457-464` - 添加 readFileContent() 辅助函数
- `new_report.html:366-368` - 添加真实API调用按钮
