# AI 赋能的智能简历分析系统

基于 FastAPI + Streamlit 的智能简历解析与岗位匹配平台，支持 PDF 简历上传、关键信息自动提取、岗位匹配度评分。

---

项目地址：https://github.com/zhang-meng66/resume-analyzer



## 项目简介

这是一个面向招聘场景的智能简历分析工具。用户上传 PDF 格式的简历后，系统自动提取姓名、电话、邮箱、学历、技能关键词等核心信息，并根据岗位描述计算简历与岗位的匹配度评分，帮助招聘者快速筛选候选人。

核心功能包括：PDF简历上传与全文解析、关键信息自动提取、岗位匹配度评分（0-100分）、结构化JSON输出、Web交互界面。


## 技术栈

后端：FastAPI + Uvicorn + pdfplumber + 正则表达式

前端：Streamlit

部署：Docker / Streamlit Cloud


## 快速启动

克隆项目到本地：git clone https://github.com/你的用户名/resume-analyzer.git

启动后端：进入backend目录，执行 pip install -r requirements.txt 安装依赖，然后运行 uvicorn main:app --reload，服务默认运行在 http://localhost:8000

启动前端：进入frontend目录，执行 pip install streamlit requests，然后运行 streamlit run app.py，页面默认运行在 http://localhost:8501

Docker部署：在backend目录下执行 docker build -t resume-analyzer . 构建镜像，然后 docker run -p 8000:8000 resume-analyzer 启动容器


## API接口

GET /health 健康检查，返回服务状态。

POST /parse 上传PDF简历，返回解析结果。参数为 file（PDF文件），响应包含 success 状态和 data 中的 name/email/phone/education/skills/raw_text 字段。

POST /match 上传简历并输入岗位描述，返回匹配度评分。参数为 file（PDF文件）和 job_description（表单文本），响应包含 resume 解析结果和 match 评分详情，其中 score 为最终得分（0-100），matched_skills 为匹配到的技能列表。


## 项目结构

backend/ 目录下包含主程序 main.py、简历解析模块 resume_parser.py、评分模块 resume_scorer.py、依赖文件 requirements.txt 和 Dockerfile。frontend/ 目录下是 Streamlit 前端 app.py。根目录有 README.md 和 .env.example 环境变量示例。


## 设计思路

简历解析采用规则优先策略。姓名取文本第一行或匹配 Name: 模式，电话和邮箱用正则精确匹配，技能基于预定义词库进行关键词匹配，学历基于关键词（本科/硕士/博士/大学等）匹配所在行。这套方案在保证速度的同时能覆盖大部分常见简历格式。

匹配度评分综合考虑技能匹配率（简历技能与岗位关键词的交集占比）和信息完整度（姓名/电话/邮箱是否识别完整），最终得分上限100分。评分逻辑透明可解释，不依赖外部API，完全本地运行。


## 环境变量

在 Streamlit Cloud 部署时，需要在 .streamlit/secrets.toml 中配置 API_URL = "http://localhost:8000" 指向后端地址。


## 待优化方向

后续可接入大模型API提升信息提取精度，增加Redis缓存避免重复解析，支持docx和图片格式简历，增加批量上传与批量评分功能，以及简历评分历史记录与对比功能。


## 作者

张萌 | 13946841695 | safla_zhang.hrb@foxmail.com | https://github.com/zhang-meng66
