"""
FastAPI 主服务
所有功能：解析 + 信息提取 + 评分匹配 + 缓存
"""
import os
import uuid
import shutil
import json
import hashlib
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from resume_parser import parse_resume
from resume_scorer import calculate_match_score

# ========== 缓存：用内存字典模拟Redis ==========
# 生产环境可替换为 Redis，这里用字典 + 时间戳实现LRU风格
CACHE = {}
CACHE_MAX_SIZE = 50

def get_cache_key(file_content: bytes, jd_text: str = "") -> str:
    """生成缓存key：文件内容哈希 + 岗位描述哈希"""
    content_hash = hashlib.md5(file_content).hexdigest()
    jd_hash = hashlib.md5(jd_text.encode()).hexdigest() if jd_text else ""
    return f"{content_hash}_{jd_hash}"

def get_from_cache(key: str) -> Dict:
    """从缓存获取"""
    if key in CACHE:
        return CACHE[key]
    return None

def set_to_cache(key: str, value: Dict):
    """存入缓存，超限时淘汰最旧的"""
    global CACHE
    if len(CACHE) >= CACHE_MAX_SIZE:
        # 删除第一个（简单淘汰）
        first_key = list(CACHE.keys())[0]
        del CACHE[first_key]
    CACHE[key] = value

# ========== FastAPI App ==========
app = FastAPI(
    title="AI 简历分析系统 API",
    description="上传PDF简历，自动提取信息并匹配岗位",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class ParseResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = None
    error: str = None
    from_cache: bool = False


class MatchResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = None
    error: str = None
    from_cache: bool = False


@app.get("/")
def health_check():
    return {"status": "ok", "message": "简历分析服务运行中", "cache_size": len(CACHE)}


@app.post("/parse", response_model=ParseResponse)
async def parse_resume_file(file: UploadFile = File(...)):
    """上传并解析简历（带缓存）"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持PDF格式")

    # 读取文件内容（用于缓存key）
    file_content = await file.read()
    file.file.seek(0)

    cache_key = get_cache_key(file_content)
    cached = get_from_cache(cache_key)
    if cached:
        return ParseResponse(
            success=True,
            data=cached,
            from_cache=True
        )

    temp_id = str(uuid.uuid4())[:8]
    temp_path = os.path.join(UPLOAD_DIR, f"{temp_id}_{file.filename}")

    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = parse_resume(temp_path)

        # 存入缓存
        set_to_cache(cache_key, result)

        return ParseResponse(success=True, data=result, from_cache=False)

    except ValueError as e:
        return ParseResponse(success=False, error=str(e))

    except Exception as e:
        return ParseResponse(success=False, error=f"解析失败: {str(e)}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/match", response_model=MatchResponse)
async def match_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    """上传简历并匹配岗位（带缓存）"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持PDF格式")

    if not job_description or len(job_description.strip()) < 5:
        return MatchResponse(
            success=False,
            error="岗位描述不能为空，且至少5个字符"
        )

    file_content = await file.read()
    file.file.seek(0)

    cache_key = get_cache_key(file_content, job_description)
    cached = get_from_cache(cache_key)
    if cached:
        return MatchResponse(
            success=True,
            data=cached,
            from_cache=True
        )

    temp_id = str(uuid.uuid4())[:8]
    temp_path = os.path.join(UPLOAD_DIR, f"{temp_id}_{file.filename}")

    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        resume_data = parse_resume(temp_path)
        match_result = calculate_match_score(resume_data, job_description)

        response_data = {
            "resume": resume_data,
            "match": match_result
        }

        set_to_cache(cache_key, response_data)

        return MatchResponse(
            success=True,
            data=response_data,
            from_cache=False
        )

    except ValueError as e:
        return MatchResponse(success=False, error=str(e))

    except Exception as e:
        return MatchResponse(success=False, error=f"匹配失败: {str(e)}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/cache/clear")
async def clear_cache():
    """清空缓存（管理接口）"""
    global CACHE
    CACHE = {}
    return {"status": "cleared", "message": "缓存已清空"}


@app.get("/cache/status")
async def cache_status():
    """查看缓存状态"""
    return {"cache_size": len(CACHE), "max_size": CACHE_MAX_SIZE}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)