"""
简历解析模块：PDF提取 + 清洗 + 关键信息提取
优化：项目经历提取、教育背景完整解析、姓名去除前缀
"""
import re
import pdfplumber
from typing import Dict, List
from datetime import datetime


def extract_text_from_pdf(pdf_path: str) -> str:
    """从PDF中提取全文文本"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise ValueError(f"PDF解析失败: {str(e)}")
    if not text.strip():
        raise ValueError("PDF中未提取到文本内容")
    return text


def clean_text(text: str) -> str:
    """清洗文本"""
    text = re.sub(r'\n\s*\n', '\n', text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    text = re.sub(r' +', ' ', text)
    return text


def extract_name(text: str) -> str:
    """提取姓名 - 去除'姓名'前缀"""
    # 匹配 "姓名：xxx" 或 "姓名 xxx" 或 "姓名xxx"
    patterns = [
        r'姓名[：:]\s*([^\s]{2,4})',
        r'姓名\s+([^\s]{2,4})',
        r'姓名([^\s]{2,4})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            if len(name) >= 2 and len(name) <= 4:
                return name

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines[:5]:
        if len(line) >= 2 and len(line) <= 4:
            if not any(kw in line for kw in ['个人', '简历', '教育', '项目', '联系', '手机', '邮箱', '电话']):
                return line
    return "未识别"


def extract_phone(text: str) -> str:
    """提取手机号"""
    pattern = r'(?:\+?86)?\s*(1[3-9]\d{9})'
    match = re.search(pattern, text.replace(' ', ''))
    if match:
        return match.group(1)
    pattern = r'(\d{3,4}-\d{7,8})'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return "未识别"


def extract_email(text: str) -> str:
    """提取邮箱"""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else "未识别"


def extract_address(text: str) -> str:
    """提取地址"""
    patterns = [
        r'地址[：:]\s*([^\n]{5,30})',
        r'现居[：:]\s*([^\n]{5,30})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    provinces = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京', '天津', '重庆',
                 '哈尔滨', '长春', '沈阳', '大连', '青岛', '西安', '长沙', '郑州', '合肥', '南昌']
    for line in text.split('\n'):
        for p in provinces:
            if p in line and len(line) < 30:
                return line.strip()
    return "未识别"


def extract_job_intention(text: str) -> str:
    """提取求职意向"""
    patterns = [
        r'求职意向[：:]\s*([^\n]{2,20})',
        r'意向岗位[：:]\s*([^\n]{2,20})',
        r'应聘[：:]\s*([^\n]{2,20})',
        r'岗位[：:]\s*([^\n]{2,20})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    # 从技能中推断
    if '后端' in text and 'Java' in text:
        return 'Java后端开发'
    if '前端' in text and 'Vue' in text:
        return '前端开发'
    if 'Python' in text and '机器学习' in text:
        return 'AI/算法工程师'

    keywords = ['后端开发', '前端开发', '全栈', 'Java', 'Python', '算法', '测试', '运维']
    for line in text.split('\n'):
        for kw in keywords:
            if kw in line:
                return line.strip()
    return "未识别"


def extract_salary(text: str) -> str:
    """提取期望薪资"""
    patterns = [
        r'期望薪资[：:]\s*([^\n]{2,15})',
        r'薪资要求[：:]\s*([^\n]{2,15})',
        r'薪酬[：:]\s*([^\n]{2,15})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    pattern = r'(\d{4,6}\s*[-—]\s*\d{4,6})'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return "未填写"


def extract_work_years(text: str) -> str:
    """提取工作年限"""
    patterns = [
        r'工作年限[：:]\s*([^\n]{2,10})',
        r'(\d+)\s*年\s*工作',
        r'(\d+)\s*年\s*经验',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1) + '年' if '年' not in match.group(1) else match.group(1)

    # 从项目时间推断：找最近的年份，推算经历年数
    years = re.findall(r'20\d{2}', text)
    if years:
        latest = sorted(set(years))[-1]
        gap = datetime.now().year - int(latest)
        if gap >= 1:
            return f"{gap}年"
    return "在校生/未填写"


def extract_education(text: str) -> str:
    """提取完整学历背景 """
    keywords = ['本科', '硕士', '博士', '研究生', '学士', '大专', 'MBA']
    lines = text.split('\n')

    for line in lines:
        line_clean = line.strip()
        for kw in keywords:
            if kw in line_clean:
                # 尽量取整行，但不要超过60字符
                if len(line_clean) <= 60:
                    return line_clean
                else:
                    # 截取包含关键词的前后部分
                    idx = line_clean.find(kw)
                    start = max(0, idx - 20)
                    end = min(len(line_clean), idx + 40)
                    return line_clean[start:end].strip()
    return "未识别"


def extract_projects(text: str) -> List[str]:
    """提取项目经历 - 过滤掉获奖/奖学金信息"""
    projects = []
    lines = text.split('\n')
    # 获奖关键词（用于过滤）
    award_keywords = [
        '哈尔滨理工大学', '奖学金', '一等奖', '二等奖', '三等奖', '程序设计', '竞赛', '挑战杯',
        '获奖', '荣誉', '称号', '三好学生', '优秀学生', '新生', '校级', '省级', '国家级',
        '励志奖学金', '优秀', '大赛'
    ]

    project_lines = []
    in_project_section = False

    for i, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            continue

        # 跳过明显是获奖信息的行
        skip = False
        for kw in award_keywords:
            if kw in line_clean:
                skip = True
                break
        if skip:
            continue

        # 检测项目经历章节开始
        if '项目经历' in line_clean or '项目经验' in line_clean or '项目实践' in line_clean:
            in_project_section = True
            continue

        if in_project_section:
            section_end_keywords = ['教育背景', '技能', '获奖', '证书', '自我评价', '实习经历', '工作经历', '荣誉',
                                    '校园']
            if any(kw in line_clean for kw in section_end_keywords):
                in_project_section = False
                continue
            if ('项目' in line_clean or '系统' in line_clean or '平台' in line_clean or
                    re.search(r'20\d{2}', line_clean) or len(line_clean) > 25):
                project_lines.append(line_clean)

    # 备用方法：从全文找，但过滤获奖信息
    if not project_lines:
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            # 跳过获奖信息
            skip = False
            for kw in award_keywords:
                if kw in line_clean:
                    skip = True
                    break
            if skip:
                continue
            if ('项目' in line_clean or '系统' in line_clean or '平台' in line_clean) and len(line_clean) > 15:
                project_lines.append(line_clean)

    # 合并
    if project_lines:
        current = []
        for p in project_lines:
            if re.search(r'20\d{2}', p) or len(p) < 30:
                if current:
                    projects.append(' '.join(current))
                    current = []
            current.append(p)
        if current:
            projects.append(' '.join(current))

    # 去重过滤
    unique_projects = []
    seen = set()
    for p in projects:
        # 再次过滤：如果内容包含获奖关键词，跳过
        skip = False
        for kw in award_keywords:
            if kw in p:
                skip = True
                break
        if skip:
            continue
        if p not in seen and len(p) > 10:
            seen.add(p)
            unique_projects.append(p)

    return unique_projects[:6]


def extract_skills(text: str) -> List[str]:
    """提取技能 - 扩展技能库"""
    skill_keywords = [
        'Python', 'Java', 'C++', 'JavaScript', 'TypeScript', 'Spring', 'SpringBoot',
        'MyBatis', 'Hibernate', 'MySQL', 'PostgreSQL', 'Redis', 'MongoDB',
        'Docker', 'Kubernetes', 'Linux', 'Git', 'Vue', 'React', 'Angular',
        'WebSocket', 'FastAPI', 'Flask', 'Django', 'PyTorch', 'TensorFlow',
        'Kafka', 'RabbitMQ', 'Nginx', 'TCP/IP', 'RESTful', 'GraphQL',
        '微服务', '分布式', '高并发', '缓存', '消息队列', 'CI/CD', '云原生',
        'Android', 'iOS', 'Swift', 'Kotlin', 'Go', 'Rust', 'HTML', 'CSS',
        'Spring Cloud', 'Dubbo', 'Zookeeper', 'Elasticsearch', 'Logstash',
        'Kibana', 'Jenkins', 'GitLab', 'Jira', 'Confluence'
    ]
    found = []
    text_lower = text.lower()
    for skill in skill_keywords:
        if skill.lower() in text_lower:
            found.append(skill)

    # 补充推断
    if '后端' in text and '后端' not in found:
        found.append('后端')
    if '前端' in text and '前端' not in found:
        found.append('前端')

    return list(set(found))


def parse_resume(pdf_path: str) -> Dict:
    """完整解析简历"""
    raw_text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_text(raw_text)

    return {
        "raw_text": cleaned_text,
        "name": extract_name(cleaned_text),
        "phone": extract_phone(cleaned_text),
        "email": extract_email(cleaned_text),
        "address": extract_address(cleaned_text),
        "job_intention": extract_job_intention(cleaned_text),
        "salary": extract_salary(cleaned_text),
        "work_years": extract_work_years(cleaned_text),
        "education": extract_education(cleaned_text),
        "projects": extract_projects(cleaned_text),
        "skills": extract_skills(cleaned_text),
    }