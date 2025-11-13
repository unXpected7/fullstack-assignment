from pydantic import BaseModel
from typing import Optional, Dict


class ProductServiceConfig(BaseModel):
    endpoint: str
    api_key: Optional[str] = None
    headers: Optional[Dict] = None


class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    vendor_id: str
    vendor_name: str
    image_url: Optional[str] = None