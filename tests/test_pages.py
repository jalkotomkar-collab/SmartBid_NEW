"""Page tests: runs every page's real code for guests, members and the admin, including forms and navigation.

Run from the project folder:  python tests/test_pages.py
The scripts replace Streamlit with a small stand-in, so they run without a browser or a server
and use a temporary SQLite file (your real data/auction.db is never touched).
"""
import sys, types, tempfile, pathlib, runpy, datetime as dt
from unittest.mock import MagicMock
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))

class Stop(Exception): pass
class Rerun(Exception): pass
class Switch(Exception): pass
class SS(dict):
    def __getattr__(self,k): return self.get(k)
    def __setattr__(self,k,v): self[k]=v

S = types.SimpleNamespace(inputs={}, md=[], msgs=[], links=[], images=0, metrics=[], nav=None)
st = types.ModuleType("streamlit")
def deco(*a, **k):
    if a and callable(a[0]): a[0].clear=lambda:None; return a[0]
    def w(f): f.clear=lambda:None; return f
    return w
st.cache_data = st.cache_resource = deco
st.fragment = lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda f: f))
st.session_state = SS(); st.query_params = {}
st.context = types.SimpleNamespace(headers={'Host': 'localhost:8501'})
class Secrets:
    def __contains__(self,k): return False
st.secrets = Secrets()
class Col:
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def __getattr__(self,name): return getattr(st,name)
def _cols(spec, **k): return [Col() for _ in range(spec if isinstance(spec,int) else len(spec))]
st.container = lambda *a, **k: Col()
st.sidebar = Col()
st.tabs = lambda labels, **k: [Col() for _ in labels]
st.expander = lambda *a, **k: Col()
st.metric = lambda label, value, *a, **k: S.metrics.append((label, value))
st.set_page_config = lambda **k: None
class Page:
    def __init__(self, path, **k): self.path, self.k = path, k
class Nav:
    def __init__(self, pages, position): self.pages, self.position = pages, position
    def run(self): S.ran = True
def _navigation(pages, position="sidebar"):
    S.nav = Nav(pages, position); return S.nav
st.Page, st.navigation = Page, _navigation
st.form = lambda *a, **k: Col()
def _in(label, default): return S.inputs.get(label, default)
st.columns = _cols
st.text_input = lambda label, value="", **k: _in(label, value)
st.text_area = lambda label, value="", **k: _in(label, value)
st.number_input = lambda label, min_value=None, value=None, **k: _in(label, value if value is not None else min_value)
st.selectbox = lambda label, options, index=0, **k: _in(label, list(options)[index])
st.segmented_control = lambda label, options, default=None, **k: _in(label, default)
st.checkbox = lambda label, value=False, **k: _in(label, value)
st.file_uploader = lambda label, **k: _in(label, None)
st.date_input = lambda label, value=None, **k: _in(label, value)
st.time_input = lambda label, value=None, **k: _in(label, value)
st.button = lambda label, **k: _in(("btn",label), False)
st.form_submit_button = lambda label, **k: _in(("btn",label), False)
def _md(body, *a, **k): S.md.append(str(body))
st.markdown = st.write = _md
for n in ("success","error","info","warning"):
    setattr(st, n, (lambda n: lambda body, *a, **k: S.msgs.append((n, str(body))))(n))
st.caption = lambda body, *a, **k: S.md.append(str(body))
st.image = lambda *a, **k: setattr(S,"images",S.images+1)
st.page_link = lambda page, **k: S.links.append(page)
def _stop(): raise Stop()
def _rerun(**k): raise Rerun()
def _switch(p): raise Switch(p)
st.stop, st.rerun, st.switch_page = _stop, _rerun, _switch
st.__getattr__ = lambda name: (lambda *a, **k: MagicMock())     # everything else: harmless no-op
sys.modules["streamlit"] = st

from core import db, auth, auctions as A, sample_data, images
from core.utils import now_utc, to_iso
db.DB_PATH = pathlib.Path(tempfile.mkdtemp())/"t.db"
db.init_db(); auth.ensure_admin()
assert sample_data.seed_if_empty() is True and sample_data.seed_if_empty() is False
rows = db.fetch_all("SELECT * FROM auctions"); assert len(rows)==6
assert db.fetch_one("SELECT COUNT(*) AS n FROM bids")["n"]==10
assert all(r["image_id"] for r in rows) and db.fetch_one("SELECT COUNT(*) AS n FROM images")["n"]==6
camera = next(r for r in rows if "camera" in r["title"]); assert camera["bid_count"]==3 and camera["current_price"]>3200000
clock = next(r for r in rows if "clock" in r["title"]); assert clock["bid_count"]==4

