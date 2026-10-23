"""Synthetic retail dataset seeding script for QueryPilot.

Provides realistic, idempotent demo data across customers, products, orders,
and order_items to support analytical questions (grouping, filtering, quarterly trends, joins).
"""

from datetime import datetime, timedelta
from decimal import Decimal
import logging
from typing import Optional
from sqlalchemy import Engine, inspect, select, func
from sqlalchemy.orm import Session
from app.database.connection import get_engine
from app.database.models import Base, Customer, Product, Order, OrderItem

logger = logging.getLogger("querypilot.demo_seed")

CUSTOMERS_DATA = [
    {"customer_name": "Apex Retailers", "region": "North", "city": "Chicago", "created_at": datetime(2025, 1, 15)},
    {"customer_name": "Beacon Global", "region": "North", "city": "Minneapolis", "created_at": datetime(2025, 2, 10)},
    {"customer_name": "Cascade Ventures", "region": "West", "city": "Seattle", "created_at": datetime(2025, 1, 20)},
    {"customer_name": "Delta Systems", "region": "South", "city": "Austin", "created_at": datetime(2025, 3, 5)},
    {"customer_name": "Echo Dynamics", "region": "East", "city": "New York", "created_at": datetime(2025, 1, 12)},
    {"customer_name": "Falcon Holdings", "region": "South", "city": "Atlanta", "created_at": datetime(2025, 2, 18)},
    {"customer_name": "Granite Corp", "region": "East", "city": "Boston", "created_at": datetime(2025, 3, 22)},
    {"customer_name": "Horizon Logistics", "region": "West", "city": "San Francisco", "created_at": datetime(2025, 1, 25)},
    {"customer_name": "Ironclad Industries", "region": "North", "city": "Detroit", "created_at": datetime(2025, 4, 2)},
    {"customer_name": "Juniper Enterprise", "region": "West", "city": "Denver", "created_at": datetime(2025, 2, 28)},
    {"customer_name": "Keystone Media", "region": "East", "city": "Philadelphia", "created_at": datetime(2025, 3, 14)},
    {"customer_name": "Luminary Tech", "region": "South", "city": "Miami", "created_at": datetime(2025, 4, 10)},
    {"customer_name": "Matrix Distribution", "region": "South", "city": "Dallas", "created_at": datetime(2025, 1, 30)},
    {"customer_name": "Nexus Partners", "region": "West", "city": "Portland", "created_at": datetime(2025, 2, 14)},
    {"customer_name": "Olympus Supply", "region": "North", "city": "Milwaukee", "created_at": datetime(2025, 3, 1)}
]

PRODUCTS_DATA = [
    {"product_name": "UltraBook Pro 15", "category": "Electronics", "unit_price": Decimal("1299.99")},
    {"product_name": "Wireless Noise-Canceling Headphones", "category": "Electronics", "unit_price": Decimal("249.50")},
    {"product_name": "4K Ultra-HD Monitor 27-inch", "category": "Electronics", "unit_price": Decimal("399.00")},
    {"product_name": "Ergonomic Mechanical Keyboard", "category": "Electronics", "unit_price": Decimal("129.00")},
    {"product_name": "Precision Wireless Mouse", "category": "Electronics", "unit_price": Decimal("59.99")},
    {"product_name": "Executive Standing Desk", "category": "Furniture", "unit_price": Decimal("650.00")},
    {"product_name": "Ergonomic Mesh Office Chair", "category": "Furniture", "unit_price": Decimal("320.00")},
    {"product_name": "Modular Bookshelf 5-Tier", "category": "Furniture", "unit_price": Decimal("180.00")},
    {"product_name": "Filing Cabinet with Lock", "category": "Furniture", "unit_price": Decimal("145.00")},
    {"product_name": "Recycled Copy Paper (Carton)", "category": "Office Supplies", "unit_price": Decimal("48.50")},
    {"product_name": "Gel Ink Pens (Box of 50)", "category": "Office Supplies", "unit_price": Decimal("22.00")},
    {"product_name": "Heavy-Duty Desk Stapler", "category": "Office Supplies", "unit_price": Decimal("18.75")},
    {"product_name": "Dry Erase Glass Whiteboard", "category": "Office Supplies", "unit_price": Decimal("95.00")},
    {"product_name": "USB-C Multiport Docking Station", "category": "Accessories", "unit_price": Decimal("89.99")},
    {"product_name": "Braided HDMI 2.1 Cable 6ft", "category": "Accessories", "unit_price": Decimal("19.99")}
]

