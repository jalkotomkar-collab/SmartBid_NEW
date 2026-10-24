"""Auction rules: creating listings, searching, bidding and closing.

Bidding rules
  * The first bid must be at least the starting price.
  * Every later bid must be at least current price + the auction's minimum increment.
  * The highest bid when the timer ends wins (and must meet the reserve, if one is set).
  * Auctions end exactly at their end time; bids never extend the clock.
  * Sellers cannot bid on their own items. The current leader may raise their own bid.
All amounts are integer paise.
"""
import time
from . import db
from .utils import format_inr, now_utc, parse_iso, to_iso

CONDITIONS = ["New", "Like New", "Used", "For Parts"]

SORTS = {
    "Ending soonest": "a.end_time ASC",
    "Newest first": "a.id DESC",
    "Price: low to high": "a.current_price ASC, a.end_time ASC",
    "Price: high to low": "a.current_price DESC, a.end_time ASC",
    "Most bids": "a.bid_count DESC, a.end_time ASC",
}

_SELECT = """
    SELECT a.*, u.username AS seller_username, c.name AS category_name,
           l.username AS leader_username, w.username AS winner_username,
           (SELECT p.status FROM payments p WHERE p.auction_id = a.id) AS payment_status
    FROM auctions a
    JOIN users u ON u.id = a.seller_id
    LEFT JOIN categories c ON c.id = a.category_id
    LEFT JOIN users l ON l.id = a.leader_id
    LEFT JOIN users w ON w.id = a.winner_id
"""

_last_close = 0.0


# ------------------------------------------------------------------- queries
def get_auction(auction_id: int):
    return db.fetch_one(_SELECT + " WHERE a.id = ?", (int(auction_id),))


def is_live(auction: dict) -> bool:
    return auction["status"] == "active" and parse_iso(auction["end_time"]) > now_utc()


def min_next_bid(auction: dict) -> int:
    if auction["bid_count"] == 0:
        return auction["starting_price"]
    return auction["current_price"] + auction["min_increment"]


def list_auctions(search="", category_id=None, sort="Ending soonest", live=True, limit=12, offset=0):
    where, params = [], []
    now = to_iso(now_utc())
    if live:
        where.append("a.status = 'active' AND a.end_time > ?")
        params.append(now)
    else:
        where.append("(a.status = 'ended' OR (a.status = 'active' AND a.end_time <= ?))")
        params.append(now)
    if category_id:
        where.append("a.category_id = ?")
        params.append(int(category_id))
    term = (search or "").strip()
    if term:
        like = "%" + term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        where.append("(a.title LIKE ? ESCAPE '\\' OR a.description LIKE ? ESCAPE '\\')")
        params += [like, like]
    order = SORTS.get(sort, SORTS["Ending soonest"]) if live else "a.end_time DESC"
    sql = _SELECT + " WHERE " + " AND ".join(where) + f" ORDER BY {order} LIMIT ? OFFSET ?"
    return db.fetch_all(sql, (*params, int(limit), int(offset)))


def bids_for(auction_id: int, limit: int = 15):
    return db.fetch_all(
        "SELECT b.id, b.amount, b.created_at, b.bidder_id, u.username "
        "FROM bids b JOIN users u ON u.id = b.bidder_id "
        "WHERE b.auction_id = ? ORDER BY b.amount DESC, b.id DESC LIMIT ?",
        (int(auction_id), int(limit)),
    )


# ------------------------------------------------------------------ creating
def create_auction(seller_id, title, category_id, condition, description, image_id,
                   starting_price, min_increment, reserve_price, end_time_utc) -> int:
    now = now_utc()
    return db.insert(
        "INSERT INTO auctions (seller_id, category_id, title, description, condition, image_id, "
        "starting_price, min_increment, current_price, reserve_price, start_time, end_time) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (seller_id, category_id, title, description, condition, image_id,
         starting_price, min_increment, starting_price, reserve_price, to_iso(now), to_iso(end_time_utc)),
    )


