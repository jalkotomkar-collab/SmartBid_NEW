"""Demo payment records. No money moves: the buyer scans the admin's QR image,
tells the app they have paid, and the admin confirms it."""
from . import db, images
from .utils import now_utc, to_iso

_BASE = (
    "SELECT p.*, a.title, a.image_id, a.seller_id, s.username AS seller_username, "
    "b.username AS buyer_username "
    "FROM payments p JOIN auctions a ON a.id = p.auction_id "
    "JOIN users s ON s.id = a.seller_id JOIN users b ON b.id = p.buyer_id "
    "WHERE a.status != 'removed' "
)


def for_buyer(user_id: int):
    return db.fetch_all(_BASE + "AND p.buyer_id = ? ORDER BY p.id DESC", (int(user_id),))


def all_payments(status: str | None = None):
    if status:
        return db.fetch_all(_BASE + "AND p.status = ? ORDER BY p.id DESC", (status,))
    return db.fetch_all(_BASE + "ORDER BY p.id DESC")


def submit(auction_id: int, buyer_id: int, reference: str):
    """Buyer says they have paid. Returns (ok, message)."""
    reference = (reference or "").strip()
    if len(reference) > 60:
        return False, "Keep the reference to 60 characters or fewer."
    with db.connection() as conn:
        done = db.rows(conn.execute(
            "UPDATE payments SET status = 'submitted', reference = ? "
            "WHERE auction_id = ? AND buyer_id = ? AND status = 'pending' RETURNING id",
            (reference or None, int(auction_id), int(buyer_id)),
        ))
    if not done:
        return False, "This payment was already submitted."
    return True, "Thanks. Your payment was sent to the administrator for confirmation."


def confirm(payment_id: int) -> bool:
    with db.connection() as conn:
        done = db.rows(conn.execute(
            "UPDATE payments SET status = 'confirmed', confirmed_at = ? "
            "WHERE id = ? AND status = 'submitted' RETURNING id",
            (to_iso(now_utc()), int(payment_id)),
        ))
    return bool(done)


def reject(payment_id: int) -> bool:
    """Admin did not receive the money: send it back to the buyer as unpaid."""
    with db.connection() as conn:
        done = db.rows(conn.execute(
            "UPDATE payments SET status = 'pending', reference = NULL "
            "WHERE id = ? AND status = 'submitted' RETURNING id",
            (int(payment_id),),
        ))
    return bool(done)


# ---- the QR code / payment image the admin controls
def qr_image_id() -> int | None:
    value = db.get_setting("payment_qr_image_id")
    return int(value) if value else None


def set_qr(image_id: int | None) -> None:
    old = qr_image_id()
    db.set_setting("payment_qr_image_id", str(image_id or ""))
    if old and old != image_id:
        images.delete_image(old)