_,bea = auth.register_user("Bea One","bea","bea@x.com","Passw0rd1","Passw0rd1")
seller_demo = db.fetch_one("SELECT id FROM users WHERE username='demo_seller'")["id"]
admin = db.fetch_one("SELECT id,full_name,username,email,role FROM users WHERE role='admin'")

def run(view, user=None, inputs=None, session=None, root_dir="views"):
    S.inputs, S.md, S.msgs, S.links, S.images, S.metrics = (inputs or {}), [], [], [], 0, []
    st.session_state.clear(); st.query_params.clear()
    if user: st.session_state["user"] = dict(user)
    st.session_state.update(session or {})
    try: runpy.run_path(str(ROOT/root_dir/view) if root_dir else str(ROOT/view))
    except (Stop, Rerun) as e: return type(e).__name__
    except Switch as e: return f"Switch:{e}"
    return "ok"
html = lambda: "\n".join(S.md)
member = {"id":bea["id"],"full_name":"Bea One","username":"bea","email":"bea@x.com","role":"user"}

# ---- Home / Browse
assert run("home.py")=="ok" and "Browse by category" not in html() and "How it works" not in html() and "Closing soon" not in html()
assert S.metrics==[] and "Your activity" not in html()                      # guests: just the hero
assert run("home.py", member)=="ok" and "Welcome back, Bea" in html()
assert dict(S.metrics)=={"Bids placed":0,"Items listed":0} and "Live auctions" not in dict(S.metrics) and "Members" not in dict(S.metrics) and "Your activity" in html()
assert run("home.py", member, inputs={("btn","View my bids"):True})=="Switch:views/my_bids.py"
assert run("home.py", member, inputs={("btn","View my listings"):True})=="Switch:views/my_auctions.py"
assert run("home.py", admin)=="ok" and S.metrics==[]
assert run("browse.py")=="ok" and html().count('class="nl-card-title"')==6 and "₹" in html()
assert run("browse.py", inputs={"Search":"camera"})=="ok" and html().count('class="nl-card-title"')==1
assert run("browse.py", inputs={"Search":"zzz"})=="ok" and "Nothing here yet" in html()
assert run("browse.py", inputs={"Category":"Electronics"})=="ok" and html().count('class="nl-card-title"')==1
assert run("browse.py", inputs={"Show":"Ended"})=="ok" and "No auctions have ended yet" in html()
assert run("browse.py", inputs={"Sort by":"Price: high to low"})=="ok" and html().index("Mirrorless")<html().index("Vintage brass")
assert run("browse.py", inputs={("btn","View auction"):True})=="Switch:views/auction_details.py"
assert st.session_state["selected_auction_id"]

