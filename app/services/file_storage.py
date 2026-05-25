import os
import uuid
from fastapi import UploadFile
from typing import Optional, Set

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_DOCUMENT_TYPES = {"text/plain", "text/markdown"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB


def get_allowed_types(sub_dir: str) -> Set[str]:
    """根据上传目录获取允许的文件类型"""
    if sub_dir == "images":
        return ALLOWED_IMAGE_TYPES
    elif sub_dir == "documents":
        return ALLOWED_DOCUMENT_TYPES
    return ALLOWED_IMAGE_TYPES


def get_max_size(sub_dir: str) -> int:
    """根据上传目录获取最大文件大小"""
    if sub_dir == "images":
        return MAX_IMAGE_SIZE
    elif sub_dir == "documents":
        return MAX_DOCUMENT_SIZE
    return MAX_IMAGE_SIZE


async def save_upload_file(file: UploadFile, sub_dir: str = "images") -> dict:
    """保存上传的文件，返回文件信息"""
    allowed_types = get_allowed_types(sub_dir)
    max_size = get_max_size(sub_dir)

    if file.content_type not in allowed_types:
        raise ValueError(f"不支持的文件类型: {file.content_type}，仅支持: {', '.join(allowed_types)}")

    # 读取文件内容检查大小
    content = await file.read()
    if len(content) > max_size:
        raise ValueError(f"文件大小超过限制: {len(content) / 1024 / 1024:.2f}MB，最大 {max_size / 1024 / 1024}MB")

    # 生成唯一文件名
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{ext}"

    # 创建子目录
    dir_path = os.path.join(UPLOAD_DIR, sub_dir)
    os.makedirs(dir_path, exist_ok=True)

    # 保存文件
    filepath = os.path.join(dir_path, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    return {
        "url": f"/uploads/{sub_dir}/{filename}",
        "filename": filename,
        "original_name": file.filename,
        "size": len(content)
    }


def delete_file(file_url: str) -> bool:
    """删除指定路径的文件"""
    try:
        # 从 URL 中提取相对路径
        relative_path = file_url.lstrip("/")
        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), relative_path)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception:
        pass
    return False


def get_file_path(relative_url: str) -> Optional[str]:
    """获取文件的绝对路径"""
    relative_path = relative_url.lstrip("/")
    filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), relative_path)
    if os.path.exists(filepath):
        return filepath
    return None
