from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter()

# Pydantic models for request/response
class BrandBase(BaseModel):
    name: str
    description: str
    industry: str
    website: Optional[str] = None
    logo_url: Optional[str] = None

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None

class Brand(BrandBase):
    id: str
    slug: str
    contact_info: Optional[dict] = None
    brand_voice: Optional[dict] = None
    colors: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# In-memory storage for demo (replace with database)
brands_db = {}

def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from the brand name."""
    return name.lower().replace(' ', '-').replace('&', 'and')

@router.get("/", response_model=List[Brand])
async def list_brands():
    """Get all brands."""
    return list(brands_db.values())

@router.get("/{brand_id}", response_model=Brand)
async def get_brand(brand_id: str):
    """Get a specific brand by ID."""
    if brand_id not in brands_db:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brands_db[brand_id]

@router.post("/", response_model=Brand)
async def create_brand(brand: BrandCreate):
    """Create a new brand."""
    brand_id = str(uuid.uuid4())
    slug = generate_slug(brand.name)
    
    # Check if slug already exists
    for existing_brand in brands_db.values():
        if existing_brand.slug == slug:
            slug = f"{slug}-{brand_id[:8]}"
            break
    
    now = datetime.utcnow()
    new_brand = Brand(
        id=brand_id,
        slug=slug,
        name=brand.name,
        description=brand.description,
        industry=brand.industry,
        website=brand.website,
        logo_url=brand.logo_url,
        contact_info={},
        brand_voice={},
        colors={},
        created_at=now,
        updated_at=now
    )
    
    brands_db[brand_id] = new_brand
    return new_brand

@router.put("/{brand_id}", response_model=Brand)
async def update_brand(brand_id: str, brand_update: BrandUpdate):
    """Update an existing brand."""
    if brand_id not in brands_db:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    existing_brand = brands_db[brand_id]
    update_data = brand_update.dict(exclude_unset=True)
    
    # Update slug if name changed
    if "name" in update_data:
        update_data["slug"] = generate_slug(update_data["name"])
    
    update_data["updated_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(existing_brand, field, value)
    
    return existing_brand

@router.delete("/{brand_id}")
async def delete_brand(brand_id: str):
    """Delete a brand."""
    if brand_id not in brands_db:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    del brands_db[brand_id]
    return {"message": "Brand deleted successfully"}
