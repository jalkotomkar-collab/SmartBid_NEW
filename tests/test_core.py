"""Core tests: database set-up, accounts, login rules, images, money and time formatting.

Run from the project folder:  python tests/test_core.py
The scripts replace Streamlit with a small stand-in, so they run without a browser or a server
and use a temporary SQLite file (your real data/auction.db is never touched).
"""
import sys, types, io, tempfile, pathlib, time
# --- minimal streamlit stub so the non-UI modules can be exercised without Streamlit installed
st = types.ModuleType("streamlit")
def _deco(*a, **k):
    if a and callable(a[0]): 
        f=a[0]; f.clear=lambda:None; return f
    def w(f): f.clear=lambda:None; return f
    return w
st.cache_resource = _deco; st.cache_data = _deco
class SS(dict):
    def __getattr__(self,k): return self.get(k)
st.session_state = SS()
class Secrets:
    def __contains__(self,k): raise FileNotFoundError("no secrets")
st.context = types.SimpleNamespace(headers={'Host': 'localhost:8501'})
st.secrets = Secrets()
sys.modules["streamlit"] = st

root = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(root))
from core import db, auth, utils, images
tmp = pathlib.Path(tempfile.mkdtemp()); db.DB_PATH = tmp/"t.db"

db.init_db()
assert db.fetch_one("SELECT COUNT(*) AS n FROM categories")["n"] == 8
assert db.get_setting("min_increment_floor") == "1000"
db.set_setting("min_increment_floor","2500"); assert db.get_setting("min_increment_floor")=="2500"

# the test admin must NOT be created for a public host, hosted DB, or non-local access
for host in ("myapp.streamlit.app", "192.168.1.5:8501", ""):
    st.context.headers = {"Host": host}
    assert auth.ensure_admin() == "missing" and not db.fetch_one("SELECT 1 AS x FROM users WHERE role='admin'"), host
st.context.headers = {}
assert auth.ensure_admin() == "missing"
st.context.headers = {"Host": "[::1]:8501"}
assert auth.ensure_admin() == "dev"
db.execute("DELETE FROM users WHERE role='admin'")
st.context.headers = {"Host": "localhost:8501"}
assert auth.ensure_admin() == "dev"
assert auth.ensure_admin() is None                       # idempotent
ok, u = auth.attempt_login("admin","Admin@12345","admin"); assert ok and u["role"]=="admin"
ok, m = auth.attempt_login("admin","Admin@12345","user");  assert not ok and "Admin login" in m
ok, m = auth.attempt_login("admin","wrong","admin");       assert not ok and m=="Incorrect username or password."

for args,frag in [(("Ann Lee","bob","bob@x.com","pass","pass"),"8 characters"),
                  (("Ann Lee","b!","bob@x.com","Passw0rdd","Passw0rdd"),"Usernames"),
                  (("Ann Lee","bobby","nope","Passw0rdd","Passw0rdd"),"email"),
                  (("Ann Lee","bobby","b@x.com","Passw0rdd","Different1"),"match"),
                  (("","bobby","b@x.com","Passw0rdd","Passw0rdd"),"full name")]:
    ok,m = auth.register_user(*args); assert not ok and frag in m, (args,m)
ok,u = auth.register_user("Bob Rao","bobby","Bob@X.com","Passw0rdd","Passw0rdd"); assert ok and u["role"]=="user"
ok,m = auth.register_user("Bob 2","BOBBY","other@x.com","Passw0rdd","Passw0rdd"); assert not ok and "taken" in m   # case-insensitive
ok,m = auth.register_user("Bob 2","bob2","bob@x.com","Passw0rdd","Passw0rdd");    assert not ok and "email" in m
ok,u = auth.attempt_login("bob@x.com","Passw0rdd","user"); assert ok and u["username"]=="bobby"
ok,m = auth.attempt_login("bobby","Passw0rdd","admin");    assert not ok and "administrator access" in m
ok,m = auth.change_password(u["id"],"Passw0rdd","NewPass99","NewPass99"); assert ok
assert auth.attempt_login("bobby","NewPass99","user")[0]
db.execute("UPDATE users SET is_active=0 WHERE username='bobby'")
ok,m = auth.attempt_login("bobby","NewPass99","user"); assert not ok and "deactivated" in m

st.session_state.clear()
for _ in range(5): auth.attempt_login("admin","bad","admin")
ok,m = auth.attempt_login("admin","Admin@12345","admin"); assert not ok and "Too many" in m

# images
from PIL import Image
buf = io.BytesIO(); Image.new("RGB",(3000,2000),(200,30,30)).save(buf,"PNG"); buf.seek(0)
iid = images.save_upload(buf); data = images.load_image(iid); im = Image.open(io.BytesIO(data)); assert max(im.size)==1000
try: images.save_upload(io.BytesIO(b"not an image")); assert False
except ValueError: pass
assert images.product_image(None).endswith("product_placeholder.jpg")
assert images.data_uri("favicon.png").startswith("data:image/png;base64,")

# utils
f = utils.format_inr
assert f(0)=="₹0" and f(100)=="₹1" and f(99900)=="₹999" and f(100000)=="₹1,000"
assert f(123456700)=="₹12,34,567" and f(1050)=="₹10.50" and f(10000000000)=="₹10,00,00,000"
assert utils.to_paise("1499.5")==149950 and utils.to_paise(10)==1000
try: utils.to_paise("abc"); assert False
except ValueError: pass
iso = utils.to_iso(utils.now_utc()); assert utils.format_local(iso)
from datetime import timedelta
assert utils.time_left_text(utils.to_iso(utils.now_utc()+timedelta(hours=50))).startswith("2d")
assert utils.time_left_text(utils.to_iso(utils.now_utc()-timedelta(seconds=5)))=="Ended"
print("ALL CORE TESTS PASSED")
