"""Counts for the Home page, the member dashboard and the admin overview."""
from . import db
from .utils import now_utc, to_iso


def platform() -> dict:
    now = to_iso(now_utc())
    return db.fetch_one(
        "SELECT "
        "(SELECT COUNT(*) FROM auctions WHERE status = 'active' AND end_time > ?) AS live, "
        "(SELECT COUNT(*) FROM bids) AS bids, "
        "(SELECT COUNT(*) FROM users WHERE role = 'user' AND email NOT LIKE '%@example.invalid') AS members, "
        "(SELECT COUNT(*) FROM auctions WHERE winner_id IS NOT NULL) AS sold, "
        "(SELECT COUNT(*) FROM payments p JOIN auctions a ON a.id = p.auction_id "
        " WHERE p.status = 'submitted' AND a.status != 'removed') AS to_confirm",
        (now,),
    )


def for_user(user_id: int) -> dict:
    now = to_iso(now_utc())
    return db.fetch_one(
        "SELECT "
        "(SELECT COUNT(*) FROM auctions WHERE seller_id = ? AND status = 'active' AND end_time > ?) AS my_live, "
        "(SELECT COUNT(*) FROM auctions WHERE seller_id = ? AND status != 'removed') AS total_listed, "
        "(SELECT COUNT(*) FROM bids WHERE bidder_id = ?) AS total_bids, "
        "(SELECT COUNT(*) FROM auctions WHERE status = 'active' AND end_time > ? AND leader_id = ?) AS leading, "
        "(SELECT COUNT(DISTINCT b.auction_id) FROM bids b JOIN auctions a ON a.id = b.auction_id "
        " WHERE b.bidder_id = ? AND a.status = 'active' AND a.end_time > ?) AS bidding_on, "
        "(SELECT COUNT(*) FROM auctions WHERE winner_id = ? AND status != 'removed') AS won, "
        "(SELECT COUNT(*) FROM payments p JOIN auctions a ON a.id = p.auction_id "
        " WHERE p.buyer_id = ? AND p.status = 'pending' AND a.status != 'removed') AS to_pay",
        (user_id, now, user_id, user_id, now, user_id, user_id, now, user_id, user_id),
    )


def recent_bids(user_id: int, limit: int = 5) -> list[dict]:
    return db.fetch_all(
        "SELECT b.amount, b.created_at, a.id AS auction_id, a.title FROM bids b "
        "JOIN auctions a ON a.id = b.auction_id WHERE b.bidder_id = ? AND a.status != 'removed' "
        "ORDER BY b.id DESC LIMIT ?",
        (user_id, limit),
    )


def recent_listings(user_id: int, limit: int = 5) -> list[dict]:
    return db.fetch_all(
        "SELECT id, title, current_price, bid_count, status, end_time, winner_id FROM auctions "
        "WHERE seller_id = ? AND status != 'removed' ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    )


def category_counts() -> list[dict]:
    now = to_iso(now_utc())
    return db.fetch_all(
        "SELECT c.id, c.name, COUNT(a.id) AS live FROM categories c "
        "LEFT JOIN auctions a ON a.category_id = c.id AND a.status = 'active' AND a.end_time > ? "
        "GROUP BY c.id, c.name ORDER BY c.name",
        (now,),
    )
