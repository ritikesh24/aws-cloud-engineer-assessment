from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    customer_id: str = Field(min_length=1)
    product: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    amount: float = Field(gt=0)
    idempotency_key: str = Field(min_length=1)


class OrderResponse(BaseModel):
    id: int
    customer_id: str
    product: str
    quantity: int
    amount: float
    idempotency_key: str

    class Config:
        from_attributes = True