# -------------------------------------------------------------------- bidding
def place_bid(auction_id: int, bidder_id: int, amount: int):
    """Try to place a bid. Returns (ok, message).

    The current leader may bid again to raise their own bid; every bid, from anyone,
    must still beat the current price by at least the minimum increment.
    """
    auction = get_auction(auction_id)
    if not auction or auction["status"] != "active":
        return False, "This auction is not open for bidding."
    now = now_utc()
    if parse_iso(auction["end_time"]) <= now:
        close_expired()
        return False, "This auction has just ended."

    bidder = db.fetch_one("SELECT role, is_active FROM users WHERE id = ?", (bidder_id,))
    if not bidder or not bidder["is_active"]:
        return False, "Your account cannot place bids."
    if bidder["role"] != "user":
        return False, "Administrator accounts cannot bid."
    if auction["seller_id"] == bidder_id:
        return False, "You cannot bid on your own listing."

    minimum = min_next_bid(auction)
    if amount < minimum:
        return False, f"Your bid must be at least {format_inr(minimum)}."

    # One conditional UPDATE decides the winner of any race: it only applies if the bid
    # still beats the current price at this exact moment. RETURNING tells us if it did.
    # The end time is never changed: auctions end exactly when the clock runs out.
    with db.connection() as conn:
        applied = db.rows(
            conn.execute(
                "UPDATE auctions SET current_price = ?, bid_count = bid_count + 1, leader_id = ? "
                "WHERE id = ? AND status = 'active' AND end_time > ? "
                "AND ((bid_count = 0 AND ? >= starting_price) "
                "OR (bid_count > 0 AND ? >= current_price + min_increment)) RETURNING id",
                (amount, bidder_id, auction_id, to_iso(now), amount, amount),
            )
        )
        if applied:
            conn.execute(
                "INSERT INTO bids (auction_id, bidder_id, amount) VALUES (?, ?, ?)",
                (auction_id, bidder_id, amount),
            )

    if not applied:
        latest = get_auction(auction_id)
        if not latest or not is_live(latest):
            return False, "This auction has just ended."
        if latest["leader_id"] == bidder_id:
            return False, (
                f"You already hold the highest bid of {format_inr(latest['current_price'])}. "
                f"To raise it, bid at least {format_inr(min_next_bid(latest))}."
            )
        return False, (
            "Someone placed a higher bid first. "
            f"The minimum bid is now {format_inr(min_next_bid(latest))}."
        )

    return True, f"Your bid of {format_inr(amount)} is now the highest bid."


# -------------------------------------------------------------------- closing
def close_expired() -> int:
    """Finish every auction whose time is up: pick the winner and open a payment record."""
    now = to_iso(now_utc())
    expired = db.fetch_all(
        "SELECT id, bid_count, current_price, reserve_price, leader_id FROM auctions "
        "WHERE status = 'active' AND end_time <= ?",
        (now,),
    )
    for a in expired:
        sold = (
            a["bid_count"] > 0
            and a["leader_id"] is not None
            and (a["reserve_price"] is None or a["current_price"] >= a["reserve_price"])
        )
        with db.connection() as conn:
            if sold:
                conn.execute(
                    "UPDATE auctions SET status = 'ended', winner_id = ?, winning_amount = ? "
                    "WHERE id = ? AND status = 'active'",
                    (a["leader_id"], a["current_price"], a["id"]),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO payments (auction_id, buyer_id, amount) VALUES (?, ?, ?)",
                    (a["id"], a["leader_id"], a["current_price"]),
                )
            else:
                conn.execute(
                    "UPDATE auctions SET status = 'ended' WHERE id = ? AND status = 'active'",
                    (a["id"],),
                )
    return len(expired)


def close_expired_throttled(seconds: int = 10) -> None:
    """Cheap to call on every page run: only hits the database every few seconds."""
    global _last_close
    if time.time() - _last_close >= seconds:
        _last_close = time.time()
        close_expired()


