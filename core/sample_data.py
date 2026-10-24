"""Demo listings, created once on first run.

Turn this off by setting SEED_SAMPLE_DATA = "0" in the secrets or environment.
The demo accounts get random passwords nobody knows, so they cannot be logged into.
The artwork used here is placeholder art from assets/placeholders/sample_*.jpg.
"""
import secrets
from datetime import timedelta

from . import auth, db, images
from .config import PLACEHOLDER_DIR, get_secret
from .utils import now_utc, to_iso

# (title, category, condition, description, image file, start Rs, increment Rs, reserve Rs, hours left, bids)
ITEMS = [
    ("Vintage brass desk lamp", "Home and Garden", "Used",
     "Heavy brass base with an adjustable arm and a warm fabric shade. Works perfectly and has been recently rewired.",
     "sample_lamp.jpg", 1500, 100, None, 52, 0),
    ("Mirrorless camera with 18-55mm lens", "Electronics", "Like New",
     "Lightly used for one season. Includes the kit lens, two batteries, charger, strap and a padded bag. Shutter count is low.",
     "sample_camera.jpg", 32000, 500, 40000, 70, 3),
    ("Framed mountain landscape print", "Art and Decor", "New",
     "Large print of a mountain sunrise in a solid wood frame, ready to hang. Never displayed.",
     "sample_print.jpg", 2500, 100, None, 118, 0),
    ("Hand-wound wall clock", "Collectibles", "Used",
     "Brass-rimmed wall clock with a white enamel face. Keeps good time with a weekly winding. Key included.",
     "sample_clock.jpg", 4000, 250, None, 5, 4),
    ("Pair of glazed ceramic vases", "Home and Garden", "New",
     "One tall teal vase and one small amber vase, hand glazed. Sold together as a pair.",
     "sample_vase.jpg", 1200, 50, None, 30, 2),
    ("Classic novels, hardcover set of 12", "Books and Media", "Used",
     "Twelve hardcover classics with matching spines. Clean pages, no markings, light shelf wear on two covers.",
     "sample_books.jpg", 3000, 100, None, 96, 1),
]


def _demo_user(username: str, full_name: str) -> int:
    row = db.fetch_one("SELECT id FROM users WHERE username = ?", (username,))
    if row:
        return row["id"]
    return auth._create_user(full_name, username, f"{username}@example.invalid", secrets.token_urlsafe(24))


def seed_if_empty() -> bool:
    """First-run seeding: only when the site has no auctions and seeding is not switched off."""
    if str(get_secret("SEED_SAMPLE_DATA", "1")) == "0":
        return False
    if db.get_setting("sample_data_seeded") == "1":
        return False
    if db.fetch_one("SELECT 1 AS x FROM auctions LIMIT 1"):
        db.set_setting("sample_data_seeded", "1")
        return False
    add_samples()
    db.set_setting("sample_data_seeded", "1")
    return True


def add_samples() -> int:
    """Create the demo listings (also used by the admin 'Add sample auctions' button)."""
    seller = _demo_user("demo_seller", "Demo Seller")
    buyers = [_demo_user("demo_buyer_one", "Demo Buyer One"), _demo_user("demo_buyer_two", "Demo Buyer Two")]
    categories = {c["name"]: c["id"] for c in db.fetch_all("SELECT id, name FROM categories")}
    now = now_utc()

    for title, category, condition, description, image, start, inc, reserve, hours, bid_count in ITEMS:
        image_id = images.save_upload(PLACEHOLDER_DIR / image)
        auction_id = db.insert(
            "INSERT INTO auctions (seller_id, category_id, title, description, condition, image_id, "
            "starting_price, min_increment, current_price, reserve_price, start_time, end_time) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (seller, categories.get(category), title, description, condition, image_id,
             start * 100, inc * 100, start * 100, reserve * 100 if reserve else None,
             to_iso(now - timedelta(days=1)), to_iso(now + timedelta(hours=hours))),
        )
        price, leader = start * 100, None
        for k in range(bid_count):
            price = start * 100 if k == 0 else price + inc * 100 * (1 + k % 2)
            leader = buyers[k % 2]
            db.execute(
                "INSERT INTO bids (auction_id, bidder_id, amount, created_at) VALUES (?, ?, ?, ?)",
                (auction_id, leader, price, to_iso(now - timedelta(hours=bid_count - k))),
            )
        if bid_count:
            db.execute(
                "UPDATE auctions SET current_price = ?, bid_count = ?, leader_id = ? WHERE id = ?",
                (price, bid_count, leader, auction_id),
            )

    return len(ITEMS)
