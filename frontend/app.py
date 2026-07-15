import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(
    page_title="AI 简历分析系统",
    page_icon="📄",
    layout="wide"
)

API_BASE_URL = "http://localhost:8000"

st.title("📄 AI 赋能的智能简历分析系统")
st.caption("上传 PDF 简历，自动提取关键信息，匹配岗位需求")

with st.sidebar:
    st.header("⚙️ 功能说明")
    st.markdown("""
    - **📤 上传简历**：支持 PDF 格式
    - **🔍 信息提取**：姓名、电话、邮箱、学历、技能、项目经历
    - **📊 岗位匹配**：输入岗位描述，计算匹配度
    - **💾 结果导出**：JSON 格式结构化数据
    """)
    st.divider()
    st.markdown("**技术栈**：FastAPI + pdfplumber + Streamlit")

tab1, tab2 = st.tabs(["📤 简历解析", "🎯 岗位匹配"])

with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "上传简历 (PDF)",
            type=['pdf'],
            help="支持单页和多页PDF"
        )
        if uploaded_file is not None:
            st.success(f"✅ 已上传: {uploaded_file.name}")
            st.info(f"文件大小: {uploaded_file.size / 1024:.1f} KB")

    with col2:
        if st.button("🚀 开始解析", type="primary", use_container_width=True):
            if uploaded_file is None:
                st.warning("请先上传PDF文件")
            else:
                with st.spinner("正在解析简历..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                        response = requests.post(
                            f"{API_BASE_URL}/parse",
                            files=files,
                            timeout=30
                        )

                        if response.status_code == 200:
                            result = response.json()
                            if result.get("success"):
                                data = result["data"]
                                if result.get("from_cache"):
                                    st.info("💡 该简历已缓存，直接读取缓存结果")
                                st.success("✅ 解析完成！")

                                # 个人信息
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.subheader("👤 个人信息")
                                    st.write(f"**姓名**：{data.get('name', '未识别')}")
                                    st.write(f"**邮箱**：{data.get('email', '未识别')}")
                                    st.write(f"**电话**：{data.get('phone', '未识别')}")
                                    st.write(f"**学历**：{data.get('education', '未识别')}")
                                with col_b:
                                    st.subheader("🛠️ 技能")
                                    skills = data.get('skills', [])
                                    if skills:
                                        st.write(", ".join(skills))
                                    else:
                                        st.write("未识别到技能关键词")

                                # 项目经历展示 - 优化排版
                                st.subheader("📁 项目经历")
                                projects = data.get('projects', [])
                                if projects:
                                    for i, proj in enumerate(projects, 1):
                                        with st.expander(f"📌 项目 {i}", expanded=(i == 1)):
                                            # 按句号/分号分割，分点展示
                                            sentences = proj.replace('；', '。').replace(';', '。').split('。')
                                            sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

                                            if sentences:
                                                for sent in sentences:
                                                    st.markdown(f"- {sent}")
                                            else:
                                                st.write(proj)
                                else:
                                    st.write("未识别到项目经历")

                                st.download_button(
                                    "📥 导出 JSON",
                                    data=json.dumps(data, ensure_ascii=False, indent=2),
                                    file_name=f"resume_parsed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                    mime="application/json"
                                )
                            else:
                                st.error(f"解析失败: {result.get('error', '未知错误')}")
                        else:
                            st.error(f"请求失败: {response.status_code}")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ 无法连接到后端服务")
                    except Exception as e:
                        st.error(f"❌ 发生错误: {str(e)}")

with tab2:
    st.subheader("🎯 简历与岗位匹配")
    col1, col2 = st.columns([1, 1])
    with col1:
        resume_file = st.file_uploader("上传简历 (PDF)", type=['pdf'], key="match_upload")
    with col2:
        jd_text = st.text_area(
            "📋 输入岗位描述",
            placeholder="例如：招聘Java后端开发工程师，熟悉Spring Boot、MySQL...",
            height=150
        )

    if st.button("📊 计算匹配度", type="primary", use_container_width=True):
        if resume_file is None:
            st.warning("请先上传简历")
        elif not jd_text or len(jd_text.strip()) < 5:
            st.warning("岗位描述至少5个字符")
        else:
            with st.spinner("正在分析匹配度..."):
                try:
                    files = {"file": (resume_file.name, resume_file.getvalue(), "application/pdf")}
                    data = {"job_description": jd_text}
                    response = requests.post(
                        f"{API_BASE_URL}/match",
                        files=files,
                        data=data,
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            data = result["data"]
                            if result.get("from_cache"):
                                st.info("💡 该简历已缓存，直接读取缓存结果")
                            resume_info = data["resume"]
                            match_info = data["match"]

                            score = match_info.get("score", 0)
                            st.metric("🎯 匹配度得分", f"{score}%")
                            st.progress(score / 100)

                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.subheader("👤 候选人信息")
                                st.write(f"**姓名**：{resume_info.get('name', '未识别')}")
                                st.write(f"**邮箱**：{resume_info.get('email', '未识别')}")
                                st.write(f"**学历**：{resume_info.get('education', '未识别')}")
                                st.write(f"**项目数**：{len(resume_info.get('projects', []))}")
                            with col_b:
                                st.subheader("🔗 匹配详情")
                                st.write(f"**匹配技能**：{', '.join(match_info.get('matched_skills', [])) or '无'}")
                                st.write(f"**岗位关键词**：{', '.join(match_info.get('jd_keywords', [])[:5])}")

                            st.download_button(
                                "📥 导出完整报告 (JSON)",
                                data=json.dumps(data, ensure_ascii=False, indent=2),
                                file_name=f"match_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                        else:
                            st.error(f"匹配失败: {result.get('error', '未知错误')}")
                    else:
                        st.error(f"请求失败: {response.status_code}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ 无法连接到后端服务")
                except Exception as e:
                    st.error(f"❌ 发生错误: {str(e)}")

st.divider()
st.caption("💡 提示：首次使用请先启动后端服务 (uvicorn main:app --reload)")