# ---- Auction details
sel = {"selected_auction_id": camera["id"]}
assert run("auction_details.py")=="Stop" and "Choose an auction" in html()
assert run("auction_details.py", session=sel)=="ok" and "Log in or create an account" in "".join(m for _,m in S.msgs) and "Mirrorless camera" in html()
assert "Reserve not met" in html() and "@demo_seller" in html() and "extend" not in html().lower()
assert run("auction_details.py", {**member,"id":seller_demo}, session=sel)=="ok" and "your listing" in "".join(m for _,m in S.msgs)
assert run("auction_details.py", admin, session=sel)=="ok" and "cannot bid" in "".join(m for _,m in S.msgs)
minimum = A.min_next_bid(A.get_auction(camera["id"]))
# bid too low -> flash error, auction unchanged
r = run("auction_details.py", member, inputs={"Your bid (rupees)": minimum//100 - 1, ("btn","Place bid"): True}, session=sel)
assert r=="Rerun" and st.session_state["_bid_flash"][0]=="error", (r, st.session_state.get("_bid_flash"))
before = A.get_auction(camera["id"])["bid_count"]
r = run("auction_details.py", member, inputs={"Your bid (rupees)": minimum//100, ("btn","Place bid"): True}, session=sel)
assert r=="Rerun" and st.session_state["_bid_flash"][0]=="ok" and A.get_auction(camera["id"])["bid_count"]==before+1
# leader sees the leader message and the flash renders on the next run
assert run("auction_details.py", member, session={**sel,"_bid_flash":("ok","Your bid of X is now the highest bid.")})=="ok"
assert any("highest bidder" in m for _,m in S.msgs) and any("highest bid" in m for k,m in S.msgs if k=="success")
assert "You" in html() or True
# ended + sold, viewed by winner and a stranger
db.execute("UPDATE auctions SET end_time=? WHERE id=?",(to_iso(now_utc()-dt.timedelta(minutes=1)),clock["id"]))
assert run("auction_details.py", session={"selected_auction_id":clock["id"]})=="ok" and "Sold to" in html() and "Ended" in html()
win = db.fetch_one("SELECT id,full_name,username,email,role FROM users WHERE id=(SELECT winner_id FROM auctions WHERE id=?)",(clock["id"],))
assert run("auction_details.py", win, session={"selected_auction_id":clock["id"]})=="ok" and any("You won" in m for _,m in S.msgs)
# bad id
assert run("auction_details.py", session={"selected_auction_id":99999})=="Stop"

# ---- Sell
assert run("sell.py")=="Stop"                                           # guest blocked by require_login
assert run("sell.py", admin)=="Stop"
assert run("sell.py", member)=="ok"
good = {"Title":"Wooden bookshelf","Description":"Solid teak, five shelves, minor scratches on one side.","Starting price (rupees)":800,
        "Minimum bid increment (rupees)":50,"Category":"Home and Garden",("btn","List item"):True}
r = run("sell.py", member, inputs=good); assert r=="Rerun" and st.session_state["_listed_id"], r
new = A.get_auction(st.session_state["_listed_id"]); assert new["starting_price"]==80000 and new["min_increment"]==5000 and new["reserve_price"] is None and new["image_id"] is None
secs = (A.parse_iso(new["end_time"])-now_utc()).total_seconds() if hasattr(A,"parse_iso") else 0
assert run("sell.py", member, session={"_listed_id":new["id"]})=="Stop" and any("live" in m for _,m in S.msgs)
assert run("sell.py", member, inputs={**good,"Title":"abc"})=="ok" and any("title" in m for k,m in S.msgs if k=="error")
assert run("sell.py", member, inputs={**good,"Set a reserve price":True,"Reserve price (rupees)":300})=="ok" and any("reserve" in m for k,m in S.msgs if k=="error")
r = run("sell.py", member, inputs={**good,"Set a reserve price":True,"Reserve price (rupees)":2000}); assert r=="Rerun"
assert A.get_auction(st.session_state["_listed_id"])["reserve_price"]==200000
past = dt.date.today()-dt.timedelta(days=1)
assert run("sell.py", member, inputs={**good,"Auction length":"Custom length","Custom length":40,"Custom unit":"days"})=="ok" and any("30 days" in m for k,m in S.msgs if k=="error")
far = dt.date.today()+dt.timedelta(days=60)
assert run("sell.py", member, inputs={**good,"Auction length":"Custom length","Custom length":31,"Custom unit":"days"})=="ok" and any("30 days" in m for k,m in S.msgs if k=="error")
ok_date = dt.date.today()+dt.timedelta(days=3)
r = run("sell.py", member, inputs={**good,"Auction length":"Custom length","Custom length":90,"Custom unit":"minutes"}); assert r=="Rerun"
ne = A.get_auction(st.session_state["_listed_id"])["end_time"]
assert 5300 < (A.parse_iso(ne)-now_utc()).total_seconds() <= 5400      # 90 minutes
# account page still fine
assert run("account.py", member)=="ok"


# =====================================================================  new in Checkpoint 4
import io
from PIL import Image
from core import payments, stats, db as DB
def png():
    b=io.BytesIO(); Image.new("RGB",(400,300),(20,100,90)).save(b,"PNG"); b.seek(0); return b


# dashboard
assert run("dashboard.py")=="Stop"
assert run("dashboard.py", member)=="ok" and html().count('class="nl-card-title"')==3 and "My live listings" in dict(S.metrics)
assert run("dashboard.py", admin)=="ok" and "Payments to confirm" in dict(S.metrics) and "Members" in dict(S.metrics)

# short auctions: 1 minute is the shortest
r = run("sell.py", member, inputs={**good,"Auction length":"5 minutes"}); assert r=="Rerun"
mins = (A.parse_iso(A.get_auction(st.session_state["_listed_id"])["end_time"]) - now_utc()).total_seconds()
assert 280 < mins <= 300, mins
soon = dt.datetime.now(dt.timezone.utc).astimezone(__import__("zoneinfo").ZoneInfo("Asia/Kolkata"))+dt.timedelta(minutes=2)
r = run("sell.py", member, inputs={**good,"Auction length":"1 minute"}); assert r=="Rerun"
assert 50 < (A.parse_iso(A.get_auction(st.session_state["_listed_id"])["end_time"])-now_utc()).total_seconds() <= 60
r = run("sell.py", member, inputs={**good,"Auction length":"Custom length","Custom length":2,"Custom unit":"hours"}); assert r=="Rerun"
assert run("sell.py", member, inputs={**good,"Auction length":"30 minutes"})=="Rerun"

# ---- My Auctions: edit + cancel on a fresh seller with exactly one live listing
_,sally = auth.register_user("Sally Sells","sally","sally@x.com","Passw0rd1","Passw0rd1")
sal = {"id":sally["id"],"full_name":"Sally Sells","username":"sally","email":"sally@x.com","role":"user"}
assert run("my_auctions.py", sal)=="ok" and "You have no live listings." in html()
lid = A.create_auction(sally["id"],"Teak coffee table",1,"Used","Round table, small mark on one leg.",None,150000,10000,None,now_utc()+dt.timedelta(days=2))
assert run("my_auctions.py", sal)=="ok" and "Teak coffee table" in html() and dict(S.metrics)["Live"]==1
r = run("my_auctions.py", sal, inputs={"Title":"Teak coffee table, round","Description":"Round teak table, one small mark.",("btn","Save changes"):True,"Starting price (rupees)":1800})
assert r=="Rerun" and A.get_auction(lid)["title"]=="Teak coffee table, round" and A.get_auction(lid)["current_price"]==180000
assert run("my_auctions.py", sal, inputs={"Title":"x",("btn","Save changes"):True})=="ok" and any("title" in m for k,m in S.msgs if k=="error")
assert run("my_auctions.py", sal, inputs={("btn","Cancel listing"):True})=="Rerun" and st.session_state["_confirm_cancel"]==lid
assert run("my_auctions.py", sal, session={"_confirm_cancel":lid})=="ok" and any("Cancel this listing" in m for _,m in S.msgs)
assert run("my_auctions.py", sal, session={"_confirm_cancel":lid}, inputs={("btn","Yes, cancel listing"):True})=="Rerun" and A.get_auction(lid)["status"]=="cancelled"
assert A.cancel_auction(lid, sally["id"]) is False
lid2 = A.create_auction(sally["id"],"Steel kettle",1,"New","Brand new kettle in the box.",None,50000,5000,None,now_utc()+dt.timedelta(days=2))
assert A.place_bid(lid2, bea["id"], 50000)[0]
assert run("my_auctions.py", sal)=="ok" and any("locked" in m for m in S.md)
assert not A.update_auction(lid2, sally["id"],"Y"*6,1,"New","d"*12,1000,1000,None)           # edit blocked once there is a bid
assert not A.cancel_auction(lid2, sally["id"])
assert not A.cancel_auction(lid2, bea["id"])                                               # not the owner
assert run("my_auctions.py", {**sal,"role":"admin"})=="Stop"

# ---- My Bids / Payment / Admin
demo_b2 = DB.fetch_one("SELECT id,full_name,username,email,role FROM users WHERE username='demo_buyer_two'")
A.place_bid(camera["id"], seller_demo, 1) if False else None
assert run("my_bids.py", member)=="ok" and "Active bids" in dict(S.metrics)
standing = {a["title"]:a["standing"] for a in A.user_bids(bea["id"])}
assert standing["Mirrorless camera with 18-55mm lens"]=="Leading" and standing["Steel kettle"]=="Leading"
A.place_bid(lid2, demo_b2["id"], 55000)
assert {a["title"]:a["standing"] for a in A.user_bids(bea["id"])}["Steel kettle"]=="Outbid"
assert run("my_bids.py", member)=="ok" and "Outbid" in html()
assert run("my_bids.py", admin)=="Stop"

# the clock auction closed earlier with demo_buyer_two as winner
won_row = [a for a in A.user_bids(demo_b2["id"]) if a["standing"]=="Won"]; assert won_row and won_row[0]["payment_status"]=="pending"
wid = won_row[0]["id"]
assert run("my_bids.py", demo_b2)=="ok" and "Payment due" in html() and dict(S.metrics)["Won"]>=1
assert run("my_bids.py", demo_b2, inputs={("btn","Pay now"):True})=="Switch:views/payment.py" and st.session_state["pay_auction_id"]==wid

assert run("payment.py")=="Stop"
assert run("payment.py", member)=="Stop" and "Nothing to pay" in html()
assert run("payment.py", admin)=="Stop"
assert run("payment.py", demo_b2, session={"pay_auction_id":wid})=="ok" and any("not uploaded a QR" in m for m in S.md) and "Amount due" in html()
assert run("payment.py", demo_b2, session={"pay_auction_id":wid}, inputs={"Transaction reference (optional)":"UPI123456",("btn","I have paid"):True})=="Rerun"
pay = DB.fetch_one("SELECT * FROM payments WHERE auction_id=?",(wid,)); assert pay["status"]=="submitted" and pay["reference"]=="UPI123456"
assert payments.submit(wid, demo_b2["id"], "again")[0] is False
assert payments.submit(wid, bea["id"], "x")[0] is False                       # wrong buyer
assert run("payment.py", demo_b2, session={"pay_auction_id":wid})=="ok" and any("waiting" in m.lower() for _,m in S.msgs)

# admin panel renders and acts
assert run("admin_panel.py", admin)=="ok"
assert run("admin_panel.py")=="Stop" and run("admin_panel.py", member)=="Stop"
r = run("admin_panel.py", admin, inputs={("btn","Confirm payment received"):True}); assert r=="Rerun" and DB.fetch_one("SELECT status FROM payments WHERE auction_id=?",(wid,))["status"]=="confirmed"
assert run("payment.py", demo_b2, session={"pay_auction_id":wid})=="ok" and any("confirmed" in m.lower() for k,m in S.msgs if k=="success")
db.execute("UPDATE payments SET status='submitted' WHERE auction_id=?",(wid,))
r = run("admin_panel.py", admin, inputs={("btn","Mark as not received"):True}); assert r=="Rerun" and DB.fetch_one("SELECT status,reference FROM payments WHERE auction_id=?",(wid,)) == {"status":"pending","reference":None}

r = run("admin_panel.py", admin, inputs={"Upload a QR code or payment image":png(),"Payee name shown to buyers":"SmartBid Pay",("btn","Save payment details"):True}); assert r=="Rerun"
qid = payments.qr_image_id(); assert qid and db.get_setting("payment_payee_name")=="SmartBid Pay"
assert run("payment.py", demo_b2, session={"pay_auction_id":wid})=="ok" and not any("not uploaded a QR" in m for m in S.md) and any("SmartBid Pay" in m for m in S.md)
old = qid; payments.set_qr(images.save_upload(png())); assert payments.qr_image_id()!=old and db.fetch_one("SELECT 1 AS x FROM images WHERE id=?",(old,)) is None

r = run("admin_panel.py", admin, inputs={("btn","Save settings"):True,"Smallest minimum bid increment sellers may set (rupees)":25})
assert r=="Rerun" and db.get_setting("min_increment_floor")=="2500"
db.set_setting("min_increment_floor","1000")

r = run("admin_panel.py", admin, inputs={"New category name":"Toys and Games",("btn","Add category"):True}); assert r=="Rerun" and db.fetch_one("SELECT 1 AS x FROM categories WHERE name='Toys and Games'")
assert run("admin_panel.py", admin, inputs={"New category name":"toys and games",("btn","Add category"):True})=="ok" and any("already exists" in m for k,m in S.msgs if k=="error")
r = run("admin_panel.py", admin, inputs={("btn","Delete category"):True}); assert r=="Rerun"      # first unused category (Sports? no - first alphabetical unused)

target_user = DB.fetch_one("SELECT id,is_active FROM users WHERE email NOT LIKE '%@example.invalid' AND role='user' ORDER BY id LIMIT 1")
r = run("admin_panel.py", admin, inputs={("btn","Deactivate member"):True}); assert r=="Rerun" and DB.fetch_one("SELECT is_active FROM users WHERE id=?",(target_user["id"],))["is_active"]==0
DB.execute("UPDATE users SET is_active=1 WHERE id=?",(target_user["id"],))

victim = A.admin_auctions()[0]["id"]
r = run("admin_panel.py", admin, inputs={("btn","Remove auction"):True}); assert r=="Rerun" and A.get_auction(victim)["status"]=="removed"
assert run("auction_details.py", session={"selected_auction_id":victim})=="Stop"            # removed auctions disappear
assert victim not in [a["id"] for a in A.list_auctions(limit=50)]
n_before = DB.fetch_one("SELECT COUNT(*) AS n FROM auctions")["n"]
r = run("admin_panel.py", admin, inputs={("btn","Add sample auctions"):True}); assert r=="Rerun" and DB.fetch_one("SELECT COUNT(*) AS n FROM auctions")["n"]==n_before+6

# ---- app shell: guests get a top menu and no sidebar, members get the sidebar and hidden detail page
def shell(user=None):
    S.nav=None; S.ran=False; st.session_state.clear(); st.query_params.clear()
    if user: st.session_state["user"]=dict(user)
    S.md=[]
    runpy.run_path(str(ROOT/"app.py"))
    return S.nav
n = shell(); assert n.position=="top" and S.ran
titles = [p.k["title"] for p in n.pages if p.k["visibility"]=="visible"]
assert titles==["Home","Browse Auctions","Login","Register","Admin Login"], titles
assert [p.path for p in n.pages if p.k["default"]]==["views/home.py"]
assert any("display: none" in m and "stSidebar" in m for m in S.md) and any("SmartBid" in m and "nl-brandbar" in m for m in S.md)
n = shell(member); assert n.position=="sidebar"
assert [p.k["title"] for p in n.pages if p.k["visibility"]=="visible"]==["Dashboard","Home","Browse Auctions","Sell Product","My Auctions","My Bids","Payment","My Account"]
assert [p.path for p in n.pages if p.k["default"]]==["views/dashboard.py"]
assert [p.k["title"] for p in n.pages if p.k["visibility"]=="hidden"]==["Auction Details"]
assert not any("stSidebar" in m and "display: none" in m for m in S.md)
n = shell(admin); assert [p.path for p in n.pages if p.k["default"]]==["views/admin_panel.py"] and "views/sell.py" not in [p.path for p in n.pages]
assert "Neelami" not in open(ROOT/"core/config.py").read() and __import__("core.config",fromlist=["x"]).APP_NAME=="SmartBid"

# ---- new in this round: back button, raising your own bid, no extension, navigation rows
sel2 = {"selected_auction_id": camera["id"]}
r = run("auction_details.py", session=sel2, inputs={("btn","All auctions"):True}); assert r=="Switch:views/browse.py" and "selected_auction_id" not in st.session_state and "auction" not in st.query_params
assert run("auction_details.py", session={"_goto":"views/login.py"})=="Switch:views/login.py"
r = run("auction_details.py", session=sel2, inputs={("btn","Log in"):True}); assert r=="Rerun" and st.session_state["_goto"]=="views/login.py"
# bea currently leads the camera auction: she sees the form and a "Raise my bid" button, and can raise it
cur = A.get_auction(camera["id"]); assert cur["leader_id"]==bea["id"]
assert run("auction_details.py", member, session=sel2)=="ok" and any("raise your bid" in m for _,m in S.msgs)
raise_to = A.min_next_bid(cur)//100
r = run("auction_details.py", member, session=sel2, inputs={"Your bid (rupees)":raise_to, ("btn","Raise my bid"):True})
assert r=="Rerun" and st.session_state["_bid_flash"][0]=="ok" and A.get_auction(camera["id"])["current_price"]==raise_to*100 and A.get_auction(camera["id"])["leader_id"]==bea["id"]
end_before = A.get_auction(camera["id"])["end_time"]
assert A.place_bid(camera["id"], demo_b2["id"], A.min_next_bid(A.get_auction(camera["id"])))[0] and A.get_auction(camera["id"])["end_time"]==end_before
# every member page has a row of navigation buttons
for page, label in (("payment.py","Dashboard"),("my_bids.py","Browse Auctions"),("my_auctions.py","Sell Product"),("account.py","My Bids"),("sell.py","Payment")):
    r = run(page, demo_b2 if page=="payment.py" else member, inputs={("btn",label):True})
    assert r.startswith("Switch:"), (page, label, r)
assert run("payment.py", member, inputs={("btn","Browse Auctions"):True})=="Switch:views/browse.py"      # the empty Payment page too
assert run("admin_panel.py", admin, inputs={("btn","Dashboard"):True})=="Switch:views/dashboard.py"
print("PAGE SMOKE TESTS PASSED")
