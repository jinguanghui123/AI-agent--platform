import os
import json
import re
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.knowledge import Document, Chunk
from app.models.user import User
from app.services.document_processor import (
    parse_document,
    chunk_text,
    count_tokens,
    generate_embedding,
    serialize_embedding,
    deserialize_embedding,
    cosine_similarity
)
from app.services.file_storage import save_upload_file


def extract_keywords(text: str) -> set:
    """从文本中提取关键词（中文和英文）"""
    # 移除标点符号，替换为空格
    text = re.sub(r'[^\w\s]', ' ', text)

    # 提取中文词语（2-4个连续汉字）
    chinese_words = set(re.findall(r'[一-鿿]{2,4}', text))
    # 提取英文单词
    english_words = set(re.findall(r'[a-zA-Z]{2,}', text.lower()))

    # 合并并过滤停用词
    stopwords = {'的', '了', '和', '是', '在', '我', '有', '这个', '那个', '它', '与', '或', '以', '及', '等', '为', '上', '下', '中', '也', '都', '要', '会', '能', '可以', '一个', '使用', '使用', 'which', 'that', 'this', 'with', 'for', 'from', 'have', 'are', 'was', 'were', 'been', 'being'}
    keywords = set()

    for w in chinese_words:
        if w not in stopwords:
            keywords.add(w)

    for w in english_words:
        if w not in stopwords:
            keywords.add(w)

    return keywords


def keyword_similarity(query: str, chunk_content: str) -> float:
    """基于关键词的相似度计算"""
    query_keywords = extract_keywords(query)
    chunk_keywords = extract_keywords(chunk_content)

    if not query_keywords:
        return 0.0

    # 计算重叠的关键词数量
    overlap = query_keywords & chunk_keywords
    return len(overlap) / len(query_keywords)


class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db

    async def add_document(self, user_id: int, file: UploadFile, custom_filename: str = None) -> Document:
        """上传并处理文档"""
        # 保存文件
        file_ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
        if file_ext not in ["txt", "md"]:
            raise ValueError(f"不支持的文件类型: {file_ext}，仅支持: txt, md（MVP阶段暂不支持PDF）")

        # 保存到 documents 目录
        result = await save_upload_file(file, sub_dir="documents")
        file_path = result["url"]

        # 解析文档
        abs_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            file_path.lstrip("/")
        )
        text = parse_document(abs_file_path, file_ext)

        if not text or len(text.strip()) < 10:
            raise ValueError("文档内容为空或无法解析")

        # 分块
        chunks = chunk_text(text, chunk_size=500, overlap=50)

        # 限制最大 chunks 数量
        max_chunks = 100
        if len(chunks) > max_chunks:
            chunks = chunks[:max_chunks]

        # 创建文档记录
        doc = Document(
            user_id=user_id,
            filename=custom_filename or file.filename,
            file_path=file_path,
            file_type=file_ext,
            file_size=result["size"],
            chunk_count=len(chunks)
        )
        self.db.add(doc)
        self.db.flush()  # 获取 doc.id

        # 处理每个 chunk
        for idx, chunk_content in enumerate(chunks):
            # 生成 embedding
            try:
                embedding = await generate_embedding(chunk_content)
                embedding_str = serialize_embedding(embedding)
            except Exception as e:
                print(f"生成 embedding 失败: {e}")
                embedding_str = None

            chunk = Chunk(
                document_id=doc.id,
                content=chunk_content,
                chunk_index=idx,
                embedding=embedding_str,
                token_count=count_tokens(chunk_content)
            )
            self.db.add(chunk)

        self.db.commit()
        self.db.refresh(doc)
        return doc

    def list_documents(self, user_id: int) -> List[Document]:
        """列出用户的所有文档"""
        return self.db.query(Document).filter(
            Document.user_id == user_id
        ).order_by(Document.created_at.desc()).all()

    def get_document(self, doc_id: int, user_id: int) -> Optional[Document]:
        """获取文档详情"""
        return self.db.query(Document).filter(
            Document.id == doc_id,
            Document.user_id == user_id
        ).first()

    def delete_document(self, doc_id: int, user_id: int) -> bool:
        """删除文档及其 chunks"""
        doc = self.get_document(doc_id, user_id)
        if not doc:
            return False

        # 删除 chunks
        self.db.query(Chunk).filter(Chunk.document_id == doc_id).delete()

        # 删除文档
        self.db.delete(doc)
        self.db.commit()

        # 删除文件
        try:
            from app.services.file_storage import delete_file
            delete_file(doc.file_path)
        except Exception as e:
            print(f"删除文件失败: {e}")

        return True

    async def search_chunks(self, user_id: int, query: str, top_k: int = 5) -> List[dict]:
        """搜索与查询相关的 chunks（使用关键词匹配）"""
        # 获取用户的所有 chunks
        chunks = self.db.query(Chunk).join(Document).filter(
            Document.user_id == user_id
        ).all()

        # 使用关键词匹配计算相似度
        scored_chunks = []
        for chunk in chunks:
            similarity = keyword_similarity(query, chunk.content)
            scored_chunks.append({
                "chunk": chunk,
                "similarity": similarity
            })

        # 排序并取 top_k
        scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        top_chunks = scored_chunks[:top_k]

        return [
            {
                "id": item["chunk"].id,
                "content": item["chunk"].content,
                "similarity": item["similarity"],
                "document_id": item["chunk"].document_id,
                "chunk_index": item["chunk"].chunk_index
            }
            for item in top_chunks
        ]

    def build_rag_context(self, chunks: List[dict]) -> str:
        """构建 RAG 上下文"""
        if not chunks:
            return ""

        context = "参考信息：\n\n"
        for i, chunk in enumerate(chunks, 1):
            context += f"[{i}] {chunk['content']}\n\n"
        return context.strip()

    def get_document_chunks(self, doc_id: int, user_id: int) -> List[Chunk]:
        """获取文档的所有 chunks"""
        doc = self.get_document(doc_id, user_id)
        if not doc:
            return []

        return self.db.query(Chunk).filter(
            Chunk.document_id == doc_id
        ).order_by(Chunk.chunk_index).all()
