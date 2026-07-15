# AI 赋能的智能简历分析系统

基于 FastAPI + 纯静态前端的智能简历解析与岗位匹配平台，支持 PDF 简历上传、关键信息自动提取（姓名、电话、邮箱、学历、技能、项目经历等 10+ 字段）、岗位匹配度评分，内置内存缓存机制。

**GitHub 仓库**：https://github.com/zhang-meng66/resume-analyzer

**线上前端演示**：https://zhang-meng66.github.io/resume-analyzer/


## 项目简介

这是一个面向招聘场景的智能简历分析工具。用户上传 PDF 格式的简历后，系统自动提取姓名、电话、邮箱、学历、技能关键词、项目经历等核心信息，并根据岗位描述计算简历与岗位的匹配度评分，帮助招聘者快速筛选候选人。

核心功能包括：PDF简历上传与全文解析、关键信息自动提取（10+字段）、岗位匹配度评分（0-100分，含五维度拆解）、结构化JSON输出、内存缓存机制、纯静态前端（GitHub Pages部署）。


## 技术栈

**后端**：FastAPI + Uvicorn + pdfplumber

**前端**：纯 HTML + CSS + JavaScript（静态页面，部署在 GitHub Pages）

**缓存**：内存字典（可无缝切换 Redis）

**部署**：前端 GitHub Pages，后端本地运行/云服务器


## 快速启动

### 1. 克隆项目

```bash
git clone https://github.com/zhang-meng66/resume-analyzer.git
cd resume-analyzer
```

### 2. 安装依赖

```bash
pip install fastapi uvicorn pdfplumber python-multipart pydantic python-dotenv
```

### 3. 启动后端

```bash
cd backend
uvicorn main:app --reload
```

后端服务默认运行在：http://localhost:8000

API 文档：http://localhost:8000/docs

### 4. 访问前端

**方式一（本地测试）**：直接用浏览器打开 `frontend/index.html`

**方式二（线上访问）**：https://zhang-meng66.github.io/resume-analyzer/

⚠️ 注意：前端页面需要后端服务运行中才能正常使用。线上部署的前端默认连接 `http://localhost:8000`，如需连接其他后端地址，请修改 `index.html` 中的 `API_BASE` 变量。


## 线上演示说明

前端页面已部署至 GitHub Pages：https://zhang-meng66.github.io/resume-analyzer/

**使用前提**：后端服务必须在运行状态。如果后端部署在云服务器，需修改 `index.html` 中 `API_BASE` 的地址；如果后端在本地，可通过内网穿透（如 ngrok）生成公网地址供线上页面调用。


## API 接口

### GET /health
健康检查。

### POST /parse
上传 PDF 简历，返回解析结果。

请求参数：file（PDF文件）

响应字段：success、data（含 name/phone/email/address/job_intention/salary/work_years/education/projects/skills/raw_text）、from_cache

### POST /match
上传简历并输入岗位描述，返回匹配度评分。

请求参数：file（PDF文件）、job_description（表单文本）

响应字段：success、data（含 resume 和 match）、from_cache

match 包含：score、skill_match_score、experience_score、education_score、project_score、ai_bonus_score、matched_skills、jd_keywords、details

### GET /cache/status
查看缓存状态。

### GET /cache/clear
清空缓存。


## 项目结构

```
resume-analyzer/
├── backend/
│   ├── main.py              # FastAPI 主入口
│   ├── resume_parser.py     # PDF 解析 + 10+ 字段提取
│   ├── resume_scorer.py     # 五维度匹配度评分
│   ├── requirements.txt     # Python 依赖
│   └── Dockerfile           # 容器化部署
├── frontend/
│   ├── index.html           # 纯静态前端（GitHub Pages 部署）
│   └── app.py               # Streamlit 版本（备用）
├── README.md
└── .env.example
```


## 设计思路

### 简历解析策略

采用规则优先策略：
- 姓名：匹配 "姓名：" 模式或取文本前几行
- 电话/邮箱：正则精确匹配
- 技能：基于 50+ 预定义技能词库匹配
- 学历：关键词（本科/硕士/博士/大学等）匹配所在行
- 项目经历：定位"项目经历"章节，按日期或标题分组提取，自动过滤获奖/奖学金信息
- 求职意向/期望薪资/工作年限/地址：正则匹配对应标签

### 匹配度评分逻辑

评分综合五个维度：
1. 技能匹配率（50分）：简历技能与岗位关键词的加权匹配
2. 工作经验相关性（20分）：工作年限 + 项目数量综合评估
3. 学历匹配（15分）：博士/硕士/本科/大专梯度计分
4. 项目经验质量（10分）：项目数量 + 技术栈丰富度
5. AI模拟加分（5分）：基于文本长度和技能数量的质量评估

### 缓存机制

内存字典实现 LRU 风格缓存，容量上限 50 条。缓存 key 基于文件内容哈希 + 岗位描述哈希生成，命中缓存时返回 `from_cache=true`。


## 环境变量

部署时如需修改后端地址，编辑 `frontend/index.html` 第 180 行：

```javascript
const API_BASE = 'http://localhost:8000';  // 改成实际后端地址
```


## 作者

张萌 | 13946841695 | safla_zhang.hrb@foxmail.com | https://github.com/zhang-meng66