# (customer_idx, order_date, status, [(product_idx, qty, price_mult, discount)])
ORDER_RECIPES = [
    # Q1 2025 Orders
    (0, datetime(2025, 1, 22), "completed", [(0, 3, Decimal("1.0"), Decimal("50.00")), (2, 2, Decimal("1.0"), Decimal("0.00"))]),
    (1, datetime(2025, 1, 28), "completed", [(5, 2, Decimal("1.0"), Decimal("30.00")), (6, 4, Decimal("1.0"), Decimal("20.00"))]),
    (2, datetime(2025, 2, 5), "completed", [(1, 5, Decimal("1.0"), Decimal("25.00")), (3, 5, Decimal("1.0"), Decimal("10.00"))]),
    (3, datetime(2025, 2, 14), "completed", [(9, 10, Decimal("1.0"), Decimal("15.00")), (10, 8, Decimal("1.0"), Decimal("5.00"))]),
    (4, datetime(2025, 2, 22), "completed", [(0, 2, Decimal("1.0"), Decimal("100.00")), (13, 4, Decimal("1.0"), Decimal("0.00"))]),
    (5, datetime(2025, 3, 2), "completed", [(6, 3, Decimal("1.0"), Decimal("15.00")), (7, 2, Decimal("1.0"), Decimal("0.00"))]),
    (6, datetime(2025, 3, 10), "completed", [(2, 4, Decimal("1.0"), Decimal("40.00")), (4, 10, Decimal("1.0"), Decimal("10.00"))]),
    (7, datetime(2025, 3, 18), "shipped", [(5, 1, Decimal("1.0"), Decimal("0.00")), (8, 2, Decimal("1.0"), Decimal("10.00"))]),
    (8, datetime(2025, 3, 25), "cancelled", [(0, 1, Decimal("1.0"), Decimal("0.00"))]),

    # Q2 2025 Orders
    (0, datetime(2025, 4, 5), "completed", [(2, 3, Decimal("1.0"), Decimal("20.00")), (13, 5, Decimal("1.0"), Decimal("15.00"))]),
    (9, datetime(2025, 4, 12), "completed", [(0, 4, Decimal("1.0"), Decimal("150.00")), (1, 6, Decimal("1.0"), Decimal("30.00"))]),
    (10, datetime(2025, 4, 20), "completed", [(5, 3, Decimal("1.0"), Decimal("50.00")), (6, 5, Decimal("1.0"), Decimal("25.00"))]),
    (11, datetime(2025, 5, 2), "completed", [(9, 15, Decimal("1.0"), Decimal("20.00")), (11, 10, Decimal("1.0"), Decimal("5.00"))]),
    (12, datetime(2025, 5, 15), "completed", [(3, 8, Decimal("1.0"), Decimal("25.00")), (4, 12, Decimal("1.0"), Decimal("15.00"))]),
    (13, datetime(2025, 5, 28), "completed", [(0, 2, Decimal("1.0"), Decimal("50.00")), (2, 2, Decimal("1.0"), Decimal("10.00"))]),
    (14, datetime(2025, 6, 8), "completed", [(6, 4, Decimal("1.0"), Decimal("30.00")), (12, 3, Decimal("1.0"), Decimal("0.00"))]),
    (1, datetime(2025, 6, 18), "completed", [(1, 8, Decimal("1.0"), Decimal("40.00")), (14, 12, Decimal("1.0"), Decimal("10.00"))]),
    (3, datetime(2025, 6, 25), "shipped", [(5, 2, Decimal("1.0"), Decimal("20.00")), (8, 3, Decimal("1.0"), Decimal("15.00"))]),

    # Q3 2025 Orders
    (4, datetime(2025, 7, 7), "completed", [(0, 5, Decimal("1.0"), Decimal("200.00")), (2, 4, Decimal("1.0"), Decimal("50.00"))]),
    (5, datetime(2025, 7, 19), "completed", [(1, 10, Decimal("1.0"), Decimal("60.00")), (3, 6, Decimal("1.0"), Decimal("15.00"))]),
    (6, datetime(2025, 8, 3), "completed", [(5, 4, Decimal("1.0"), Decimal("80.00")), (6, 6, Decimal("1.0"), Decimal("40.00"))]),
    (7, datetime(2025, 8, 16), "completed", [(9, 20, Decimal("1.0"), Decimal("30.00")), (10, 15, Decimal("1.0"), Decimal("10.00"))]),
    (8, datetime(2025, 8, 29), "completed", [(2, 5, Decimal("1.0"), Decimal("45.00")), (13, 8, Decimal("1.0"), Decimal("20.00"))]),
    (9, datetime(2025, 9, 10), "completed", [(0, 3, Decimal("1.0"), Decimal("100.00")), (4, 15, Decimal("1.0"), Decimal("20.00"))]),
    (10, datetime(2025, 9, 22), "shipped", [(6, 2, Decimal("1.0"), Decimal("10.00")), (7, 3, Decimal("1.0"), Decimal("15.00"))]),

    # Q4 2025 Orders
    (11, datetime(2025, 10, 5), "completed", [(0, 4, Decimal("1.0"), Decimal("120.00")), (1, 5, Decimal("1.0"), Decimal("25.00"))]),
    (12, datetime(2025, 10, 18), "completed", [(5, 3, Decimal("1.0"), Decimal("45.00")), (6, 4, Decimal("1.0"), Decimal("20.00"))]),
    (13, datetime(2025, 11, 2), "completed", [(2, 6, Decimal("1.0"), Decimal("60.00")), (3, 10, Decimal("1.0"), Decimal("30.00"))]),
    (14, datetime(2025, 11, 15), "completed", [(9, 25, Decimal("1.0"), Decimal("40.00")), (12, 5, Decimal("1.0"), Decimal("15.00"))]),
    (0, datetime(2025, 11, 28), "completed", [(0, 6, Decimal("1.0"), Decimal("250.00")), (13, 10, Decimal("1.0"), Decimal("35.00"))]),
    (2, datetime(2025, 12, 5), "completed", [(1, 12, Decimal("1.0"), Decimal("80.00")), (4, 20, Decimal("1.0"), Decimal("25.00"))]),
    (3, datetime(2025, 12, 14), "completed", [(5, 5, Decimal("1.0"), Decimal("100.00")), (8, 4, Decimal("1.0"), Decimal("20.00"))]),
    (5, datetime(2025, 12, 20), "shipped", [(2, 3, Decimal("1.0"), Decimal("25.00")), (14, 15, Decimal("1.0"), Decimal("10.00"))]),
    (7, datetime(2025, 12, 28), "completed", [(0, 2, Decimal("1.0"), Decimal("50.00")), (6, 3, Decimal("1.0"), Decimal("15.00"))])
]


