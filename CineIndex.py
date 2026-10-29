import os, hashlib, re
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus
from html import unescape, escape

import pandas as pd
import requests
import feedparser
import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="CinePulse — Indian Cinema, in focus", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")

# Editorial cinema-inspired visual system
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
:root { --ink:#f7f3ec; --muted:#b7b1a8; --panel:#191a1d; --panel2:#202126; --line:rgba(255,255,255,.09); --accent:#f2a65a; }
.stApp { background: radial-gradient(ellipse at 80% 0%, rgba(111,62,39,.20), transparent 32%), #101114; color:var(--ink); }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.block-container { max-width:1440px; padding-top:1.7rem; padding-bottom:3rem; }
[data-testid="stSidebar"] { background:#17181b; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:var(--ink); }
.eyebrow { color:var(--accent); font-size:.72rem; font-weight:700; letter-spacing:.18em; text-transform:uppercase; margin-bottom:.65rem; }
.hero { background:linear-gradient(115deg,rgba(39,30,27,.98),rgba(25,26,30,.94)); border:1px solid rgba(242,166,90,.22); border-radius:24px; padding:30px 32px 26px; margin:0 0 22px; position:relative; overflow:hidden; }
.hero:after { content:'✦'; position:absolute; right:35px; top:12px; font-size:7rem; line-height:1; color:rgba(242,166,90,.10); }
.hero h1 { font-family:'Playfair Display',serif; font-size:clamp(2.15rem,4vw,3.45rem); line-height:1.08; letter-spacing:-.04em; margin:0 0 12px; color:#fff8ef; }
.hero p { color:#c8c0b6; max-width:700px; font-size:1rem; margin:0; line-height:1.65; }
.hero .hero-tag { display:inline-block; margin-top:19px; padding:7px 11px; border:1px solid rgba(242,166,90,.35); border-radius:999px; color:#f5bd83; font-size:.75rem; letter-spacing:.04em; }
.section-heading { font-family:'Playfair Display',serif; font-size:1.55rem; color:#fff8ef; margin:0 0 .25rem; }
.section-sub { color:var(--muted); font-size:.88rem; margin-bottom:1rem; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#202126,#191a1e); border:1px solid var(--line); padding:16px 18px; border-radius:16px; }
[data-testid="stMetricLabel"] { color:#b7b1a8 !important; font-size:.8rem; }
[data-testid="stMetricValue"] { color:#fff8ef !important; font-size:1.5rem !important; }
.stTabs [data-baseweb="tab-list"] { gap:8px; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { background:transparent; border-radius:10px 10px 0 0; color:#b7b1a8; padding:12px 16px; }
.stTabs [aria-selected="true"] { color:#f2a65a !important; border-bottom:2px solid #f2a65a; }
.stTextInput input, .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] { background:#202126; border-color:#393a40; border-radius:10px; }
.stButton > button { border-radius:10px; border:1px solid #44454b; background:#25262b; color:#f7f3ec; font-weight:600; transition:all .15s ease; }
.stButton > button:hover { border-color:#f2a65a; color:#ffc58c; }
.stButton > button[kind="primary"] { background:#e99a4b; color:#181513; border-color:#e99a4b; }
.stButton > button[kind="primary"]:hover { background:#f6b36c; color:#181513; }
.story-card { height:100%; background:linear-gradient(155deg,#202126,#191a1d); border:1px solid var(--line); border-radius:17px; padding:20px; margin-bottom:12px; }
.story-kicker { color:#f2a65a; text-transform:uppercase; font-size:.68rem; letter-spacing:.13em; font-weight:700; margin-bottom:9px; }
.story-title { color:#fff8ef; font-family:'Playfair Display',serif; font-size:1.18rem; line-height:1.4; font-weight:600; margin-bottom:10px; }
.story-meta { color:#a8a29a; font-size:.75rem; margin-bottom:12px; }
.story-summary { color:#d0cbc4; font-size:.88rem; line-height:1.6; }
hr { border-color:var(--line); }
[data-testid="stAlert"] { border-radius:12px; }
footer { visibility:hidden; }
.movie-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:18px; }
.movie-tile { display:block; text-decoration:none !important; color:inherit !important; min-width:0; background:#191a1d; border:1px solid rgba(255,255,255,.09); border-radius:15px; overflow:hidden; transition:transform .18s ease,border-color .18s ease; }
.movie-tile:hover { transform:translateY(-4px); border-color:rgba(242,166,90,.65); }
.poster-wrap { position:relative; aspect-ratio:2/3; background:linear-gradient(145deg,#292a30,#17181b); overflow:hidden; }
.poster-wrap img { width:100%; height:100%; object-fit:cover; display:block; }
.rating-pill { position:absolute; top:9px; left:9px; background:rgba(10,11,13,.88); color:#ffd27c; padding:6px 8px; border:1px solid rgba(255,255,255,.16); border-radius:8px; font-size:.78rem; font-weight:800; }
.movie-info { padding:11px 12px 14px; }
.movie-title { color:#fff8ef; font-weight:700; font-size:.93rem; line-height:1.35; margin-bottom:5px; }
.movie-meta { color:#aaa49b; font-size:.75rem; line-height:1.5; }
.movie-rank { color:#f2a65a; font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; font-weight:800; margin-bottom:5px; }
@media(max-width:1100px){.movie-grid{grid-template-columns:repeat(4,minmax(0,1fr));}}
@media(max-width:800px){.movie-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;}}
@media(max-width:520px){.movie-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;}}
</style>
<div class="hero">
  <div class="eyebrow">The Indian cinema briefing</div>
  <h1>Stories behind<br>the silver screen.</h1>
  <p>Your daily lens on Indian cinema — from first-look posters and trailers to box-office moves, reviews and OTT premieres. Curated from public news feeds, with every story linked to its original publisher.</p>
  <span class="hero-tag">✦ BOLLYWOOD · SOUTH CINEMA · BOX OFFICE · OTT</span>
</div>
""", unsafe_allow_html=True)

RSS_SOURCES = [
    ("India Cinema", "Indian cinema Bollywood Telugu Tamil Malayalam Kannada movie news"),
    ("Bollywood", "Bollywood Hindi film movie news"),
    ("Telugu Cinema", "Telugu cinema Tollywood movie news"),
    ("Tamil Cinema", "Tamil cinema Kollywood movie news"),
    ("Malayalam Cinema", "Malayalam cinema movie news"),
    ("Kannada Cinema", "Kannada cinema Sandalwood movie news"),
    ("Box Office", "Indian film box office collection"),
    ("Trailers & Releases", "Indian movie official trailer release date"),
    ("Reviews", "Indian movie film review"),
    ("OTT Releases", "Indian movie OTT release")
]
CATEGORIES = ["All Indian Cinema", "Bollywood", "Telugu Cinema", "Tamil Cinema", "Malayalam Cinema",
              "Kannada Cinema", "Box Office", "Trailers & Releases", "Reviews", "OTT Releases"]
TIMEOUT = 15

def get_supabase() -> Client:
    # Read Streamlit secrets without ever displaying their values.
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
    except Exception as exc:
        st.error(f"Could not read Streamlit Secrets ({type(exc).__name__}). Open the settings for this exact deployed app and verify the TOML format.")
        st.stop()
    if not url or not key:
        present = list(st.secrets.keys())
        st.error("Supabase credentials are missing. Expected SUPABASE_URL and SUPABASE_KEY in this app's Secrets.")
        st.caption("Secret names detected: " + (", ".join(present) if present else "none") + ". Secret values are never displayed.")
        st.stop()
    try:
        return create_client(url, key)
    except Exception as exc:
        st.error(f"Supabase client could not initialize ({type(exc).__name__}). Check that SUPABASE_URL is the project URL and SUPABASE_KEY is a publishable/anon key.")
        st.stop()

def strip_html(s):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def fetch_rss(label, query):
    url = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
    response = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "IndianCinemaPulse/1.0 RSS reader"})
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for entry in feed.entries:
        link = entry.get("link", "")
        if not link:
            continue
        title = strip_html(entry.get("title", "Untitled"))
        source_name = entry.get("source", {}).get("title", label)
        published = entry.get("published", entry.get("updated", ""))
        summary = strip_html(entry.get("summary", entry.get("description", "")))[:1000]
        rows.append({
            "article_id": hashlib.sha256(link.encode("utf-8")).hexdigest()[:32],
            "title": title,
            "link": link,
            "source": source_name,
            "published_at": published,
            "summary": summary,
            "category": label,
            "fetched_at": now
        })
    return rows

def sync_feeds(sb, selected_sources):
    progress = st.progress(0, text="Fetching public RSS feeds…")
    all_rows, errors = [], []
    for i, (label, query) in enumerate(selected_sources):
        try:
            all_rows.extend(fetch_rss(label, query))
        except Exception as e:
            errors.append(f"{label}: {type(e).__name__}: {e}")
        progress.progress((i + 1) / max(len(selected_sources), 1), text=f"Checked {label}")
    progress.empty()
    # Upsert in chunks to avoid request size limits
    inserted = 0
    for i in range(0, len(all_rows), 100):
        chunk = all_rows[i:i+100]
        if chunk:
            sb.table("articles").upsert(chunk, on_conflict="article_id").execute()
            inserted += len(chunk)
    return inserted, errors

def get_articles(sb, limit=500):
    result = sb.table("articles").select("*").order("published_at", desc=True).limit(limit).execute()
    return pd.DataFrame(result.data or [])

def get_saved_ids(sb):
    try:
        result = sb.table("saved_articles").select("article_id").execute()
        return {r["article_id"] for r in (result.data or [])}
    except Exception:
        return set()

def save_article(sb, article_id):
    sb.table("saved_articles").upsert({"article_id": article_id}, on_conflict="article_id").execute()

def unsave_article(sb, article_id):
    sb.table("saved_articles").delete().eq("article_id", article_id).execute()

def get_optional_secret(name):
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""

@st.cache_data(ttl=900, show_spinner=False)
def fetch_tmdb_titles(api_key, period, media_type, language_filter):
    base = "https://api.themoviedb.org/3"
    params = {"api_key": api_key, "language": "en-US", "region": "IN", "with_origin_country": "IN", "include_adult": "false"}
    if period == "week":
        url = f"{base}/trending/{media_type}/week"
        params.pop("with_origin_country", None)
    elif period == "month":
        url = f"{base}/discover/{media_type}"
        params.update({"sort_by": "popularity.desc", "vote_count.gte": 5})
        since = (datetime.now(timezone.utc).date() - timedelta(days=30)).isoformat()
        if media_type == "movie":
            params["primary_release_date.gte"] = since
            params["primary_release_date.lte"] = datetime.now(timezone.utc).date().isoformat()
        else:
            params["first_air_date.gte"] = since
            params["first_air_date.lte"] = datetime.now(timezone.utc).date().isoformat()
    else:
        url = f"{base}/discover/{media_type}"
        params.update({"sort_by": "vote_average.desc", "vote_count.gte": 250, "page": 1})
    if language_filter != "All languages":
        lang_map = {"Hindi":"hi", "Telugu":"te", "Tamil":"ta", "Malayalam":"ml", "Kannada":"kn", "Bengali":"bn", "Marathi":"mr"}
        code = lang_map.get(language_filter)
        if code:
            params["with_original_language"] = code
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    results = response.json().get("results", [])
    if period == "week":
        filtered = []
        for item in results:
            origin = item.get("origin_country") or []
            lang = item.get("original_language", "")
            if "IN" in origin or lang in {"hi", "te", "ta", "ml", "kn", "bn", "mr"}:
                filtered.append(item)
        results = filtered or results
    normalized = []
    for item in results[:30]:
        title = item.get("title") or item.get("name") or item.get("original_title") or item.get("original_name") or "Untitled"
        date = item.get("release_date") or item.get("first_air_date") or ""
        normalized.append({
            "id": item.get("id"), "media_type": item.get("media_type", media_type),
            "title": title, "year": date[:4] if date else "Year unknown",
            "poster": ("https://image.tmdb.org/t/p/w500" + item["poster_path"]) if item.get("poster_path") else "",
            "tmdb_rating": item.get("vote_average"), "language": item.get("original_language", "").upper(),
            "popularity": item.get("popularity", 0), "vote_count": item.get("vote_count", 0)
        })
    return normalized

@st.cache_data(ttl=86400, show_spinner=False)
def get_imdb_rating(omdb_api_key, title, year):
    if not omdb_api_key:
        return "Add OMDb key"
    try:
        params = {"apikey": omdb_api_key, "t": title}
        if str(year).isdigit():
            params["y"] = year
        data = requests.get("https://www.omdbapi.com/", params=params, timeout=10).json()
        rating = data.get("imdbRating")
        if data.get("Response") == "True" and rating and rating != "N/A":
            return rating
    except Exception:
        pass
    return "—"

def render_movie_grid(items, omdb_api_key, label):
    if not items:
        st.info("No titles came back for this filter. Try another language or refresh shortly.")
        return
    cards = []
    for i, item in enumerate(items[:25], start=1):
        rating = get_imdb_rating(omdb_api_key, item["title"], item["year"])
        if rating == "Add OMDb key":
            rating_label = "★ IMDb key needed"
        elif rating == "—":
            rating_label = "★ IMDb —"
        else:
            rating_label = f"★ IMDb {escape(str(rating))}"
        poster = escape(item.get("poster") or "https://placehold.co/400x600/202126/f2a65a?text=No+Poster", quote=True)
        title = escape(str(item.get("title", "Untitled")))
        year = escape(str(item.get("year", "")))
        lang = escape(str(item.get("language", "")))
        media = "Series" if item.get("media_type") == "tv" else "Movie"
        query = quote_plus(f'{item.get("title", "")} {item.get("year", "")} Indian {media}')
        google_url = f"https://www.google.com/search?q={query}"
        card = f'''<a class="movie-tile" href="{google_url}" target="_blank" rel="noopener noreferrer" title="Search Google for {title}">
          <div class="poster-wrap"><img src="{poster}" alt="Poster for {title}" loading="lazy"><span class="rating-pill">{rating_label}</span></div>
          <div class="movie-info"><div class="movie-rank">{label} #{i}</div><div class="movie-title">{title}</div><div class="movie-meta">{year} &nbsp;·&nbsp; {lang} &nbsp;·&nbsp; {media}</div></div></a>'''
        cards.append(card)
    st.markdown('<div class="movie-grid">' + "\n".join(cards) + '</div>', unsafe_allow_html=True)

sb = get_supabase()
with st.sidebar:
    st.markdown("<div class='eyebrow'>CINEPULSE</div>", unsafe_allow_html=True)
    st.markdown("### Your cinema desk")
    st.caption("Find the stories worth following.")
    st.divider()
    category = st.selectbox("Category", CATEGORIES)
    query_text = st.text_input("Search headlines", placeholder="e.g. Rajinikanth, box office, trailer")
    st.divider()
    st.subheader("Feed refresh")
    selected_labels = st.multiselect("Sources", [x[0] for x in RSS_SOURCES], default=[x[0] for x in RSS_SOURCES])
    refresh_now = st.button("🔄 Fetch latest headlines", type="primary", use_container_width=True)
    st.caption("Refresh pulls the latest entries available in public RSS search feeds. Publisher updates and feed availability vary.")

if refresh_now or "did_initial_refresh" not in st.session_state:
    selected = [x for x in RSS_SOURCES if x[0] in selected_labels]
    if selected:
        with st.spinner("Checking public feeds and saving new headlines to Supabase…"):
            try:
                count, errors = sync_feeds(sb, selected)
                st.session_state.did_initial_refresh = True
                st.session_state.last_refresh = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
                st.success(f"Processed {count} feed entries. Supabase has been updated.")
                if errors:
                    with st.expander(f"{len(errors)} feed(s) could not be fetched"):
                        st.write("\n".join(errors))
            except Exception as e:
                st.error(f"Supabase sync failed: {type(e).__name__}: {e}")

try:
    articles = get_articles(sb)
except Exception as e:
    st.error(f"Could not read articles from Supabase: {type(e).__name__}: {e}")
    st.stop()

saved_ids = get_saved_ids(sb)
if articles.empty:
    st.warning("Your Supabase articles table is empty. Click Fetch latest headlines to populate it.")
else:
    articles["search_blob"] = (articles["title"].fillna("") + " " + articles["summary"].fillna("") + " " + articles["source"].fillna("") + " " + articles["category"].fillna("")).str.lower()
    if category != "All Indian Cinema":
        category_term = category.lower().replace(" & ", " ")
        if category == "Bollywood":
            category_term = "bollywood"
        articles = articles[articles["search_blob"].str.contains(category_term, regex=False, na=False)]
    if query_text.strip():
        articles = articles[articles["search_blob"].str.contains(query_text.strip().lower(), regex=False, na=False)]

m1, m2, m3 = st.columns(3)
m1.metric("Stories in view", f"{len(articles):,}")
m2.metric("Saved to watchlist", f"{len(saved_ids):,}")
m3.metric("Last synced", st.session_state.get("last_refresh", "Not yet this session"))

st.markdown("<div style='height:10px'></div><div class='section-heading'>Explore Indian cinema</div><div class='section-sub'>Discover movies and series first. Catch up on headlines when you want the story behind them.</div>", unsafe_allow_html=True)
tab_discover, tab_feed, tab_watchlist, tab_info = st.tabs(["✦  Discover & Trending", "▤  Cinema News", "♡  Watchlist", "ⓘ  About & setup"])

with tab_discover:
    tmdb_api_key = get_optional_secret("dd1762e251cdf72c775801f7dd9c3615")
    omdb_api_key = get_optional_secret("8d604a92")
    st.markdown("<div class='section-heading'>The titles everyone's talking about</div><div class='section-sub'>Posters, verified IMDb ratings when available, and one-click Google discovery.</div>", unsafe_allow_html=True)
    if not tmdb_api_key:
        st.warning("Movie discovery needs a TMDB API key. Add TMDB_API_KEY in Streamlit → App settings → Secrets. Add OMDB_API_KEY too to show actual IMDb ratings on posters.")
        st.markdown("Get keys: [TMDB developer API](https://www.themoviedb.org/settings/api) · [OMDb API](http://www.omdbapi.com/?i=tt3896198&apikey=8d604a92)")
    else:
        c1, c2 = st.columns([1.3, 1])
        with c1:
            trend = st.selectbox("Explore by", ["Trending this week", "Trending this month", "All-time favourites"], key="movie_period")
        with c2:
            language_filter = st.selectbox("Language", ["All languages", "Hindi", "Telugu", "Tamil", "Malayalam", "Kannada", "Bengali", "Marathi"], key="movie_language")
        movie_kind = st.radio("Show", ["Movies", "Web series", "Both"], horizontal=True, key="movie_kind")
        period_key = {"Trending this week":"week", "Trending this month":"month", "All-time favourites":"all"}[trend]
        kinds = ["movie", "tv"] if movie_kind == "Both" else (["movie"] if movie_kind == "Movies" else ["tv"])
        all_titles = []
        try:
            with st.spinner("Finding titles and checking IMDb ratings…"):
                for kind in kinds:
                    all_titles.extend(fetch_tmdb_titles(tmdb_api_key, period_key, kind, language_filter))
            all_titles.sort(key=lambda x: (x.get("popularity", 0), x.get("tmdb_rating") or 0), reverse=True) if period_key != "all" else all_titles.sort(key=lambda x: (x.get("tmdb_rating") or 0, x.get("vote_count") or 0), reverse=True)
            seen, unique_titles = set(), []
            for item in all_titles:
                k = (item["title"].lower(), item["year"])
                if k not in seen:
                    seen.add(k)
                    unique_titles.append(item)
            if not omdb_api_key:
                st.caption("IMDb ratings come from OMDb. Add OMDB_API_KEY in Secrets to show real IMDb scores; TMDB scores will not be mislabeled as IMDb ratings.")
            render_movie_grid(unique_titles, omdb_api_key, trend)
            st.caption("Posters and discovery data are provided by TMDB. 'Trending this month' uses titles released in the last 30 days; 'All-time favourites' is a high-vote, high-rating discovery ranking. Click any tile to search Google.")
        except Exception as e:
            st.error(f"Could not load movie discovery ({type(e).__name__}). Check TMDB_API_KEY and try again.")

def display_rows(frame):
    if frame.empty:
        st.info("No stories match these filters yet. Try another category or refresh the feeds.")
        return
    for _, row in frame.head(100).iterrows():
        article_id = row["article_id"]
        title = str(row.get("title", "Untitled"))
        source = str(row.get("source", "Cinema desk"))
        published = str(row.get("published_at", "Publication time unavailable"))
        summary = str(row.get("summary", "") or "")
        category_label = escape(str(row.get("category", "Indian Cinema")))
        title = escape(title)
        source = escape(source)
        published = escape(published)
        summary = escape(summary)
        st.markdown(
            "<div class='story-card'>"
            f"<div class='story-kicker'>{category_label}</div>"
            f"<div class='story-title'>{title}</div>"
            f"<div class='story-meta'>{source} &nbsp;·&nbsp; {published}</div>"
            f"<div class='story-summary'>{summary[:350]}{'…' if len(summary)>350 else ''}</div>"
            "</div>", unsafe_allow_html=True
        )
        c1, c2, c3 = st.columns([1.15, 1.5, 5])
        with c1:
            if article_id in saved_ids:
                if st.button("♥ Saved", key=f"unsave_{article_id}", use_container_width=True):
                    try:
                        unsave_article(sb, article_id)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not remove bookmark: {e}")
            else:
                if st.button("♡ Save story", key=f"save_{article_id}", use_container_width=True):
                    try:
                        save_article(sb, article_id)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not save bookmark: {e}")
        with c2:
            st.link_button("Read original ↗", str(row.get("link", "#")), use_container_width=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

with tab_feed:
    display_rows(articles.sort_values("published_at", ascending=False, na_position="last") if not articles.empty else articles)

with tab_watchlist:
    try:
        saved = sb.table("saved_articles").select("article_id, saved_at, articles(*)").execute()
        saved_rows = []
        for row in (saved.data or []):
            article = row.get("articles")
            if article:
                saved_rows.append(article)
        display_rows(pd.DataFrame(saved_rows))
    except Exception as e:
        st.warning("Watchlist could not be loaded. Check the saved_articles table and its foreign-key relationship.")
        st.caption(str(e))

with tab_info:
    st.subheader("Movie discovery setup")
    st.markdown("""
- Add `TMDB_API_KEY` for movie and series posters and discovery lists.
- Add `OMDB_API_KEY` for actual IMDb ratings. Without it, ratings are shown as unavailable rather than inventing scores.
- Trending this month uses titles released in the last 30 days, ranked by TMDB popularity. All-time favourites uses high vote counts and ratings; it is not an official IMDb chart.
- Movie tiles open a Google search for the title in a new tab.
""")
    st.subheader("What 'realtime' means in this version")
    st.markdown("""
- When you click **Fetch latest headlines**, the app checks multiple public RSS search feeds and stores/updates entries in Supabase.
- Supabase provides a persistent shared database across app restarts and deployments.
- This is near-real-time on refresh, not a guaranteed live news wire. Google News and publishers determine when items appear.
- The app does not run a permanent background job on every visitor page load. A scheduled worker can be added later, but free hosting and quotas must be respected.
- Article headlines, summaries, and links are displayed; the full article remains on the publisher's site.
    """)
    st.subheader("Privacy note")
    st.write("This starter version has a shared watchlist for all app visitors. Before making it public for multiple users, add Supabase Auth and user_id-based row-level security so bookmarks are private.")
    st.subheader("Troubleshooting")
    st.markdown("""
1. If tables are missing, run `schema.sql` in Supabase SQL Editor.
2. In Streamlit Community Cloud, add `SUPABASE_URL` and `SUPABASE_KEY` under App settings → Secrets.
3. Use a Supabase publishable/anon key with appropriate RLS policies. Never put the `service_role` key in a public app or commit secrets to GitHub.
4. If feeds fail temporarily, try again later; public RSS availability can vary.
    """)

st.divider()
st.markdown("<div style='text-align:center;color:#827d76;font-size:.75rem;padding:24px 0 4px'>CINEPULSE · INDIAN CINEMA, IN FOCUS · PUBLIC FEEDS, ORIGINAL PUBLISHER LINKS</div>", unsafe_allow_html=True)
