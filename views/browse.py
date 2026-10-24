"""Browse Auctions: search, filter, sort and open an auction."""
import streamlit as st

from core import auctions, auth, db, ui

PAGE_SIZE = 12

ui.page_header(
    "Browse auctions",
    "Find something worth bidding on. Every price is in rupees and every auction has a clock.",
    "banner_browse.jpg",
)

categories = db.fetch_all("SELECT id, name FROM categories ORDER BY name")
category_ids = {c["name"]: c["id"] for c in categories}

f1, f2, f3, f4 = st.columns([2.2, 1.4, 1.4, 1.2], vertical_alignment="bottom")
search = f1.text_input("Search", placeholder="Search titles and descriptions", key="browse_search")
category = f2.selectbox("Category", ["All categories"] + list(category_ids), key="browse_category")
sort = f3.selectbox("Sort by", list(auctions.SORTS), key="browse_sort")
view = f4.segmented_control("Show", ["Live", "Ended"], default="Live", key="browse_view") or "Live"
live = view == "Live"

# Start from the first page again whenever the filters change.
signature = (search, category, sort, view)
if st.session_state.get("browse_sig") != signature:
    st.session_state["browse_sig"] = signature
    st.session_state["browse_limit"] = PAGE_SIZE
limit = st.session_state.get("browse_limit", PAGE_SIZE)

results = auctions.list_auctions(
    search=search,
    category_id=category_ids.get(category),
    sort=sort,
    live=live,
    limit=limit + 1,
)
has_more = len(results) > limit
results = results[:limit]

if not results:
    st.markdown("### Nothing here yet")
    if search or category != "All categories":
        st.write("No auctions match these filters. Clear the search or choose another category.")
    elif live:
        st.write("There are no live auctions right now.")
    else:
        st.write("No auctions have ended yet.")
    if auth.is_logged_in() and live and ui.page_exists("views/sell.py"):
        ui.nav_button("List the first item", "views/sell.py", icon=":material/sell:", key="browse_to_sell")
else:
    st.caption(f"Showing {len(results)} {'live' if live else 'ended'} auction{'s' if len(results) != 1 else ''}")
    for start in range(0, len(results), 3):
        cols = st.columns(3, gap="medium")
        for col, auction in zip(cols, results[start:start + 3]):
            with col:
                ui.auction_card(auction, key_prefix="browse")
    if has_more:
        if st.button("Show more auctions", icon=":material/expand_more:"):
            st.session_state["browse_limit"] = limit + PAGE_SIZE
            st.rerun()
