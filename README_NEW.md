# RSS Feed Collector with Custom Keywords

A Streamlit web app for collecting and analyzing RSS feeds from Google News with customizable keywords.

## Features

✅ **Custom Keywords** - Add, remove, and manage your own keywords  
✅ **Date Filtering** - Filter articles by date range with quick filter buttons  
✅ **Search & Filter** - Full-text search with keyword and source filters  
✅ **Export Data** - Download results as CSV or JSON  
✅ **No Database Required** - Simple, lightweight, browser-based  
✅ **Free to Deploy** - Works on Streamlit Cloud free tier  

## Quick Start

### Deploy to Streamlit Cloud

1. Fork or clone this repository
2. Sign up at [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub account
4. Deploy this repository
5. Done! Your app is live

### Files Needed

- `streamlit_app.py` - Main application
- `requirements.txt` - Python dependencies

## How to Use

1. **Add Keywords** - Use the sidebar to add/remove keywords
2. **Collect Articles** - Click "🚀 Collect Articles" to fetch RSS feeds
3. **Filter Results** - Use date range, search, and filters
4. **Download Data** - Export as CSV for Excel or JSON for analysis

## Example Use Cases

- Media monitoring and PR tracking
- Competitive intelligence
- Industry research and trends
- Policy and regulatory tracking
- ESG and sustainability reporting

## Default Keywords

The app comes with these default keywords (related to Carbon Measures):
- "carbon measures"
- "scope 3 emissions"
- "exxon scope 3"
- "greenhouse gas protocol scope 3"
- "Amy Bracchio"
- "Karthik Ramanna"

You can modify, add, or remove these keywords directly in the app!

## Technical Details

- **Framework**: Streamlit
- **Data Source**: Google News RSS feeds
- **Cache**: 1 hour (to avoid rate limiting)
- **Export Formats**: CSV, JSON

## Requirements

```
streamlit
feedparser
pandas
python-dateutil
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

Visit `http://localhost:8501` in your browser.

## License

Free to use and modify.

## Support

For issues or questions, please open an issue in this repository.