# ------------------------------------------------------------- seller tools
_KEEP = object()


def seller_auctions(seller_id: int):
    return db.fetch_all(
        _SELECT + " WHERE a.seller_id = ? AND a.status != 'removed' ORDER BY a.id DESC", (int(seller_id),)
    )


def update_auction(auction_id, seller_id, title, category_id, condition, description,
                   starting_price, min_increment, reserve_price, image_id=_KEEP) -> bool:
    """Edit a listing. Only allowed while it is live and has no bids."""
    sets = ("title = ?, category_id = ?, condition = ?, description = ?, starting_price = ?, "
            "min_increment = ?, current_price = ?, reserve_price = ?")
    params = [title, category_id, condition, description, starting_price, min_increment,
              starting_price, reserve_price]
    if image_id is not _KEEP:
        sets += ", image_id = ?"
        params.append(image_id)
    with db.connection() as conn:
        done = db.rows(conn.execute(
            f"UPDATE auctions SET {sets} WHERE id = ? AND seller_id = ? AND status = 'active' "
            "AND bid_count = 0 AND end_time > ? RETURNING id",
            (*params, auction_id, seller_id, to_iso(now_utc())),
        ))
    return bool(done)


def cancel_auction(auction_id, seller_id) -> bool:
    """Withdraw a listing. Only allowed while it is live and has no bids."""
    with db.connection() as conn:
        done = db.rows(conn.execute(
            "UPDATE auctions SET status = 'cancelled' WHERE id = ? AND seller_id = ? "
            "AND status = 'active' AND bid_count = 0 RETURNING id",
            (auction_id, seller_id),
        ))
    return bool(done)


# --------------------------------------------------------------- buyer view
def user_bids(user_id: int):
    """Every auction the user has bid on, with their best bid and how they stand."""
    items = db.fetch_all(
        _SELECT.replace(
            "SELECT a.*,",
            "SELECT a.*, (SELECT MAX(b.amount) FROM bids b WHERE b.auction_id = a.id AND b.bidder_id = ?) AS my_best,",
            1,
        )
        + " WHERE a.id IN (SELECT auction_id FROM bids WHERE bidder_id = ?) AND a.status != 'removed' "
        "ORDER BY a.end_time DESC",
        (int(user_id), int(user_id)),
    )
    for a in items:
        if a["status"] == "cancelled":
            a["standing"] = "Cancelled"
        elif is_live(a):
            a["standing"] = "Leading" if a["leader_id"] == user_id else "Outbid"
        else:
            a["standing"] = "Won" if a["winner_id"] == user_id else "Lost"
    return items


# --------------------------------------------------------------- admin tools
def admin_auctions(search: str = "", status: str = "All", limit: int = 100):
    where, params = ["a.status != 'removed'"], []
    now = to_iso(now_utc())
    if status == "Live":
        where.append("a.status = 'active' AND a.end_time > ?"); params.append(now)
    elif status == "Ended":
        where.append("(a.status = 'ended' OR (a.status = 'active' AND a.end_time <= ?))"); params.append(now)
    elif status == "Cancelled":
        where.append("a.status = 'cancelled'")
    term = (search or "").strip()
    if term:
        like = "%" + term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        where.append("(a.title LIKE ? ESCAPE '\\' OR u.username LIKE ? ESCAPE '\\')")
        params += [like, like]
    return db.fetch_all(
        _SELECT + " WHERE " + " AND ".join(where) + " ORDER BY a.id DESC LIMIT ?", (*params, int(limit))
    )


def remove_auction(auction_id: int) -> bool:
    with db.connection() as conn:
        done = db.rows(conn.execute(
            "UPDATE auctions SET status = 'removed' WHERE id = ? AND status != 'removed' RETURNING id",
            (int(auction_id),),
        ))
    return bool(done)
