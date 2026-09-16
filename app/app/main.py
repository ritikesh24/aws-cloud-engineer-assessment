import logging

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Order
from .schemas import OrderCreate, OrderResponse


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Order Management API")


Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
):
    try:
        existing_order = (
            db.query(Order)
            .filter(Order.idempotency_key == order.idempotency_key)
            .first()
        )

        if existing_order:
            return existing_order

        new_order = Order(**order.model_dump())

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        logger.info("Order created: %s", new_order.id)

        return new_order

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Order already exists",
        )

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating order")

        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    try:
        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found",
            )

        return order

    except HTTPException:
        raise

    except SQLAlchemyError:
        logger.exception("Database error while retrieving order")

        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )