from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"


class TableStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    CLEANING = "cleaning"


class EmployeeRole(str, Enum):
    ADMIN = "admin"
    WAITER = "waiter"
    COOK = "cook"
    CASHIER = "cashier"


# Categorías del menú
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class Category(CategoryBase):
    id: int
    created_at: datetime


# Productos del menú
class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: int
    image_url: Optional[str] = None
    available: bool = True


class MenuItem(MenuItemBase):
    id: int
    created_at: datetime


# Items de un pedido
class OrderItemBase(BaseModel):
    menu_item_id: int
    quantity: int
    special_instructions: Optional[str] = None


class OrderItem(OrderItemBase):
    id: int
    unit_price: float
    subtotal: float


# Pedidos
class OrderBase(BaseModel):
    table_number: Optional[int] = None
    customer_name: Optional[str] = None
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemBase]
    waiter_id: Optional[int] = None


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    tip: Optional[float] = None
    discount: Optional[float] = None
    notes: Optional[str] = None
    cook_id: Optional[int] = None
    waiter_id: Optional[int] = None
    cashier_id: Optional[int] = None


class Order(OrderBase):
    id: int
    status: OrderStatus
    payment_status: Optional[PaymentStatus] = PaymentStatus.PENDING
    payment_method: Optional[PaymentMethod] = None
    subtotal: Optional[float] = 0
    tax: Optional[float] = 0
    tip: Optional[float] = 0
    discount: Optional[float] = 0
    total: float
    waiter_id: Optional[int] = None
    cook_id: Optional[int] = None
    cashier_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    prepared_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    items: List[OrderItem] = []


# ==================== TABLES ====================
class TableBase(BaseModel):
    number: int
    capacity: int = 4


class Table(TableBase):
    id: int
    status: TableStatus
    created_at: datetime


class TableUpdate(BaseModel):
    status: Optional[TableStatus] = None
    capacity: Optional[int] = None


# ==================== EMPLOYEES ====================
class EmployeeBase(BaseModel):
    name: str
    email: Optional[str] = None
    role: EmployeeRole


class EmployeeCreate(EmployeeBase):
    pin: str


class Employee(EmployeeBase):
    id: int
    active: bool
    created_at: datetime


class EmployeeLogin(BaseModel):
    pin: str


# ==================== PAYMENT ====================
class PaymentRequest(BaseModel):
    payment_method: PaymentMethod
    tip: float = 0
    discount: float = 0
    cashier_id: Optional[int] = None


# Comando de voz
class VoiceCommand(BaseModel):
    text: str
    language: str = "es-ES"


class VoiceCommandResponse(BaseModel):
    understood: bool
    action: Optional[str] = None
    items: List[dict] = []
    table_number: Optional[int] = None
    available_tables: Optional[List[int]] = None
    customer_name: Optional[str] = None
    message: str
    suggested_response: Optional[str] = None


# Transcripción de audio
class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: Optional[float] = None
