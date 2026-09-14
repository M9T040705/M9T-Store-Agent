"""知识库管理 API：文档上传/列表/详情/更新/删除/重建索引/统计。

文档存储：
- 原始文件：data/raw_docs/{doc_id}.md
- 元数据：data/kb_meta.json（doc_id, filename, category, title, created_at, updated_at, size, chunk_count）
- 向量索引：data/index.json（内存模式）或 Milvus（生产模式）
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from .config import settings
from .rag.chunker import StructuredChunker
from .rag.embedder import embedder
from .rag.vector_store import get_vector_store

router = APIRouter(prefix="/api/kb", tags=["知识库管理"])

# 目录
RAW_DOCS_DIR = settings.data_dir / "raw_docs"
META_PATH = settings.data_dir / "kb_meta.json"
RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------- 元数据管理 ----------------
def _load_meta() -> dict:
    if META_PATH.exists():
        with open(META_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_meta(meta: dict):
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def _guess_category(filename: str, content: str = "") -> str:
    """根据文件名和内容猜测文档分类。"""
    name = filename.lower()
    category_map = {
        "repair": "设备报修", "cashier": "收银操作", "refund": "退款流程",
        "coupon": "优惠券", "takeout": "外卖操作", "complaint": "客诉处理",
        "food": "食品操作", "hygiene": "卫生清洁", "inv": "物料库存",
        "inventory": "物料库存", "member": "会员管理", "promo": "促销活动",
        "sched": "排班考勤", "schedule": "排班考勤", "sop": "标准流程",
        "store": "门店管理", "train": "培训资料", "training": "培训资料",
    }
    for key, cat in category_map.items():
        if key in name:
            return cat
    return "其他"


def _extract_title(content: str, filename: str) -> str:
    """从文档内容提取标题（第一个 # 标题），否则用文件名。"""
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("# ") and not line.startswith("## "):
            return line.lstrip("# ").strip()
    return Path(filename).stem


# ---------------- Schema ----------------
class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None


class RebuildResponse(BaseModel):
    ok: bool
    total_chunks: int
    total_docs: int
    elapsed_ms: int


class StatsResponse(BaseModel):
    total_docs: int
    total_chunks: int
    categories: dict
    vector_store: str
    index_path: str
    last_rebuild: Optional[str] = None


# ---------------- API ----------------
@router.get("/documents")
def list_documents(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    category: str = "",
):
    """获取文档列表，支持分页、关键词搜索、分类筛选。"""
    meta = _load_meta()
    docs = list(meta.values())

    # 筛选
    if keyword:
        kw = keyword.lower()
        docs = [d for d in docs if kw in d.get("title", "").lower() or kw in d.get("filename", "").lower()]
    if category:
        docs = [d for d in docs if d.get("category") == category]

    # 按更新时间倒序
    docs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

    # 分页
    total = len(docs)
    start = (page - 1) * page_size
    end = start + page_size
    items = docs[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "items": items,
    }


@router.get("/documents/{doc_id}")
def get_document(doc_id: str):
    """获取文档详情和内容。"""
    meta = _load_meta()
    if doc_id not in meta:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    doc_info = meta[doc_id]
    file_path = RAW_DOCS_DIR / f"{doc_id}.md"
    content = ""
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

    return {**doc_info, "content": content}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(""),
    title: str = Form(""),
):
    """上传文档（支持 .md / .txt / .pdf）。"""
    filename = file.filename or "untitled.md"
    ext = Path(filename).suffix.lower()

    if ext not in (".md", ".txt", ".pdf"):
        raise HTTPException(status_code=400, detail=f"不支持的文件格式 {ext}，仅支持 .md / .txt / .pdf")

    # 读取内容
    raw = await file.read()
    if ext == ".pdf":
        try:
            import pymupdf
            pdf_doc = pymupdf.open(stream=raw, filetype="pdf")
            content = "\n\n".join(page.get_text("text") for page in pdf_doc)
            pdf_doc.close()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF 解析失败：{e}")
    else:
        content = raw.decode("utf-8", errors="ignore")

    # 生成 doc_id
    doc_id = f"doc-{int(time.time())}-{uuid.uuid4().hex[:8]}"

    # 保存文件
    file_path = RAW_DOCS_DIR / f"{doc_id}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    # 元数据
    doc_title = title or _extract_title(content, filename)
    doc_category = category or _guess_category(filename, content)
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    meta = _load_meta()
    meta[doc_id] = {
        "doc_id": doc_id,
        "filename": filename,
        "title": doc_title,
        "category": doc_category,
        "size": len(raw),
        "created_at": now,
        "updated_at": now,
        "chunk_count": 0,
    }
    _save_meta(meta)

    return {"ok": True, "doc_id": doc_id, "title": doc_title, "category": doc_category}


