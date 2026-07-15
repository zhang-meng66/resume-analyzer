# AI 赋能的智能简历分析系统

基于 FastAPI + Streamlit 的智能简历解析与岗位匹配平台，支持 PDF 简历上传、关键信息自动提取（姓名、电话、邮箱、学历、技能、项目经历等）、岗位匹配度评分，并内置缓存机制避免重复解析。

项目地址：https://github.com/zhang-meng66/resume-analyzer


## 项目简介

这是一个面向招聘场景的智能简历分析工具。用户上传 PDF 格式的简历后，系统自动提取姓名、电话、邮箱、学历、技能关键词、项目经历等核心信息，并根据岗位描述计算简历与岗位的匹配度评分，帮助招聘者快速筛选候选人。

核心功能包括：PDF简历上传与全文解析、关键信息自动提取（10+字段）、岗位匹配度评分（0-100分，含多维度拆解）、结构化JSON输出、内存缓存机制、Web交互界面。


## 技术栈

后端：FastAPI + Uvicorn + pdfplumber + 正则表达式

前端：Streamlit

缓存：内存字典（可无缝切换 Redis）

部署：Docker / Streamlit Cloud


## 快速启动

### 1. 克隆项目

```bash
git clone https://github.com/zhang-meng66/resume-analyzer.git
cd resume-analyzer
```

### 2. 安装依赖

```bash
pip install fastapi uvicorn pdfplumber python-multipart pydantic python-dotenv streamlit requests
```

### 3. 启动后端

```bash
cd backend
uvicorn main:app --reload
```

后端服务默认运行在：http://localhost:8000

API 文档自动生成：http://localhost:8000/docs

### 4. 启动前端（新开终端）

```bash
streamlit run frontend/app.py
```

前端页面默认运行在：http://localhost:8501

### 5. Docker 部署（可选）

```bash
docker build -t resume-analyzer .
docker run -p 8000:8000 resume-analyzer
```


## API 接口

### GET /health
健康检查，返回服务状态。

### POST /parse
上传 PDF 简历，返回解析结果。

请求参数：file（PDF文件）

响应字段：success、data（含 name/phone/email/address/job_intention/salary/work_years/education/projects/skills/raw_text）、from_cache（是否命中缓存）

### POST /match
上传简历并输入岗位描述，返回匹配度评分。

请求参数：file（PDF文件）、job_description（表单文本）

响应字段：success、data（含 resume 解析结果和 match 评分详情）、from_cache

其中 match 包含：score（最终得分0-100）、skill_match_score、experience_score、education_score、project_score、ai_bonus_score、matched_skills、jd_keywords、details

### GET /cache/status
查看缓存状态（缓存条目数/最大容量）。

### GET /cache/clear
清空缓存（管理接口）。


## 项目结构

```
resume-analyzer/
├── backend/
│   ├── main.py              # FastAPI 主入口
│   ├── resume_parser.py     # PDF 解析 + 信息提取（10+字段）
│   ├── resume_scorer.py     # 匹配度评分（多维度 + AI模拟加分）
│   ├── requirements.txt     # Python 依赖
│   └── Dockerfile           # 容器化部署配置
├── frontend/
│   └── app.py               # Streamlit 前端界面
├── README.md                # 项目文档
└── .env.example             # 环境变量示例
```


## 设计思路

### 简历解析策略

简历解析采用规则优先策略：
- 姓名：匹配"姓名："模式或取文本前几行
- 电话/邮箱：正则精确匹配
- 技能：基于 50+ 预定义技能词库进行关键词匹配
- 学历：基于关键词（本科/硕士/博士/大学等）匹配所在行
- 项目经历：定位"项目经历"章节，按日期或标题分组提取，自动过滤获奖/奖学金信息
- 求职意向/期望薪资/工作年限/地址：正则匹配对应标签

这套方案在保证速度的同时能覆盖大部分常见简历格式。

### 匹配度评分逻辑

评分综合五个维度：
1. 技能匹配率（50分）：简历技能与岗位关键词的加权匹配
2. 工作经验相关性（20分）：工作年限 + 项目数量综合评估
3. 学历匹配（15分）：博士/硕士/本科/大专梯度计分
4. 项目经验质量（10分）：项目数量 + 技术栈丰富度
5. AI模拟加分（5分）：基于文本长度和技能数量的质量评估

最终得分上限100分，评分逻辑透明可解释，不依赖外部API。

### 缓存机制

使用内存字典实现 LRU 风格缓存，容量上限50条。缓存 key 基于文件内容哈希 + 岗位描述哈希生成，命中缓存时响应头标记 from_cache=true。可通过 /cache/status 和 /cache/clear 接口管理缓存，生产环境可无缝切换至 Redis。


## 线上演示

前端页面已部署至 Streamlit Cloud：

🔗 https://zhang-meng66-resume-analyzer.streamlit.app

⚠️ 注意：该应用需要浏览器启用 JavaScript 才能运行。如无法访问，请检查网络环境或尝试更换浏览器。也可在本地启动后端后，将前端配置指向本地地址进行体验。


## 环境变量

在 Streamlit Cloud 部署时，需要在 `.streamlit/secrets.toml` 中配置：

```toml
API_URL = "http://localhost:8000"
```

或直接在 frontend/app.py 中修改 API_BASE_URL 变量。


## 作者

张萌 | 13946841695 | safla_zhang.hrb@foxmail.com | https://github.com/zhang-meng66