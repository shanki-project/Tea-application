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

# Additional catalogue — reuses the three product images. Image is chosen by mood:
#   green/bright -> dawn,  black/spiced -> dusk,  white/calming -> night.
DAWN_IMG, DUSK_IMG, NIGHT_IMG = "/dawn-product.png", "/dusk-product.png", "/night-product.png"

EXTRA_PRODUCTS = [
    (
        "Highland",
        "Darjeeling first flush — delicate, floral, muscatel.",
        "Darjeeling. Muscatel notes.",
        "1180.00",
        40,
        DAWN_IMG,
        "Green tea",
    ),
    (
        "Lotus",
        "Jasmine-scented green tea, layered overnight with fresh blossoms.",
        "Green tea. Jasmine.",
        "990.00",
        35,
        DAWN_IMG,
        "Green tea",
    ),
    (
        "Zen",
        "Japanese sencha — grassy, clean, quietly energising.",
        "Sencha. Green tea.",
        "1120.00",
        30,
        DAWN_IMG,
        "Green tea",
    ),
    (
        "Saffron Noon",
        "Kashmiri kahwa — saffron, almond and cardamom.",
        "Green tea. Saffron. Almond. Cardamom.",
        "1350.00",
        18,
        DAWN_IMG,
        "Green tea",
    ),
    (
        "Golden Hour",
        "Turmeric-ginger tisane for a warm, golden lift.",
        "Turmeric. Ginger. Black pepper.",
        "760.00",
        60,
        DAWN_IMG,
        "Herbal",
    ),
    (
        "Meadow",
        "Single-note peppermint — cooling and bright.",
        "Peppermint.",
        "640.00",
        55,
        DAWN_IMG,
        "Herbal",
    ),
    (
        "Monsoon",
        "Masala chai — bold black tea and warming spice.",
        "Black tea. Ginger. Clove. Cinnamon. Cardamom.",
        "820.00",
        50,
        DUSK_IMG,
        "Black tea",
    ),
    (
        "Silk Road",
        "Earl Grey with bergamot and a thread of vanilla.",
        "Black tea. Bergamot. Vanilla.",
        "980.00",
        42,
        DUSK_IMG,
        "Black tea",
    ),
    (
        "Amber Leaf",
        "Bold single-estate Assam — malty and full.",
        "Assam black tea.",
        "880.00",
        48,
        DUSK_IMG,
        "Black tea",
    ),
    (
        "Cardamom Hills",
        "Spiced black tea with green cardamom and rose.",
        "Black tea. Cardamom. Rose.",
        "940.00",
        9,
        DUSK_IMG,
        "Black tea",
    ),
    (
        "Ember",
        "Smoked oolong — toasty, deep, lingering.",
        "Oolong. Smoked notes.",
        "1240.00",
        22,
        DUSK_IMG,
        "Oolong",
    ),
    (
        "Rosewood",
        "Hibiscus and rose — tart, ruby and aromatic.",
        "Hibiscus. Rose. Beetroot.",
        "720.00",
        38,
        DUSK_IMG,
        "Herbal",
    ),
    (
        "Mist",
        "White peony (Bai Mu Dan) — soft, sweet, gentle.",
        "White peony tea.",
        "1280.00",
        16,
        NIGHT_IMG,
        "White tea",
    ),
    (
        "Frost",
        "Silver needle — the most delicate of white teas.",
        "Silver needle white tea.",
        "1480.00",
        8,
        NIGHT_IMG,
        "White tea",
    ),
    (
        "Midnight",
        "Lavender and chamomile to ease into sleep.",
        "Lavender. Chamomile.",
        "780.00",
        44,
        NIGHT_IMG,
        "Herbal",
    ),
    (
        "Tulsi Calm",
        "Holy basil tisane — grounding and caffeine-free.",
        "Tulsi. Holy basil.",
        "690.00",
        52,
        NIGHT_IMG,
        "Herbal",
    ),
    (
        "Velvet",
        "Rooibos with vanilla — naturally sweet, no caffeine.",
        "Rooibos. Vanilla.",
        "740.00",
        47,
        NIGHT_IMG,
        "Herbal",
    ),
]


def _extra_dicts():
    for name, desc, ing, price, stock, img, cat in EXTRA_PRODUCTS:
        yield {
            "name": name,
            "description": desc,
            "ingredients": ing,
            "price": Decimal(price),
            "stock_qty": stock,
            "image_url": img,
            "category": cat,
        }


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

        # Products (signature blends + the wider catalogue)
        for p in [*PRODUCTS, *_extra_dicts()]:
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
