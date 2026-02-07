"""
API для управления категориями статей, их секциями и блоками
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ArticleCategory, CategorySection, CategoryBlock

router = APIRouter()


# ============================================================================
# Pydantic models
# ============================================================================

class CategorySectionCreate(BaseModel):
    section_type: str
    background_style: str = "light"
    css_classes: Optional[str] = None
    container_width: str = "default"
    padding_y: str = "default"
    position: int = 0


class CategorySectionUpdate(BaseModel):
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


class CategoryBlockCreate(BaseModel):
    block_type: str
    content: Dict[str, Any]
    css_classes: Optional[str] = None
    position: int = 0


class CategoryBlockUpdate(BaseModel):
    content: Optional[Dict[str, Any]] = None
    css_classes: Optional[str] = None
    position: Optional[int] = None
    is_visible: Optional[bool] = None


# ============================================================================
# Category sections
# ============================================================================

@router.post("/categories/{category_id}/sections/")
async def create_category_section(
    category_id: int,
    body: CategorySectionCreate,
    db: Session = Depends(get_db),
):
    """Создание секции категории"""
    cat = db.query(ArticleCategory).filter(ArticleCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    max_pos = db.query(CategorySection).filter(CategorySection.category_id == category_id).count()
    section = CategorySection(
        category_id=category_id,
        section_type=body.section_type,
        background_style=body.background_style,
        css_classes=body.css_classes,
        container_width=body.container_width,
        padding_y=body.padding_y,
        position=body.position if body.position >= 0 else max_pos,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return {"success": True, "section_id": section.id}


@router.put("/category-sections/{section_id}/")
async def update_category_section(
    section_id: int,
    body: CategorySectionUpdate,
    db: Session = Depends(get_db),
):
    """Обновление секции категории"""
    section = db.query(CategorySection).filter(CategorySection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    data = body.model_dump(exclude_unset=True)
    if "settings" in data:
        current = section.settings if isinstance(section.settings, dict) else {}
        section.settings = {**current, **(data["settings"] or {})}
        del data["settings"]
    for k, v in data.items():
        setattr(section, k, v)
    db.commit()
    db.refresh(section)
    return {"success": True}


@router.delete("/category-sections/{section_id}/")
async def delete_category_section(
    section_id: int,
    db: Session = Depends(get_db),
):
    """Удаление секции категории"""
    section = db.query(CategorySection).filter(CategorySection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    db.delete(section)
    db.commit()
    return {"success": True}


# ============================================================================
# Category blocks
# ============================================================================

@router.post("/category-sections/{section_id}/blocks/")
async def create_category_block(
    section_id: int,
    body: CategoryBlockCreate,
    db: Session = Depends(get_db),
):
    """Создание блока в секции категории"""
    section = db.query(CategorySection).filter(CategorySection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    max_pos = db.query(CategoryBlock).filter(CategoryBlock.section_id == section_id).count()
    block = CategoryBlock(
        section_id=section_id,
        block_type=body.block_type,
        content=body.content,
        css_classes=body.css_classes,
        position=body.position if body.position >= 0 else max_pos,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return {"success": True, "block": {"id": block.id, "block_type": block.block_type, "position": block.position, "content": block.content, "css_classes": block.css_classes, "is_visible": block.is_visible}}


@router.put("/category-blocks/{block_id}/")
async def update_category_block(
    block_id: int,
    body: CategoryBlockUpdate,
    db: Session = Depends(get_db),
):
    """Обновление блока категории"""
    block = db.query(CategoryBlock).filter(CategoryBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(block, k, v)
    db.commit()
    db.refresh(block)
    return {"success": True, "block": {"id": block.id, "block_type": block.block_type, "position": block.position, "content": block.content, "css_classes": block.css_classes, "is_visible": block.is_visible}}


@router.delete("/category-blocks/{block_id}/")
async def delete_category_block(
    block_id: int,
    db: Session = Depends(get_db),
):
    """Удаление блока категории"""
    block = db.query(CategoryBlock).filter(CategoryBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    db.delete(block)
    db.commit()
    return {"success": True}


@router.post("/categories/blocks/reorder/")
async def reorder_category_blocks(
    blocks: List[Dict[str, int]],
    db: Session = Depends(get_db),
):
    """Перестановка блоков. Body: [{"id": 1, "position": 0}, ...]"""
    for item in blocks:
        bid = item.get("id")
        pos = item.get("position", 0)
        if bid is None:
            continue
        block = db.query(CategoryBlock).filter(CategoryBlock.id == bid).first()
        if block:
            block.position = pos
    db.commit()
    return {"success": True}
