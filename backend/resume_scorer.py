"""
简历评分模块：关键词提取 + 匹配度评分（含模拟AI加分）
"""
import re
from typing import Dict, List
from collections import Counter


# 技能权重
SKILL_WEIGHT = {
    'Python': 1.2, 'Java': 1.2, 'C++': 1.1, 'JavaScript': 1.0,
    'SpringBoot': 1.3, 'Spring': 1.2, 'MyBatis': 1.1, 'MySQL': 1.0,
    'Redis': 1.1, 'Docker': 1.0, 'Linux': 1.0, 'Vue': 1.0,
    'React': 1.0, 'FastAPI': 1.1, 'Flask': 1.0, 'PyTorch': 1.2,
    'TensorFlow': 1.2, '微服务': 1.3, '分布式': 1.3, '高并发': 1.3,
    '消息队列': 1.2, 'Kafka': 1.1, 'RabbitMQ': 1.1,
    '后端': 1.0, '前端': 1.0, '全栈': 1.2, '算法': 1.1,
}


def extract_jd_keywords(jd_text: str) -> List[str]:
    """从岗位描述中提取关键词（含权重）"""
    # 过滤出技术关键词
    tech_keywords = list(SKILL_WEIGHT.keys())

    matched = []
    for kw in tech_keywords:
        if kw.lower() in jd_text.lower():
            matched.append(kw)

    # 如果匹配太少，用正则提取
    if len(matched) < 3:
        words = re.findall(r'[A-Za-z#+]{2,}', jd_text)
        stopwords = {'and', 'or', 'the', 'for', 'with', 'from', 'our', 'team', 'work', 'we', 'are'}
        words = [w for w in words if len(w) > 2 and w.lower() not in stopwords]
        from collections import Counter
        counter = Counter(words)
        top = [k for k, _ in counter.most_common(10)]
        matched.extend(top)

    return list(set(matched))


def calculate_match_score(resume_data: Dict, jd_text: str) -> Dict:
    """
    计算匹配度评分（含模拟AI加分）
    评分维度：
    - 技能匹配率（50%）
    - 工作经验相关性（20%）
    - 学历匹配（15%）
    - 项目经验质量（10%）
    - AI模拟加分（5%）
    """
    if not jd_text or len(jd_text.strip()) < 5:
        return {
            "score": 0,
            "details": "岗位描述不能为空",
            "matched_skills": [],
            "score_breakdown": {}
        }

    resume_skills = resume_data.get('skills', [])
    jd_keywords = extract_jd_keywords(jd_text)

    if not jd_keywords:
        return {
            "score": 0,
            "details": "岗位描述中未提取到有效关键词",
            "matched_skills": [],
            "jd_keywords": [],
            "resume_skills": resume_skills,
            "score_breakdown": {}
        }

    # ========== 1. 技能匹配率（50分）==========
    matched_skills = []
    weighted_total = 0
    weighted_match = 0

    for kw in jd_keywords:
        weight = SKILL_WEIGHT.get(kw, 1.0)
        weighted_total += weight
        for rs in resume_skills:
            if kw.lower() in rs.lower() or rs.lower() in kw.lower():
                matched_skills.append(kw)
                weighted_match += weight
                break

    skill_score = (weighted_match / weighted_total * 50) if weighted_total > 0 else 0

    # ========== 2. 工作经验相关性（20分）==========
    work_years = resume_data.get('work_years', '')
    years = re.findall(r'(\d+)', work_years)

    if years and int(years[0]) >= 3:
        exp_score = 18 + min(int(years[0]) * 0.5, 2)  # 3年以上给18-20分
    elif years and int(years[0]) >= 1:
        exp_score = 10 + int(years[0]) * 3
    elif years:
        exp_score = 5
    else:
        # 从项目经历推断
        projects = resume_data.get('projects', [])
        if len(projects) >= 3:
            exp_score = 15
        elif len(projects) >= 1:
            exp_score = 8
        else:
            exp_score = 5
    exp_score = min(exp_score, 20)

    # ========== 3. 学历匹配（15分）==========
    edu = resume_data.get('education', '')
    edu_score = 0
    if '博士' in edu or 'PhD' in edu:
        edu_score = 15
    elif '硕士' in edu or 'Master' in edu or '研究生' in edu:
        edu_score = 13
    elif '本科' in edu or 'Bachelor' in edu or '学士' in edu:
        edu_score = 10
    elif '大专' in edu:
        edu_score = 6
    else:
        # 有无大学关键词
        if '大学' in edu or '学院' in edu:
            edu_score = 8
        else:
            edu_score = 5

    # ========== 4. 项目经验质量（10分）==========
    projects = resume_data.get('projects', [])
    if projects:
        proj_text = ' '.join(projects)
        # 项目数量和质量
        quality_score = min(len(projects) * 2, 6)
        # 包含技术栈加分
        tech_in_proj = 0
        for skill in resume_skills:
            if skill.lower() in proj_text.lower():
                tech_in_proj += 1
        quality_score += min(tech_in_proj * 0.5, 4)
        proj_score = min(quality_score, 10)
    else:
        proj_score = 2  # 没有项目经历最低分

    # ========== 5. AI模拟加分（5分）==========
    # 用文本复杂度模拟AI评分：简历文本越长、关键词越多，质量越高
    raw_text = resume_data.get('raw_text', '')
    text_len = len(raw_text)
    ai_bonus = 0
    if text_len > 5000:
        ai_bonus = 5
    elif text_len > 3000:
        ai_bonus = 4
    elif text_len > 1500:
        ai_bonus = 3
    elif text_len > 500:
        ai_bonus = 1

    # 技能越多，AI加分越高
    ai_bonus += min(len(resume_skills) * 0.2, 2)
    ai_bonus = min(ai_bonus, 5)

    # ========== 总分 ==========
    final_score = skill_score + exp_score + edu_score + proj_score + ai_bonus
    final_score = round(min(final_score, 100), 1)

    return {
        "score": final_score,
        "skill_match_score": round(skill_score, 1),
        "experience_score": round(exp_score, 1),
        "education_score": round(edu_score, 1),
        "project_score": round(proj_score, 1),
        "ai_bonus_score": round(ai_bonus, 1),
        "matched_skills": list(set(matched_skills)),
        "jd_keywords": jd_keywords[:15],
        "resume_skills": resume_skills,
        "details": f"技能匹配{round(skill_score,1)}分 + 经验{round(exp_score,1)}分 + 学历{round(edu_score,1)}分 + 项目{round(proj_score,1)}分 + AI加分{round(ai_bonus,1)}分"
    }