"""Seed script: create roles, the first Super Admin, and the 3 tea blends.

Idempotent — running it again will not create duplicates.

    cd backend
    python -m scripts.seed
"""

from decimal import Decimal

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.utils import slugify
from app.crud import user as user_crud
from app.models.enums import UserRole
from app.models.product import Product
from app.models.role import Role

ROLES = ["Super Admin", "Admin", "Customer"]

PRODUCTS = [
    {
        "name": "Dawn",
        "blend": "Morning Clarity Blend",
        "description": "Morning Clarity Blend — a bright, awakening cup to begin the ritual.",
        "ingredients": "Tulsi. Rose. Cardamom. Green tea.",
        "price": Decimal("890.00"),
        "stock_qty": 50,
        "image_url": "/dawn-product.png",
        "category": "Green tea",
    },
    {
        "name": "Dusk",
        "blend": "Evening Unwind Blend",
        "description": "Evening Unwind Blend — our bestseller, for the slow descent into evening.",
        "ingredients": "Chamomile. Rose. Cardamom. Black tea.",
        "price": Decimal("950.00"),
        "stock_qty": 50,
        "image_url": "/dusk-product.png",
        "category": "Black tea",
    },
    {
        "name": "Night",
        "blend": "Deep Rest Blend",
        "description": "Deep Rest Blend — a calming infusion for deep, restorative rest.",
        "ingredients": "Ashwagandha. Rose. Lavender. White tea.",
        "price": Decimal("1050.00"),
        "stock_qty": 50,
        "image_url": "/night-product.png",
        "category": "White tea",
    },
]


def seed() -> None:
    db = SessionLocal()
    try:
        # Roles catalog
        existing_roles = {r.name for r in db.query(Role).all()}
        for name in ROLES:
            if name not in existing_roles:
                db.add(Role(name=name))

        # Super Admin
        admin = user_crud.get_by_email(db, settings.SUPERADMIN_EMAIL)
        if admin is None:
            admin = user_crud.create(
                db,
                name=settings.SUPERADMIN_NAME,
                email=settings.SUPERADMIN_EMAIL,
                password=settings.SUPERADMIN_PASSWORD,
                role=UserRole.super_admin,
            )
            print(f"  + Super Admin created: {settings.SUPERADMIN_EMAIL}")
        else:
            print(f"  = Super Admin already exists: {settings.SUPERADMIN_EMAIL}")

        db.flush()

        # Products
        for p in PRODUCTS:
            slug = slugify(p["name"])
            if db.query(Product).filter(Product.slug == slug).first():
                print(f"  = Product already exists: {p['name']}")
                continue
            db.add(
                Product(
                    name=p["name"],
                    slug=slug,
                    description=p["description"],
                    ingredients=p["ingredients"],
                    price=p["price"],
                    stock_qty=p["stock_qty"],
                    image_url=p["image_url"],
                    category=p["category"],
                    created_by_admin_id=admin.id,
                )
            )
            print(f"  + Product created: {p['name']} (₹{p['price']})")

        db.commit()
        print("\nSeed complete.")
        print(f"  Super Admin login: {settings.SUPERADMIN_EMAIL} / {settings.SUPERADMIN_PASSWORD}")
        print("  (change this password after first login)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
