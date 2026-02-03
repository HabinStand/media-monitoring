"""
Streamlit Web App - Carbon Measures RSS Feed Collector
No terminal required - runs in your browser!
"""

import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import time
import json
from dateutil import parser as date_parser

# Page configuration
st.set_page_config(
    page_title="Carbon Measures RSS Collector",
    page_icon="📰",
    layout="wide"
)

# Initialize session state for keywords
if 'custom_keywords' not in st.session_state:
    st.session_state['custom_keywords'] = [
        "carbon measures",
        "scope 3 emissions",
        "exxon scope 3",
        "greenhouse gas protocol scope 3",
        "Amy Bracchio",
        "Karthik Ramanna"
    ]

# Default keywords (for reference)
DEFAULT_KEYWORDS = [
    "carbon measures",
    "scope 3 emissions",
    "exxon scope 3",
    "greenhouse gas protocol scope 3",
    "Amy Bracchio",
    "Karthik Ramanna"
]


@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_google_news_rss(keyword):
    """Fetch articles from Google News RSS for a specific keyword"""
    articles = []
    url = f"https://news.google.com/rss/search?q={quote_plus(keyword)}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            # Parse the published date
            published_str = entry.get('published', '')
            published_date = None
            
            try:
                if published_str:
                    published_date = date_parser.parse(published_str)
            except:
                pass
            
            article = {
                'Keyword': keyword,
                'Title': entry.get('title', ''),
                'URL': entry.get('link', ''),
                'Published': published_str,
                'Published_Date': published_date,
                'Source': entry.get('source', {}).get('title', 'Unknown'),
                'Description': entry.get('summary', '')
            }
            articles.append(article)
    except Exception as e:
        st.error(f"Error fetching {keyword}: {e}")
    
    return articles


def collect_all_feeds(progress_bar, status_text, keywords):
    """Collect RSS feeds for all keywords"""
    all_articles = []
    total_keywords = len(keywords)
    
    for i, keyword in enumerate(keywords):
        status_text.text(f"Fetching articles for: {keyword}")
        articles = fetch_google_news_rss(keyword)
        all_articles.extend(articles)
        progress_bar.progress((i + 1) / total_keywords)
        time.sleep(1)  # Be nice to Google's servers
    
    # Remove duplicates based on URL
    df = pd.DataFrame(all_articles)
    if not df.empty:
        df = df.drop_duplicates(subset=['URL'], keep='first')
    
    return df


