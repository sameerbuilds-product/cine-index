# CinePulse — Indian cinema discovery + news

A Streamlit app with a cinema discovery section and a separate Indian cinema news feed. Supabase stores news articles and saved stories.

## Features
- Discover movies and series in poster tiles.
- Trending this week, trending this month, and all-time favourites views.
- Filter by Movies, Web series, or Both; filter by Indian language.
- Actual IMDb ratings on posters when an OMDb API key is configured. Ratings are never fabricated; unavailable ratings show as a dash.
- Clicking a poster opens a Google search for that movie or series in a new tab.
- Separate cinema news feed sourced from public Google News RSS feeds.
- Supabase-backed article storage and saved-story list.

## Deploy
1. Upload `app.py`, `requirements.txt`, `schema.sql`, and `README.md` to the GitHub repository connected to Streamlit Community Cloud.
2. In Streamlit Community Cloud, open the app's Settings → Secrets and configure:

```toml
SUPABASE_URL = "https://YOUR-PROJECT-ID.supabase.co"
SUPABASE_KEY = "YOUR-SUPABASE-PUBLISHABLE-OR-ANON-KEY"
TMDB_API_KEY = "YOUR-TMDB-API-KEY"
OMDB_API_KEY = "YOUR-OMDB-API-KEY"
```

3. Save secrets and reboot/redeploy the app.
4. If Supabase tables are not yet created, run `schema.sql` in Supabase Dashboard → SQL Editor.

## API keys
- TMDB: request an API key from https://www.themoviedb.org/settings/api. Used for discovery lists and poster images.
- OMDb: request a key from https://www.omdbapi.com/apikey.aspx. Used to retrieve IMDb ratings. Free key limits apply.
- Supabase: use a publishable key or legacy anon key for the public app. Never expose a `service_role` key.

## How rankings work
- **Trending this week:** TMDB's weekly trending endpoint, filtered toward Indian-origin/language titles when available.
- **Trending this month:** Indian-language/country discovery for titles released within the last 30 days, sorted by TMDB popularity.
- **All-time favourites:** discovery sorted by high TMDB user rating and a minimum vote count. This is a curated discovery ranking, not an official IMDb all-time chart.
- The badge shows the IMDb score returned by OMDb. It is not the TMDB score.

TMDB data and images are subject to TMDB terms and attribution requirements. IMDb ratings are sourced via OMDb and are subject to its quotas/terms. Public feeds and API results may update with delays.

## Notes
- Supabase demo schema uses shared saved-story rows. Before a public multi-user launch, add Supabase Auth and user-specific row-level security.
- News refresh happens on initial load or when the user clicks Fetch latest headlines; this app does not run a permanent background worker.
