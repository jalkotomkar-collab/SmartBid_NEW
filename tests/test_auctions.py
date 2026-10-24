"""Auction tests: bidding rules, raising your own bid, closing, winners, payments, search and sort.

Run from the project folder:  python tests/test_auctions.py
The scripts replace Streamlit with a small stand-in, so they run without a browser or a server
and use a temporary SQLite file (your real data/auction.db is never touched).
"""
import sys, types, io, tempfile, pathlib, time
from datetime import timedelta
st = types.ModuleType("streamlit")
def _deco(*a, **k):
    if a and callable(a[0]): a[0].clear=lambda:None; return a[0]
    def w(f): f.clear=lambda:None; return f
    return w
st.cache_resource=_deco; st.cache_data=_deco
class SS(dict):
    def __getattr__(self,k): return self.get(k)
st.session_state=SS()
class Secrets:
    def __contains__(self,k): raise FileNotFoundError
st.context = types.SimpleNamespace(headers={'Host': 'localhost:8501'})
st.secrets=Secrets(); sys.modules["streamlit"]=st
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from core import db, auth, auctions as A, utils as U
db.DB_PATH = pathlib.Path(tempfile.mkdtemp())/"t.db"
db.init_db()
_,seller = auth.register_user("Sam Seller","sam","sam@x.com","Passw0rd1","Passw0rd1")
_,b1 = auth.register_user("Bea One","bea","bea@x.com","Passw0rd1","Passw0rd1")
_,b2 = auth.register_user("Cy Two","cyrus","cy@x.com","Passw0rd1","Passw0rd1")
auth.ensure_admin(); admin = db.fetch_one("SELECT id FROM users WHERE role='admin'")["id"]
now = U.now_utc()
def mk(hours=48, start=50000, inc=5000, reserve=None, title="Lamp"):
    return A.create_auction(seller["id"], title, 1, "Used", "desc", None, start, inc, reserve, now+timedelta(hours=hours))
a = mk()
ok,m = A.place_bid(a,b1["id"],49900); assert not ok and "at least" in m and "₹500" in m, m
ok,m = A.place_bid(a,seller["id"],60000); assert not ok and "own" in m
ok,m = A.place_bid(a,admin,60000); assert not ok and "Administrator" in m
ok,m = A.place_bid(a,b1["id"],50000); assert ok, m          # first bid = starting price
au = A.get_auction(a); assert au["current_price"]==50000 and au["bid_count"]==1 and au["leader_id"]==b1["id"]
ok,m = A.place_bid(a,b1["id"],50000); assert not ok and "at least ₹550" in m, m      # same amount again
ok,m = A.place_bid(a,b1["id"],55000); assert ok, m                                    # the leader may raise their own bid
au = A.get_auction(a); assert au["current_price"]==55000 and au["bid_count"]==2 and au["leader_id"]==b1["id"]
ok,m = A.place_bid(a,b2["id"],55000); assert not ok and "at least ₹600" in m, m
ok,m = A.place_bid(a,b2["id"],59999); assert not ok
ok,m = A.place_bid(a,b2["id"],60000); assert ok                                       # exactly current + increment
assert A.min_next_bid(A.get_auction(a))==65000
assert [x["amount"] for x in A.bids_for(a)]==[60000,55000,50000]

# the first leader raises again after being outbid, then the other bids on top
ok,_ = A.place_bid(a,b1["id"],65000); assert ok
ok,m = A.place_bid(a,b2["id"],65000); assert not ok                                   # must beat 65000
ok,m = A.place_bid(a,b2["id"],70000); assert ok
assert A.get_auction(a)["bid_count"]==5 and len(A.bids_for(a,50))==5

# the clock never moves: a bid in the last minutes does not extend the auction
e = mk(hours=0, title="Soon"); db.execute("UPDATE auctions SET end_time=? WHERE id=?",(U.to_iso(now+timedelta(minutes=2)),e))
before = A.get_auction(e)["end_time"]
ok,m = A.place_bid(e,b1["id"],50000); assert ok and "extend" not in m.lower(), m
assert A.get_auction(e)["end_time"]==before
ok,m = A.place_bid(e,b1["id"],55000); assert ok and A.get_auction(e)["end_time"]==before   # raising own bid, still no change

# closing: sold, reserve not met, no bids
sold = mk(title="Sold"); A.place_bid(sold,b1["id"],50000); A.place_bid(sold,b2["id"],55000)
res  = mk(title="Reserve", reserve=90000); A.place_bid(res,b1["id"],50000)
none = mk(title="None")
past = U.to_iso(now-timedelta(minutes=1))
for i in (sold,res,none): db.execute("UPDATE auctions SET end_time=? WHERE id=?",(past,i))
ok,m = A.place_bid(sold,b1["id"],90000); assert not ok and "ended" in m
A.close_expired()  # the rejected late bid above already triggered closing
s=A.get_auction(sold); assert s["status"]=="ended" and s["winner_id"]==b2["id"] and s["winning_amount"]==55000 and s["winner_username"]=="cyrus"
p=db.fetch_one("SELECT * FROM payments WHERE auction_id=?",(sold,)); assert p["buyer_id"]==b2["id"] and p["amount"]==55000 and p["status"]=="pending"
r=A.get_auction(res); assert r["status"]=="ended" and r["winner_id"] is None
assert db.fetch_one("SELECT COUNT(*) AS n FROM payments WHERE auction_id IN (?,?)",(res,none))["n"]==0
assert A.get_auction(none)["status"]=="ended"
assert A.close_expired()==0                                      # idempotent
assert db.fetch_one("SELECT COUNT(*) AS n FROM payments")["n"]==1

# listing / search / sort
live = A.list_auctions(); titles=[x["title"] for x in live]
assert "Sold" not in titles and "Lamp" in titles and live[0]["end_time"]<=live[-1]["end_time"]
assert {x["title"] for x in A.list_auctions(live=False)}=={"Sold","Reserve","None"}
mk(title="100% cotton_throw"); mk(title="Other")
assert [x["title"] for x in A.list_auctions(search="100%")]==["100% cotton_throw"]
assert A.list_auctions(search="cotton_t")[0]["title"]=="100% cotton_throw"
assert A.list_auctions(search="zzz")==[]
assert A.list_auctions(category_id=999)==[]
assert A.list_auctions(sort="Price: high to low")[0]["current_price"]>=A.list_auctions(sort="Price: high to low")[-1]["current_price"]
assert len(A.list_auctions(limit=2))==2 and len(A.list_auctions(limit=2,offset=2))>=1
a2 = A.get_auction(a); assert A.is_live(a2) and not A.is_live(A.get_auction(sold))
print("AUCTION TESTS PASSED")
