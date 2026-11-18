# Salih Bishara Page

My personal news page for AI Usage for Engineering Design. The homepage introduces me and links to the latest stock market, motorsport, and automotive industry stories. Each topic page lists up to six articles with links to their publishers.

## Preview on your computer

With Python 3.9 or newer, run these commands from the repository folder.

```sh
python3 scripts/build.py --offline
python3 -m http.server 8000 --directory dist
```

Open [the local homepage](http://localhost:8000/). You can also open `dist/index.html` directly. The saved stories, photographs, and fonts are included.

## Edit and refresh

- Edit the introduction or replace a publisher’s RSS feed in [data/site.json](data/site.json).
- Update the homepage layout in [templates/home.html](templates/home.html) and the styling in [assets/style.css](assets/style.css).
- Run `python3 scripts/build.py` to fetch new articles and rebuild all four pages. A failed feed keeps its last successful stories and refresh date in `data/news.json`.
- Run `python3 -m unittest discover -s scripts` to check the feed fallback.

## GitHub Pages

Use **Settings → Pages → Source → GitHub Actions**. The [publication workflow](.github/workflows/pages.yml) builds on pushes to `main` and refreshes the news every day at 06:17 UTC. To refresh it immediately, choose **Actions → Refresh news and publish → Run workflow**.

## Sources and photography

Article headlines and excerpts link to [CNBC Market Insider](https://www.cnbc.com/market-insider/), [Motorsport.com](https://www.motorsport.com/), and [WardsAuto](https://www.wardsauto.com/).

Topic photographs illustrate the sections. The Monza photograph is by [Isaac Maffeis](https://unsplash.com/photos/8ViEbuWhfGo), the market display by [chilldude](https://unsplash.com/photos/R7YrpkXpMwU), the race at Spa by [Raphael Rousseau](https://unsplash.com/photos/dRiyN7o5ydY), and the assembly line by [Hyundai Motor Group](https://unsplash.com/photos/mPreSMYIr1E). All four are available under the [Unsplash License](https://unsplash.com/license).

Barlow Condensed and DM Sans are distributed under the SIL Open Font License. Their licenses are included in [assets/fonts](assets/fonts).
