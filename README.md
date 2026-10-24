# SmartBid

SmartBid is a multi-page online auction web app. Members list products, bid on each
other's items, and pay for what they win. An administrator manages the marketplace and
sets the payment QR code. It is written entirely in Python: **Streamlit** for the
interface and **SQLite** for the data. All prices are in rupees.

> The payment page is a demonstration. It shows an image chosen by the administrator
> (for example a UPI QR code) and records that the buyer says they paid. No money is
> processed by the app.

## Features

| Area | What it does |
|---|---|
| Accounts | Register, log in, change password. Passwords are salted and hashed (PBKDF2). Five wrong logins lock the form for 60 seconds. |
| Selling | List an item with photo, category, condition, description, starting price, **minimum bid increment**, optional reserve price and a length from **1 minute to 30 days**. Edit or cancel a listing while it has no bids. |
| Bidding | Each bid must beat the current price by at least the auction's minimum increment. The highest bid when the clock ends wins, and the clock is never extended. You can raise your own bid while you lead. Sellers cannot bid on their own items. |
| Browsing | Search, category filter, five sort orders, Live and Ended views. Auction Details refreshes price, clock and bid history every 5 seconds. |
| Payment | Winners see the amount due and the administrator's QR image, then tell the app they paid. The administrator confirms. |
| Admin | Overview, remove auctions, deactivate members, manage categories, confirm payments, upload the payment QR, change bidding rules. |

## Pages

| Page | Who | Purpose |
|---|---|---|
| Home | Everyone | A short welcome. After login it shows your bids placed and items listed |
| Login, Register, Admin Login | Logged out | Sign in or create an account |
| Browse Auctions | Everyone | Find auctions |
| Auction Details | Everyone (bidding needs a member login) | Photo, description, live price and clock, bid form, bid history |
| Dashboard | Logged in | Your numbers, latest bids and listings, and the auctions closing soon |
| Sell Product | Members | List an item |
| My Auctions | Members | Your listings: live, ended, cancelled |
| My Bids | Members | Auctions you bid on: leading, outbid, won, lost |
| Payment | Members | Pay for won auctions |
| My Account | Logged in | Details and password |
| Admin Panel | Administrator | Manage everything |

Logged-out visitors get a top menu and no sidebar. The sidebar appears after login.

## Project structure

```
app.py                  entry point: theme, startup, navigation
requirements.txt        pinned dependencies
.streamlit/
  config.toml           light theme and server settings
  secrets.toml.example  template for admin login and database settings
core/                   logic: database, auth, auctions, payments, stats, images, styling
views/                  one file per page
assets/placeholders/    bundled placeholder images (see below)
scripts/                make_placeholders.py regenerates the placeholder images
data/                   local SQLite file, created on first run (git-ignored)
```

## Run it on your computer

You need Python 3.10 or newer.

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate            # Windows (Command Prompt)
# venv\Scripts\Activate.ps1      # Windows (PowerShell)
# source venv/bin/activate       # macOS / Linux

# 2. Install
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

Open <http://localhost:8501>.

**The database is created for you.** On first run the app creates `data/auction.db`,
all tables, the categories and settings, six demo listings and a test administrator.
To start over, stop the app and delete `data/auction.db`.

**Test administrator (local only):** username `admin`, password `Admin@12345`. It is
created only when the app is opened at `localhost`, and never on a deployed site. To use
your own admin instead, copy `.streamlit/secrets.toml.example` to
`.streamlit/secrets.toml` and fill in `ADMIN_USERNAME`, `ADMIN_EMAIL` and `ADMIN_PASSWORD`
before the first run. Change the password later in **My Account**.

## Configuration

Settings come from environment variables or `.streamlit/secrets.toml`.

| Key | Purpose |
|---|---|
| `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Creates the first administrator. Required when deployed. |
| `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` | Use a hosted Turso database instead of the local file. Required on Streamlit Community Cloud. |
| `SEED_SAMPLE_DATA` | Set to `"0"` to skip the demo listings. |

Other settings: name, currency symbol and time zone are in `core/config.py`. The smallest
minimum bid increment sellers may set is in **Admin Panel, Settings**.

## Deploy with GitHub and Streamlit Community Cloud

Streamlit Community Cloud deletes any file the app writes whenever the app restarts, so
a local SQLite file would lose all accounts and auctions. SmartBid therefore uses
**Turso**, a hosted SQLite service, when you give it a database URL. The SQL is the same.
Images are stored inside the database too, so they survive restarts.

### 1. Push the project to GitHub

```bash
git init
git add .
git commit -m "SmartBid auction app"
git branch -M main
```

Create an empty repository at <https://github.com/new> (no README, no .gitignore), then:

```bash
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