@router.put("/documents/{doc_id}")
def update_document(doc_id: str, req: DocumentUpdate):
    """更新文档标题、分类或内容。"""
    meta = _load_meta()
    if doc_id not in meta:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    file_path = RAW_DOCS_DIR / f"{doc_id}.md"
    content = ""
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

    if req.content is not None:
        content = req.content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    if req.title:
        meta[doc_id]["title"] = req.title
    if req.category:
        meta[doc_id]["category"] = req.category
    meta[doc_id]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _save_meta(meta)

    return {"ok": True, "doc_id": doc_id}


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """删除文档（同时删除文件和元数据）。"""
    meta = _load_meta()
    if doc_id not in meta:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    # 删除文件
    file_path = RAW_DOCS_DIR / f"{doc_id}.md"
    if file_path.exists():
        file_path.unlink()

    # 删除元数据
    del meta[doc_id]
    _save_meta(meta)

    return {"ok": True, "doc_id": doc_id, "message": "文档已删除，建议重建索引"}


@router.post("/rebuild", response_model=RebuildResponse)
def rebuild_index():
    """重建向量索引：遍历所有文档 → 分块 → 向量化 → 入库 → 持久化。"""
    t0 = time.time()
    meta = _load_meta()
    store, kind = get_vector_store()
    store.clear()

    total_chunks = 0
    processed_docs = 0

    for doc_id, doc_info in meta.items():
        file_path = RAW_DOCS_DIR / f"{doc_id}.md"
        if not file_path.exists():
            continue

        try:
            chunker = StructuredChunker()
            chunks = chunker.parse_file(file_path)
        except Exception as e:
            print(f"[rebuild] 分块失败 {doc_id}: {e}")
            continue

        if not chunks:
            continue

        texts = [c.text for c in chunks]
        try:
            vectors = embedder.embed(texts)
        except Exception as e:
            print(f"[rebuild] 向量化失败 {doc_id}: {e}")
            continue

        items = [c.to_dict() for c in chunks]
        store.add(items, vectors)
        total_chunks += len(chunks)
        processed_docs += 1

        # 更新元数据中的 chunk_count
        if doc_id in meta:
            meta[doc_id]["chunk_count"] = len(chunks)

    # 持久化
    if kind == "memory":
        store.save(settings.index_path)

    _save_meta(meta)

    elapsed_ms = int((time.time() - t0) * 1000)
    return RebuildResponse(
        ok=True,
        total_chunks=total_chunks,
        total_docs=processed_docs,
        elapsed_ms=elapsed_ms,
    )


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """获取知识库统计信息。"""
    meta = _load_meta()
    store, kind = get_vector_store()

    # 分类统计
    categories = {}
    for doc in meta.values():
        cat = doc.get("category", "其他")
        categories[cat] = categories.get(cat, 0) + 1

    # 最后重建时间（取索引文件修改时间）
    last_rebuild = None
    if settings.index_path.exists():
        last_rebuild = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(settings.index_path.stat().st_mtime))

    return StatsResponse(
        total_docs=len(meta),
        total_chunks=store.count(),
        categories=categories,
        vector_store=kind,
        index_path=str(settings.index_path),
        last_rebuild=last_rebuild,
    )


@router.get("/categories")
def get_categories():
    """获取所有文档分类列表。"""
    meta = _load_meta()
    categories = sorted(set(doc.get("category", "其他") for doc in meta.values()))
    return {"categories": categories}
