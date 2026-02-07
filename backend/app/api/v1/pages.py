"""
API для управления страницами, секциями и блоками (Block Builder)
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database import get_db
from app.models import Page, PageSection, ContentBlock

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class BlockCreate(BaseModel):
    block_type: str
    content: Dict[str, Any]
    css_classes: Optional[str] = None
    position: int = 0


class BlockUpdate(BaseModel):
    content: Optional[Dict[str, Any]] = None
    css_classes: Optional[str] = None
    position: Optional[int] = None
    is_visible: Optional[bool] = None


class SectionCreate(BaseModel):
    section_type: str
    background_style: str = "light"
    css_classes: Optional[str] = None
    container_width: str = "default"
    padding_y: str = "default"
    position: int = 0


class SectionUpdate(BaseModel):
    background_style: Optional[str] = None
    css_classes: Optional[str] = None
    container_width: Optional[str] = None
    padding_y: Optional[str] = None
    position: Optional[int] = None
    is_visible: Optional[bool] = None
    grid_columns: Optional[int] = None
    grid_gap: Optional[str] = None
    grid_style: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class SectionGridUpdate(BaseModel):
    """Тело запроса только для обновления сетки секции."""
    grid_columns: int = 2
    grid_gap: str = "medium"
    grid_style: str = "grid"


class PageUpdate(BaseModel):
    title: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    page_type: Optional[str] = None
    canonical_url: Optional[str] = None
    status: Optional[str] = None


# ============================================================================
# Sections API
# ============================================================================

@router.post("/pages/{page_id}/sections/")
async def create_section(
    page_id: int,
    section: SectionCreate,
    db: Session = Depends(get_db)
):
    """Создание новой секции"""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    new_section = PageSection(
        page_id=page_id,
        section_type=section.section_type,
        background_style=section.background_style,
        css_classes=section.css_classes,
        container_width=section.container_width,
        padding_y=section.padding_y,
        position=section.position
    )
    
    db.add(new_section)
    db.commit()
    db.refresh(new_section)
    
    return {"success": True, "section_id": new_section.id}


@router.put("/sections/{section_id}/")
async def update_section(
    section_id: int,
    section_update: SectionUpdate,
    db: Session = Depends(get_db)
):
    """Обновление секции"""
    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    data = section_update.model_dump(exclude_unset=True)
    if "settings" in data:
        current = section.settings if isinstance(section.settings, dict) else {}
        section.settings = {**current, **data["settings"]}
        flag_modified(section, "settings")
        del data["settings"]
    for field, value in data.items():
        setattr(section, field, value)
    db.add(section)
    db.commit()
    db.refresh(section)
    return {"success": True}


@router.patch("/sections/{section_id}/grid/")
async def update_section_grid(
    section_id: int,
    body: SectionGridUpdate,
    db: Session = Depends(get_db),
):
    """Обновление только настроек сетки секции. Отдельный endpoint."""
    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    section.grid_columns = body.grid_columns
    section.grid_gap = body.grid_gap
    section.grid_style = body.grid_style
    db.add(section)
    db.commit()
    db.refresh(section)
    return {
        "success": True,
        "grid_columns": section.grid_columns,
        "grid_gap": section.grid_gap,
        "grid_style": section.grid_style,
    }


@router.delete("/sections/{section_id}/")
async def delete_section(
    section_id: int,
    db: Session = Depends(get_db)
):
    """Удаление секции"""
    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    db.delete(section)
    db.commit()
    
    return {"success": True}


@router.post("/sections/reorder/")
async def reorder_sections(
    sections: List[Dict[str, int]],  # [{"id": 1, "position": 0}, ...]
    db: Session = Depends(get_db)
):
    """Изменение порядка секций"""
    for item in sections:
        section = db.query(PageSection).filter(PageSection.id == item["id"]).first()
        if section:
            section.position = item["position"]
    
    db.commit()
    
    return {"success": True}


# ============================================================================
# Blocks API
# ============================================================================

@router.post("/sections/{section_id}/blocks/")
async def create_block(
    section_id: int,
    block: BlockCreate,
    db: Session = Depends(get_db)
):
    """Создание нового блока"""
    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    new_block = ContentBlock(
        section_id=section_id,
        block_type=block.block_type,
        content=block.content,
        css_classes=block.css_classes,
        position=block.position
    )
    
    db.add(new_block)
    db.commit()
    db.refresh(new_block)
    
    return {
        "success": True,
        "block_id": new_block.id,
        "block": {
            "id": new_block.id,
            "block_type": new_block.block_type,
            "position": new_block.position,
            "content": new_block.content,
            "css_classes": new_block.css_classes,
            "is_visible": new_block.is_visible,
        }
    }


@router.put("/blocks/{block_id}/")
async def update_block(
    block_id: int,
    block_update: BlockUpdate,
    db: Session = Depends(get_db)
):
    """Обновление блока"""
    block = db.query(ContentBlock).filter(ContentBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    # Обновляем только переданные поля
    for field, value in block_update.dict(exclude_unset=True).items():
        setattr(block, field, value)
    
    db.commit()
    
    return {"success": True}


@router.delete("/blocks/{block_id}/")
async def delete_block(
    block_id: int,
    db: Session = Depends(get_db)
):
    """Удаление блока"""
    block = db.query(ContentBlock).filter(ContentBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    db.delete(block)
    db.commit()
    
    return {"success": True}


@router.post("/blocks/{block_id}/duplicate/")
async def duplicate_block(
    block_id: int,
    db: Session = Depends(get_db)
):
    """Копирование блока в той же секции (сразу после оригинала)"""
    import json
    block = db.query(ContentBlock).filter(ContentBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    # Копируем content через JSON, чтобы избежать проблем с типами SQLAlchemy/JSON
    raw = block.content
    try:
        content_copy = json.loads(json.dumps(raw)) if raw is not None else {}
    except (TypeError, ValueError):
        content_copy = {}
    if not isinstance(content_copy, dict):
        content_copy = {}
    max_pos = db.query(ContentBlock).filter(ContentBlock.section_id == block.section_id).count()
    new_block = ContentBlock(
        section_id=block.section_id,
        block_type=block.block_type,
        content=content_copy,
        css_classes=block.css_classes,
        position=max_pos,
        is_visible=block.is_visible,
    )
    db.add(new_block)
    db.commit()
    db.refresh(new_block)
    return {
        "success": True,
        "block": {
            "id": new_block.id,
            "block_type": new_block.block_type,
            "position": new_block.position,
            "content": new_block.content,
            "css_classes": new_block.css_classes,
            "is_visible": new_block.is_visible,
        },
    }


@router.post("/blocks/reorder/")
async def reorder_blocks(
    blocks: List[Dict[str, int]] = Body(..., embed=False),
    db: Session = Depends(get_db)
):
    """Изменение порядка блоков"""
    for item in blocks:
        block = db.query(ContentBlock).filter(ContentBlock.id == item["id"]).first()
        if block:
            block.position = item["position"]
    
    db.commit()
    
    return {"success": True}


# ============================================================================
# Pages API
# ============================================================================

@router.get("/pages/{page_id}/")
async def get_page(
    page_id: int,
    db: Session = Depends(get_db)
):
    """Получение страницы с секциями и блоками"""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return {
        "id": page.id,
        "slug": page.slug,
        "title": page.title,
        "status": page.status,
        "sections": [
            {
                "id": s.id,
                "section_type": s.section_type,
                "position": s.position,
                "background_style": s.background_style,
                "css_classes": s.css_classes,
                "container_width": getattr(s, "container_width", None) or "default",
                "settings": {
                    **(s.settings or {}),
                    "grid_columns": getattr(s, "grid_columns", 2),
                    "grid_gap": getattr(s, "grid_gap", "medium"),
                    "grid_style": getattr(s, "grid_style", "grid"),
                },
                "blocks": [
                    {
                        "id": b.id,
                        "block_type": b.block_type,
                        "position": b.position,
                        "content": b.content,
                        "css_classes": b.css_classes,
                        "is_visible": b.is_visible
                    }
                    for b in sorted(s.blocks, key=lambda x: x.position)
                ]
            }
            for s in sorted(page.sections, key=lambda x: x.position)
        ]
    }


@router.put("/pages/{page_id}/")
async def update_page(
    page_id: int,
    page_update: PageUpdate,
    db: Session = Depends(get_db)
):
    """Обновление метаданных страницы"""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Обновляем только переданные поля
    for field, value in page_update.model_dump(exclude_unset=True).items():
        setattr(page, field, value)
    
    db.commit()
    
    return {"success": True}
