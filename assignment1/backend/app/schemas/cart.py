from pydantic import BaseModel
from typing import List, Optional


class CartItem(BaseModel):
    product_id: str
    quantity: int


class CartItemResponse(BaseModel):
    id: int
    product_id: str
    product_name: str
    price: float
    quantity: int
    vendor_id: str
    vendor_name: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    session_id: str
    items: List[CartItemResponse]
    subtotal: float
    discount: float
    shipping: float
    total: float
    discount_code: Optional[str] = None


class DiscountCodeRequest(BaseModel):
    code: str


class CartTotals(BaseModel):
    subtotal: float
    discount: float
    shipping: float
    total: float