def main():
    # Header
    st.title("📰 Carbon Measures RSS Feed Collector")
    st.markdown("Collect and analyze media coverage about Carbon Measures and related topics")
    
    # Sidebar
    st.sidebar.header("⚙️ Keyword Management")
    
    # Add new keyword
    with st.sidebar.expander("➕ Add New Keyword", expanded=False):
        new_keyword = st.text_input("Enter keyword to monitor:", key="new_keyword_input")
        if st.button("Add Keyword"):
            if new_keyword and new_keyword.strip():
                if new_keyword.strip() not in st.session_state['custom_keywords']:
                    st.session_state['custom_keywords'].append(new_keyword.strip())
                    st.success(f"Added: {new_keyword}")
                    st.rerun()
                else:
                    st.warning("Keyword already exists!")
            else:
                st.warning("Please enter a keyword")
    
    # Display and manage current keywords
    st.sidebar.subheader("📋 Current Keywords")
    st.sidebar.text(f"Total: {len(st.session_state['custom_keywords'])}")
    
    # Show keywords with delete buttons
    keywords_to_remove = []
    for i, keyword in enumerate(st.session_state['custom_keywords']):
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            st.text(f"{i+1}. {keyword}")
        with col2:
            if st.button("🗑️", key=f"delete_{i}"):
                keywords_to_remove.append(keyword)
    
    # Remove keywords
    if keywords_to_remove:
        for keyword in keywords_to_remove:
            st.session_state['custom_keywords'].remove(keyword)
        st.rerun()
    
    # Reset to defaults
    if st.sidebar.button("🔄 Reset to Default Keywords"):
        st.session_state['custom_keywords'] = DEFAULT_KEYWORDS.copy()
        st.rerun()
    
    st.sidebar.divider()
    
    st.sidebar.header("ℹ️ About")
    st.sidebar.info("""
    This app collects RSS feeds from Google News for your custom keywords.
    
    **How to use:**
    1. Add or remove keywords in the sidebar
    2. Collect articles using your keywords
    3. Filter and download results
    """)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📥 Collect Feeds", "🔍 Search & Filter", "ℹ️ Instructions"])
    
    with tab1:
        st.header("📥 Collect RSS Feeds")
        
        # Show current keywords being monitored
        st.subheader("Current Keywords")
        st.write(f"Monitoring **{len(st.session_state['custom_keywords'])}** keywords:")
        
        # Display keywords in a nice format
        keyword_cols = st.columns(3)
        for i, keyword in enumerate(st.session_state['custom_keywords']):
            with keyword_cols[i % 3]:
                st.markdown(f"✓ {keyword}")
        
        st.divider()
        
        if len(st.session_state['custom_keywords']) == 0:
            st.warning("⚠️ No keywords configured. Please add keywords in the sidebar.")
        else:
            st.markdown("Click the button below to fetch the latest articles from Google News")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                collect_button = st.button("🚀 Collect Articles", type="primary", use_container_width=True)
            
            if collect_button:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("Collecting RSS feeds..."):
                    df = collect_all_feeds(progress_bar, status_text, st.session_state['custom_keywords'])
                
                progress_bar.empty()
                status_text.empty()
            
            if df.empty:
                st.warning("No articles found. Try again later.")
            else:
                # Store in session state
                st.session_state['articles_df'] = df
                st.session_state['collection_time'] = datetime.now()
                st.session_state['keywords_used'] = st.session_state['custom_keywords'].copy()
                
                st.success(f"✅ Collection complete! Found {len(df)} unique articles")
                
                # Display summary
                st.subheader("📊 Summary")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Articles", len(df))
                with col2:
                    st.metric("Keywords Searched", len(st.session_state['custom_keywords']))
                with col3:
                    st.metric("Unique Sources", df['Source'].nunique())
                
                # Articles by keyword
                st.subheader("Articles by Keyword")
                keyword_counts = df['Keyword'].value_counts()
                st.bar_chart(keyword_counts)
                
                # Display articles
                st.subheader("📰 Recent Articles")
                display_df = df[['Title', 'Source', 'Keyword', 'Published', 'URL']].head(20)
                
                # Make URLs clickable
                st.dataframe(
                    display_df,
                    column_config={
                        "URL": st.column_config.LinkColumn("URL"),
                        "Title": st.column_config.TextColumn("Title", width="large"),
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Download buttons
                st.subheader("💾 Download Data")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📄 Download CSV",
                        data=csv,
                        file_name=f"rss_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    json_str = df.to_json(orient='records', indent=2)
                    st.download_button(
                        label="📋 Download JSON",
                        data=json_str,
                        file_name=f"rss_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
    
    with tab2:
        st.header("Search & Filter Collected Data")
        
        if 'articles_df' not in st.session_state:
            st.info("👈 Please collect articles first using the 'Collect Feeds' tab")
        else:
            df = st.session_state['articles_df']
            collection_time = st.session_state['collection_time']
            
            st.text(f"Last collected: {collection_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Search
            search_term = st.text_input("🔍 Search in titles and descriptions", "")
            
            # Date filter
            st.subheader("📅 Date Filter")
            col1, col2 = st.columns(2)
            
            with col1:
                # Calculate min and max dates from data
                valid_dates = df[df['Published_Date'].notna()]['Published_Date']
                if len(valid_dates) > 0:
                    # Convert to datetime and remove timezone for date picker
                    valid_dates_dt = pd.to_datetime(valid_dates).dt.tz_localize(None)
                    min_date = valid_dates_dt.min().date()
                    max_date = valid_dates_dt.max().date()
                else:
                    min_date = datetime.now().date() - timedelta(days=30)
                    max_date = datetime.now().date()
                
                start_date = st.date_input(
                    "From date",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date
                )
            
            with col2:
                end_date = st.date_input(
                    "To date",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
            
            # Quick date filters
            st.write("Quick filters:")
            col1, col2, col3, col4 = st.columns(4)
            
            # Note: These buttons will update the date inputs in the next rerun
            quick_filter = None
            
            with col1:
                if st.button("Today"):
                    quick_filter = "today"
            
            with col2:
                if st.button("Last 7 days"):
                    quick_filter = "7days"
            
            with col3:
                if st.button("Last 30 days"):
                    quick_filter = "30days"
            
            with col4:
                if st.button("All time"):
                    quick_filter = "all"
            
            # Apply quick filter
            if quick_filter == "today":
                start_date = datetime.now().date()
                end_date = datetime.now().date()
            elif quick_filter == "7days":
                start_date = (datetime.now() - timedelta(days=7)).date()
                end_date = datetime.now().date()
            elif quick_filter == "30days":
                start_date = (datetime.now() - timedelta(days=30)).date()
                end_date = datetime.now().date()
            elif quick_filter == "all":
                if len(valid_dates) > 0:
                    valid_dates_dt = pd.to_datetime(valid_dates).dt.tz_localize(None)
                    start_date = valid_dates_dt.min().date()
                    end_date = valid_dates_dt.max().date()
            
            st.divider()
            
            # Keyword filter
            selected_keywords = st.multiselect(
                "Filter by keyword",
                options=df['Keyword'].unique().tolist(),
                default=df['Keyword'].unique().tolist()
            )
            
            # Source filter
            selected_sources = st.multiselect(
                "Filter by source",
                options=sorted(df['Source'].unique().tolist()),
                default=[]
            )
            
            # Apply filters
            filtered_df = df.copy()
            
            # Date filter
            if 'Published_Date' in filtered_df.columns:
                # Convert start and end dates to datetime for comparison
                start_datetime = pd.Timestamp(start_date)
                end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                
                # Filter by date, keeping articles without dates
                date_mask = filtered_df['Published_Date'].isna()
                if filtered_df['Published_Date'].notna().any():
                    # Remove timezone info for comparison if present
                    filtered_df['Published_Date_Compare'] = pd.to_datetime(filtered_df['Published_Date']).dt.tz_localize(None)
                    date_mask = date_mask | (
                        (filtered_df['Published_Date_Compare'] >= start_datetime) & 
                        (filtered_df['Published_Date_Compare'] <= end_datetime)
                    )
                filtered_df = filtered_df[date_mask]
            
            if search_term:
                mask = (filtered_df['Title'].str.contains(search_term, case=False, na=False) | 
                       filtered_df['Description'].str.contains(search_term, case=False, na=False))
                filtered_df = filtered_df[mask]
            
            if selected_keywords:
                filtered_df = filtered_df[filtered_df['Keyword'].isin(selected_keywords)]
            
            if selected_sources:
                filtered_df = filtered_df[filtered_df['Source'].isin(selected_sources)]
            
            # Display results
            st.subheader(f"Results: {len(filtered_df)} articles")
            
            if len(filtered_df) > 0:
                display_df = filtered_df[['Title', 'Source', 'Keyword', 'Published', 'URL']]
                
                st.dataframe(
                    display_df,
                    column_config={
                        "URL": st.column_config.LinkColumn("URL"),
                        "Title": st.column_config.TextColumn("Title", width="large"),
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Download filtered results
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download Filtered Results (CSV)",
                    data=csv,
                    file_name=f"filtered_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No articles match your filters")
    
    with tab3:
        st.header("📖 How to Use This App")
        
        st.markdown("""
        ### Step-by-Step Instructions
        
        #### 1. Manage Your Keywords
        - In the **sidebar**, click **"➕ Add New Keyword"**
        - Type your keyword and click **"Add Keyword"**
        - Remove keywords by clicking the 🗑️ button next to them
        - Click **"🔄 Reset to Default Keywords"** to restore original keywords
        
        #### 2. Collect Articles
        - Go to the **"📥 Collect Feeds"** tab
        - Review the keywords that will be searched
        - Click the **"🚀 Collect Articles"** button
        - Wait 10-30 seconds while articles are fetched
        - View the results and summary
        
        #### 3. Download Your Data
        After collection, you can download the data in two formats:
        - **CSV**: Open in Excel or Google Sheets
        - **JSON**: For programming or further processing
        
        #### 4. Search & Filter
        - Go to the **"🔍 Search & Filter"** tab
        - Use the date range picker or quick filter buttons
        - Search for specific terms
        - Filter by keyword or news source
        - Download filtered results
        
        ### Default Keywords
        The app comes pre-configured with these keywords:
        1. "carbon measures"
        2. "scope 3 emissions"
        3. "exxon scope 3"
        4. "greenhouse gas protocol scope 3"
        5. "Amy Bracchio"
        6. "Karthik Ramanna"
        
        ### Example Keywords You Can Add
        - Company names: "ExxonMobil", "BASF", "BlackRock"
        - Topics: "carbon accounting", "net zero", "climate risk"
        - People: Names of executives, researchers, policymakers
        - Regulations: "CBAM", "SEC climate rules", "ISSB standards"
        - Technologies: "carbon capture", "renewable energy"
        
        ### Tips
        - **Be specific**: "Tesla carbon footprint" vs just "Tesla"
        - **Use quotes** (in your search): Exact phrase matching
        - **Combine terms**: "carbon AND accounting" finds both words
        - **Monitor competitors**: Add competitor company names
        - **Track events**: Add conference names, policy initiatives
        
        ### Data Freshness
        - Articles are fetched from Google News RSS feeds
        - Data is cached for 1 hour to avoid excessive requests
        - Click "Collect Articles" again to refresh
        - Keywords are saved during your session only
        
        ### About This Tool
        This RSS collector helps you monitor media coverage across any topics you choose.
        It's perfect for:
        - Media monitoring and PR tracking
        - Competitive intelligence
        - Industry research
        - Policy and regulatory tracking
        - ESG and sustainability reporting
        
        ### Frequently Asked Questions
        
        **Q: How many keywords can I add?**  
        A: As many as you want, but more keywords = longer collection time (1-2 seconds per keyword).
        
        **Q: Are my keywords saved permanently?**  
        A: No, keywords reset when you refresh the page. Download your data regularly.
        
        **Q: Can I collect historical articles?**  
        A: Google News RSS typically shows recent articles (last 24-48 hours).
        
        **Q: Why are some results not relevant?**  
        A: RSS feeds use basic text matching. Use more specific keywords to improve results.
        
        **Q: Can I schedule automatic collection?**  
        A: Not in this version, but you can manually collect daily/weekly and build a database in Excel.
        """)
        
        st.divider()
        
        st.subheader("🎯 Quick Start Example")
        st.markdown("""
        **Scenario**: You want to monitor "hydrogen fuel" and "carbon credits"
        
        1. **Add keywords**: Go to sidebar → Add "hydrogen fuel" → Add "carbon credits"
        2. **Collect**: Click "🚀 Collect Articles"
        3. **Filter**: Go to "Search & Filter" → Select "Last 7 days"
        4. **Download**: Click "📄 Download CSV"
        5. **Repeat**: Come back tomorrow and collect again
        """)


if __name__ == "__main__":
    main()
