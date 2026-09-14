# RAG 知识库管理后台

基于 Vue 3 + Element Plus 的 RAG 知识库可视化管理后台，对接 FastAPI + Milvus（含内存降级模式）。

## 功能特性

- **仪表盘**：文档总数、Chunk 数、分类分布、向量引擎状态
- **文档管理**：文档列表、搜索筛选、上传（.md/.txt/.pdf）、在线编辑、删除
- **索引管理**：一键重建向量索引、索引状态监控、分类分布统计
- **自动分类**：根据文件名和内容自动识别文档分类（设备报修/收银操作/客诉处理等）

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 + Vite |
| UI 组件库 | Element Plus |
| 路由 | Vue Router 4 |
| HTTP 客户端 | Axios |
| 后端 | FastAPI |
| 向量库 | Milvus（生产）/ 内存向量库（演示） |

## 快速开始

### 1. 启动后端服务

```bash
cd project1_store_agent
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

后端 API 文档：http://127.0.0.1:8000/docs

### 2. 启动前端开发服务

```bash
cd kb-admin
npm install
npm run dev
```

访问 http://localhost:5173

### 3. 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录，可部署到 Nginx 或直接由 FastAPI 托管。

## 后端 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/kb/documents` | 文档列表（分页/搜索/分类筛选） |
| GET | `/api/kb/documents/{doc_id}` | 文档详情和内容 |
| POST | `/api/kb/upload` | 上传文档（multipart/form-data） |
| PUT | `/api/kb/documents/{doc_id}` | 更新文档标题/分类/内容 |
| DELETE | `/api/kb/documents/{doc_id}` | 删除文档 |
| POST | `/api/kb/rebuild` | 重建向量索引 |
| GET | `/api/kb/stats` | 知识库统计信息 |
| GET | `/api/kb/categories` | 文档分类列表 |

## 项目结构

```
kb-admin/
├── index.html              # 入口 HTML
├── package.json            # 依赖配置
├── vite.config.js          # Vite 配置（含 API 代理）
└── src/
    ├── main.js             # 应用入口
    ├── App.vue             # 根组件（布局）
    ├── router.js           # 路由配置
    ├── api/
    │   └── index.js        # API 封装
    └── views/
        ├── Dashboard.vue       # 仪表盘
        ├── DocumentList.vue    # 文档列表
        ├── DocumentEdit.vue    # 文档编辑
        └── IndexManage.vue     # 索引管理
```

## 部署到服务器

### 方式一：Nginx 托管前端 + FastAPI 后端

1. 构建前端：`npm run build`
2. 将 `dist/` 内容复制到 Nginx 静态目录
3. 配置 Nginx 反向代理 `/api` 到 FastAPI 服务

### 方式二：FastAPI 直接托管静态文件

在 `main.py` 中添加：

```python
from fastapi.staticfiles import StaticFiles
app.mount("/admin", StaticFiles(directory="kb-admin/dist", html=True), name="admin")
```

访问 `http://your-server/admin`

## 注意事项

- 上传/编辑文档后，需要在「索引管理」页面点击「重建向量索引」才能生效
- 内存向量库模式下，索引持久化到 `data/index.json`，重启服务自动加载
- Milvus 模式下，索引存储在 Milvus 的 `store_chunks` 集合中
- 支持的文档格式：`.md`（Markdown）、`.txt`（纯文本）、`.pdf`（PDF 文档）
