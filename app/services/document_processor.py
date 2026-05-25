import os
import json
import httpx
from typing import List, Tuple
from app.core.config import settings


def parse_document(file_path: str, file_type: str) -> str:
    """解析文档内容"""
    if file_type == "txt" or file_type == "md":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_type == "pdf":
        # 简单的 PDF 文本提取
        # 生产环境建议使用 pypdf 或 pdfplumber
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            # 如果没有 pypdf，使用简单方法
            with open(file_path, "rb") as f:
                content = f.read()
                # 尝试提取可见文本（简化处理）
                text = content.decode("utf-8", errors="ignore")
                # 移除不可见字符
                import re
                text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
                return text
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """将文本分割成重叠的块"""
    if not text or not text.strip():
        return []

    # 按句子分割，避免在句子中间断开
    import re
    sentences = re.split(r'([。！？.!?\n])', text)

    chunks = []
    current_chunk = ""
    current_size = 0

    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i]
        punct = sentences[i + 1] if i + 1 < len(sentences) else ""

        sentence_with_punct = sentence + punct
        sentence_len = len(sentence_with_punct)

        # 如果单个句子超过 chunk_size，直接添加
        if sentence_len > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = ""
            current_size = 0
            # 将长句子分割成更小的块
            for j in range(0, len(sentence), chunk_size - overlap):
                chunk_piece = sentence[j:j + chunk_size]
                if chunk_piece.strip():
                    chunks.append(chunk_piece.strip())
            current_chunk = ""
            current_size = 0
            continue

        if current_size + sentence_len > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # 保留 overlap 长度的内容作为重叠部分
            current_chunk = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_size = len(current_chunk)

        current_chunk += sentence_with_punct
        current_size += sentence_len

    # 添加最后一个 chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def count_tokens(text: str) -> int:
    """简单估算 token 数量（中文按字数，英文按单词）"""
    # 中文：每个字约 1-2 token
    # 英文：每个单词约 1.3 token
    import re
    chinese_chars = len(re.findall(r'[一-鿿]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    other = len(text) - chinese_chars - len(re.findall(r'[a-zA-Z]', text))

    return int(chinese_chars * 1.5 + english_words * 1.3 + other * 1)


async def generate_embedding(text: str) -> List[float]:
    """调用 MiniMax API 生成文本 embedding"""
    if not settings.MINIMAX_API_KEY:
        raise ValueError("MiniMax API 密钥未配置")

    headers = {
        "Authorization": f"Bearer {settings.MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "emb0",
        "texts": [text],
        "type": "db"
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.MINIMAX_BASE_URL}/embeddings",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()

            # 检查 API 返回错误
            base_resp = result.get("base_resp", {})
            if base_resp and base_resp.get("status_code", 0) != 0:
                error_msg = base_resp.get("status_msg", "未知错误")
                raise ValueError(f"MiniMax Embedding API 错误: {error_msg}")

            # 检查返回数据 - MiniMax 可能返回 vectors 字段而不是 data
            if "vectors" in result and result["vectors"]:
                return result["vectors"][0]["embedding"]
            elif "data" in result and result["data"]:
                return result["data"][0]["embedding"]
            else:
                raise ValueError(f"Embedding API 返回格式错误: {result}")
    except httpx.HTTPError as e:
        raise ValueError(f"HTTP 请求失败: {e}")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    if len(a) != len(b):
        raise ValueError("向量维度不一致")

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def serialize_embedding(embedding: List[float]) -> str:
    """将 embedding 向量序列化为 JSON 字符串"""
    return json.dumps(embedding)


def deserialize_embedding(embedding_str: str) -> List[float]:
    """从 JSON 字符串反序列化 embedding"""
    return json.loads(embedding_str)
