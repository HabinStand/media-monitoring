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
    page_title="RSS Feed Collector",
    page_icon="📰",
    layout="wide"
)

# Initialize session state for keywords
if 'custom_keywords' not in st.session_state:
    st.session_state['custom_keywords'] = []


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
    st.title("📰 RSS Feed Collector")
    st.markdown("Collect and analyze RSS feeds from Google News with custom keywords")
    
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
    
    # Clear all keywords
    if st.sidebar.button("🗑️ Clear All Keywords"):
        st.session_state['custom_keywords'] = []
        st.rerun()
    
    st.sidebar.divider()
    
    st.sidebar.header("ℹ️ About")
    st.sidebar.info("""
    This app collects RSS feeds from Google News for your custom keywords.
    
    **How to use:**
    1. Add keywords in the sidebar
    2. Collect articles using your keywords
    3. Filter and download results
    
    **Getting Started:**
    Click "➕ Add New Keyword" above to add your first keyword!
    """)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📥 Collect Feeds", "🔍 Search & Filter", "ℹ️ Instructions"])
    
    with tab1:
        st.header("📥 Collect RSS Feeds")
        
        # Show current keywords being monitored
        if len(st.session_state['custom_keywords']) > 0:
            st.subheader("Current Keywords")
            st.write(f"Monitoring **{len(st.session_state['custom_keywords'])}** keywords:")
            
            # Display keywords in a nice format
            keyword_cols = st.columns(3)
            for i, keyword in enumerate(st.session_state['custom_keywords']):
                with keyword_cols[i % 3]:
                    st.markdown(f"✓ {keyword}")
            
            st.divider()
        
        if len(st.session_state['custom_keywords']) == 0:
            st.info("👈 **Get Started:** Add your first keyword using the sidebar!")
            st.markdown("""
            ### How to Add Keywords:
            1. Look at the **sidebar** on the left
            2. Click **"➕ Add New Keyword"**
            3. Type your keyword (e.g., "climate change", "renewable energy")
            4. Click **"Add Keyword"**
            5. Come back here and click **"🚀 Collect Articles"**
            
            ### Example Keywords:
            - Company names: "Tesla", "Microsoft"
            - Topics: "artificial intelligence", "electric vehicles"
            - People: "Elon Musk", "your competitor's CEO"
            - Products: "ChatGPT", "iPhone 15"
            """)
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
            
            # Show total articles
            st.metric("Total Articles Collected", len(df))
            
            st.divider()
            
            # Search
            st.subheader("🔍 Text Search")
            search_term = st.text_input("Search in titles and descriptions", "", placeholder="Type keywords to search...")
            
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
            st.subheader("🏷️ Filters")
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
            st.divider()
            
            # Show search status prominently
            if search_term:
                st.success(f"🔍 **Search Active:** Showing results for '{search_term}'")
            
            st.subheader(f"📊 Results: {len(filtered_df)} articles")
            
            # Show active filters
            active_filters = []
            if search_term:
                active_filters.append(f"✓ Text search: '{search_term}'")
            if len(selected_keywords) < len(df['Keyword'].unique()):
                active_filters.append(f"Keywords: {len(selected_keywords)} selected")
            if selected_sources:
                active_filters.append(f"Sources: {len(selected_sources)} selected")
            active_filters.append(f"Date range: {start_date} to {end_date}")
            
            if active_filters:
                st.caption("Active filters: " + " • ".join(active_filters))
            
            if len(filtered_df) > 0:
                # Show search statistics if search is active
                if search_term:
                    search_matches = len(filtered_df)
                    total_before_search = len(df)
                    
                    # Apply all filters except search to see search impact
                    temp_df = df.copy()
                    if 'Published_Date' in temp_df.columns:
                        start_datetime = pd.Timestamp(start_date)
                        end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                        date_mask = temp_df['Published_Date'].isna()
                        if temp_df['Published_Date'].notna().any():
                            temp_df['Published_Date_Compare'] = pd.to_datetime(temp_df['Published_Date']).dt.tz_localize(None)
                            date_mask = date_mask | (
                                (temp_df['Published_Date_Compare'] >= start_datetime) & 
                                (temp_df['Published_Date_Compare'] <= end_datetime)
                            )
                        temp_df = temp_df[date_mask]
                    if selected_keywords:
                        temp_df = temp_df[temp_df['Keyword'].isin(selected_keywords)]
                    if selected_sources:
                        temp_df = temp_df[temp_df['Source'].isin(selected_sources)]
                    
                    articles_before_search = len(temp_df)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Articles Before Search", articles_before_search)
                    with col2:
                        st.metric("Matching Search Term", search_matches)
                    with col3:
                        match_rate = (search_matches / articles_before_search * 100) if articles_before_search > 0 else 0
                        st.metric("Match Rate", f"{match_rate:.1f}%")
                    
                    st.info(f"💡 **Search Results:** Found '{search_term}' in {search_matches} article(s)")
                
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
                if search_term:
                    st.error(f"❌ **No Results Found for '{search_term}'**")
                    st.warning("""
                    Your search term didn't match any articles. Try:
                    - Using different keywords
                    - Checking for typos
                    - Using partial words (e.g., "climat" instead of "climate change")
                    - Removing other filters to expand results
                    """)
                else:
                    st.warning("⚠️ No articles match your filters")
                    st.info("""
                    **Tips:**
                    - Try removing some filters
                    - Expand the date range
                    - Make sure keywords are selected
                    """)
    
    with tab3:
        st.header("📖 How to Use This App")
        
        st.markdown("""
        ### Step-by-Step Instructions
        
        #### 1. Manage Your Keywords
        - In the **sidebar**, click **"➕ Add New Keyword"**
        - Type your keyword and click **"Add Keyword"**
        - Remove keywords by clicking the 🗑️ button next to them
        - Use **"🗑️ Clear All Keywords"** to delete all keywords at once
        
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
        
        ### Example Keywords You Can Add
        - **Company names**: "Apple", "Google", "Tesla", "Microsoft"
        - **Topics**: "climate change", "artificial intelligence", "cryptocurrency"
        - **People**: "Elon Musk", "Tim Cook", industry leaders
        - **Products**: "iPhone", "ChatGPT", "Tesla Model 3"
        - **Regulations**: "EU AI Act", "GDPR", "carbon tax"
        - **Technologies**: "quantum computing", "5G", "solar energy"
        - **Events**: "COP28", "World Economic Forum", "Tech Summit"
        
        ### Tips for Better Results
        - **Be specific**: "Tesla production delays" vs just "Tesla"
        - **Use phrases**: Multi-word keywords work great
        - **Combine terms**: "Microsoft AND acquisition"
        - **Monitor competitors**: Add competitor names and products
        - **Track trends**: Add emerging technology or policy terms
        - **Industry terms**: Use jargon specific to your field
        
        ### Data Freshness
        - Articles are fetched from Google News RSS feeds
        - Data is cached for 1 hour to avoid excessive requests
        - Click "Collect Articles" again to refresh
        - Keywords are saved during your session only
        - Download your data regularly to build a historical database
        
        ### About This Tool
        This RSS collector helps you monitor media coverage across any topics you choose.
        Perfect for:
        - Media monitoring and PR tracking
        - Competitive intelligence
        - Market research
        - Industry trend analysis
        - Policy and regulatory tracking
        - ESG and sustainability reporting
        - Academic research
        - Investment research
        
        ### Frequently Asked Questions
        
        **Q: How many keywords can I add?**  
        A: As many as you want! But more keywords = longer collection time (1-2 seconds per keyword).
        
        **Q: Are my keywords saved permanently?**  
        A: No, keywords reset when you refresh the page. Keep a list of your keywords saved elsewhere.
        
        **Q: Can I collect historical articles?**  
        A: Google News RSS typically shows recent articles (last 24-48 hours). For history, collect regularly.
        
        **Q: Why are some results not relevant?**  
        A: RSS feeds use basic text matching. Use more specific keywords to improve results.
        
        **Q: Can I schedule automatic collection?**  
        A: Not in this version. Manually collect daily/weekly and build your database in Excel.
        
        **Q: What's the difference between CSV and JSON?**  
        A: CSV opens in Excel/Sheets. JSON is better for programming and data processing.
        """)
        
        st.divider()
        
        st.subheader("🎯 Quick Start Example")
        st.markdown("""
        **Scenario**: You want to monitor news about "electric vehicles" and "battery technology"
        
        1. **Add keywords**: 
           - Sidebar → "➕ Add New Keyword"
           - Type "electric vehicles" → Add Keyword
           - Type "battery technology" → Add Keyword
        
        2. **Collect**: Click "🚀 Collect Articles"
        
        3. **Filter**: Go to "Search & Filter" → Select "Last 7 days"
        
        4. **Download**: Click "📄 Download CSV"
        
        5. **Repeat**: Come back tomorrow and collect again to track trends
        
        That's it! You now have a database of recent news articles.
        """)


if __name__ == "__main__":
    main()