def seed_database(engine: Optional[Engine] = None, reset: bool = False) -> dict:
    """Idempotently seed the retail demo database.

    Args:
        engine: SQLAlchemy engine to target. Defaults to configured engine.
        reset: If True, drops all tables and recreates them before seeding.

    Returns:
        dict with counts of created entities.
    """
    target_engine = engine or get_engine()

    # Recreate or ensure tables exist
    if reset:
        Base.metadata.drop_all(target_engine)
    Base.metadata.create_all(target_engine)

    with Session(target_engine) as session:
        # Check if already seeded (idempotency check)
        existing_customers = session.scalar(select(func.count(Customer.id)))
        if existing_customers and existing_customers > 0 and not reset:
            logger.info("Database already contains %d customers. Skipping seed.", existing_customers)
            return {
                "status": "already_seeded",
                "customers": existing_customers,
                "products": session.scalar(select(func.count(Product.id))),
                "orders": session.scalar(select(func.count(Order.id))),
                "order_items": session.scalar(select(func.count(OrderItem.id))),
            }

        # 1. Insert Customers
        customer_objs = [Customer(**c) for c in CUSTOMERS_DATA]
        session.add_all(customer_objs)
        session.flush()

        # 2. Insert Products
        product_objs = [Product(**p) for p in PRODUCTS_DATA]
        session.add_all(product_objs)
        session.flush()

        # 3. Insert Orders & OrderItems
        order_count = 0
        item_count = 0

        for cust_idx, o_date, status, items in ORDER_RECIPES:
            order = Order(
                customer_id=customer_objs[cust_idx].id,
                order_date=o_date,
                status=status,
            )
            session.add(order)
            session.flush()
            order_count += 1

            for prod_idx, qty, mult, discount in items:
                prod = product_objs[prod_idx]
                item = OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=prod.unit_price * mult,
                    discount_amount=discount,
                )
                session.add(item)
                item_count += 1

        session.commit()
        logger.info(
            "Seeded demo database successfully: %d customers, %d products, %d orders, %d items",
            len(customer_objs),
            len(product_objs),
            order_count,
            item_count,
        )

        return {
            "status": "seeded",
            "customers": len(customer_objs),
            "products": len(product_objs),
            "orders": order_count,
            "order_items": item_count,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = seed_database(reset=True)
    print("Seed result:", result)