The `.gitignore` keeps your virtual environment, local database and
`.streamlit/secrets.toml` out of the repository. Check on GitHub that none of them appear.

### 2. Create the Turso database

Create a free account at <https://turso.tech>. With the Turso CLI (on Windows it runs
inside WSL; you can also use the Turso web dashboard):

```bash
turso auth login
turso db create smartbid
turso db show smartbid --url        # copy: libsql://smartbid-<you>.turso.io
turso db tokens create smartbid     # copy the token
```

### 3. Deploy on Streamlit Community Cloud

1. Go to <https://share.streamlit.io> and sign in with GitHub.
2. Click **Create app**, choose your repository, branch `main`, and main file path `app.py`.
3. Click **Advanced settings**. Choose **Python 3.12**. You cannot change the Python
   version after deploying without deleting and redeploying the app.
4. In **Secrets**, paste (with your own values):

   ```toml
   ADMIN_USERNAME = "admin"
   ADMIN_EMAIL = "you@example.com"
   ADMIN_PASSWORD = "a-long-unique-password"
   TURSO_DATABASE_URL = "libsql://smartbid-<you>.turso.io"
   TURSO_AUTH_TOKEN = "the-token-from-step-2"
   ```

5. Click **Deploy**. The first start creates the tables and demo listings in Turso.
6. Log in through **Admin Login** with the username and password from the secrets,
   then open **Admin Panel, Payment QR** and upload your payment QR image.

Pushing new commits to `main` redeploys the app automatically. Your data stays in Turso.

## Placeholder images

No real photographs are bundled. Every image is a generated placeholder in
`assets/placeholders/`. To use your own pictures, replace the file with one of the same
name (and similar shape), or edit `scripts/make_placeholders.py` and run it.

| File | Where it appears |
|---|---|
| `hero_home.jpg` | Home page hero (sits on a coloured panel) |
| `auth_login.jpg`, `auth_register.jpg`, `auth_admin.jpg` | Side image on Login, Register, Admin Login |
| `banner_dashboard.jpg` | Dashboard banner |
| `banner_browse.jpg` | Browse Auctions banner |
| `banner_sell.jpg` | Sell Product banner |
| `banner_my_auctions.jpg` | My Auctions banner |
| `banner_my_bids.jpg` | My Bids banner |
| `banner_payment.jpg` | Payment banner |
| `banner_admin.jpg` | Admin Panel banner |
| `banner_account.jpg` | My Account banner |
| `product_placeholder.jpg` | Any listing without a photo (cards, Auction Details, Sell preview) |
| `qr_placeholder.jpg` | Payment page and Admin Panel until a real QR is uploaded |
| `sample_lamp.jpg`, `sample_camera.jpg`, `sample_print.jpg`, `sample_clock.jpg`, `sample_vase.jpg`, `sample_books.jpg` | The six demo listings |
| `favicon.png` | Browser tab icon and the logo bar |

Product photos on Browse Auctions and Auction Details are whatever sellers upload.

## Good to know

- Logging in lasts for the browser tab. A full page refresh signs you out.
- Expired auctions are closed when anyone loads a page, since Streamlit has no background
  scheduler.
- Auctions end exactly at their end time. Very short auctions (even 1 minute) are possible.
- There are no emails or notifications. People see results when they open the app.
- The demo listings end within a few days. Use **Admin Panel, Settings, Add sample
  auctions** to refill an empty site, or set `SEED_SAMPLE_DATA = "0"` before the first run.

## Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit` is not recognized | Activate the virtual environment, or run `python -m streamlit run app.py`. |
| `pip install` fails on a package for your Python version | Use Python 3.10 to 3.13 or the exact pins in `requirements.txt`. |
| "The database could not be opened" on the deployed site | Recheck `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` in the app's Secrets. |
| No admin on the deployed site | Add `ADMIN_USERNAME` and `ADMIN_PASSWORD` to Secrets, then reboot the app. |
| Sample listings are missing locally | Delete `data/auction.db` and start again. |
