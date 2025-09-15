from pydantic import BaseModel, Field
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class Item(BaseModel):
    id: int
    name: str
    price: int
    qty: int


class CheckoutRequest(BaseModel):
    address: str
    items: list[Item]
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None


class CheckoutResponse(BaseModel):
    order_id: str
    amount: int
    eta_days: Optional[int] = None
    eta_date: Optional[str] = None
    distance_km: Optional[int] = None


class PayRequest(BaseModel):
    order_id: str
    card_number: str = Field(..., description="Card number (demo mode)")
    exp_month: str
    exp_year: str
    name: str


class PayResponse(BaseModel):
    status: str
    message: str
    transaction_id: Optional[str] = None
    delivery_time: Optional[str] = None


class DeliveryEtaRequest(BaseModel):
    geo_lat: float
    geo_lon: float
    items: list[Item]


class DeliveryEtaResponse(BaseModel):
    distance_km: int
    eta_days: int
    eta_date: str


class ReviewIn(BaseModel):
    rating: int
    text: str
    author: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    product_id: str
    rating: int
    text: str
    author: Optional[str]
    created_at: str


class OrderItemOut(BaseModel):
    id: int
    name: str
    price: int
    qty: int


class OrderOut(BaseModel):
    order_id: str
    address: str
    amount: int
    created_at: str
    items: list[OrderItemOut]
    payment_status: Optional[str] = None
    payment_card_last4: Optional[str] = None
    payment_card_brand: Optional[str] = None
    payment_created_at: Optional[str] = None

