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
import re

# Page configuration
st.set_page_config(
    page_title="RSS Feed Collector",
    page_icon="📰",
    layout="wide"
)

# Initialize session state for keywords
if 'custom_keywords' not in st.session_state:
    st.session_state['custom_keywords'] = []


def categorize_source(source_name):
    """
    Categorize news sources into different types
    Returns: category name
    """
    source_lower = source_name.lower()
    
    # Mainstream Media
    mainstream = [
        'cnn', 'bbc', 'reuters', 'associated press', 'ap news', 'bloomberg',
        'financial times', 'wall street journal', 'wsj', 'new york times', 'nyt',
        'washington post', 'guardian', 'telegraph', 'fox news', 'nbc', 'abc',
        'cbs', 'npr', 'pbs', 'usa today', 'time', 'newsweek', 'economist',
        'forbes', 'fortune', 'business insider', 'cnbc', 'marketwatch', 'axios'
    ]
    
    # Trade Press / Industry Publications
    trade_press = [
        'techcrunch', 'the verge', 'wired', 'ars technica', 'zdnet', 'cnet',
        'venturebeat', 'recode', 'engadget', 'gizmodo', 'mashable', 'greentech',
        'renewable energy world', 'energy storage news', 'utility dive', 'power',
        'pv magazine', 'solar power world', 'wind power monthly', 'cleantechnica',
        'electrek', 'green car reports', 'inside evs', 'automotive news',
        'trade', 'industry week', 'manufacturing', 'chemical', 'engineering'
    ]
    
    # Blogs and Independent Media
    blogs = [
        'medium', 'substack', 'blog', 'blogger', 'wordpress', 'tumblr',
        'ghost', 'writefreely', 'newsletter', 'independent', 'personal site'
    ]
    
    # Government and Academic
    government_academic = [
        '.gov', 'government', 'department of', 'ministry of', 'agency',
        'university', 'college', 'institute', 'research', 'academic',
        '.edu', 'journal', 'nature', 'science', 'pnas', 'arxiv'
    ]
    
    # NGOs and Think Tanks
    ngo_thinktank = [
        'greenpeace', 'wwf', 'nrdc', 'sierra club', 'friends of the earth',
        'brookings', 'cato', 'heritage', 'cfr', 'carnegie', 'rand',
        'center for', 'institute for', 'foundation', 'council on'
    ]
    
    # Local and Regional News
    local_regional = [
        'tribune', 'gazette', 'herald', 'times', 'post', 'news', 'daily',
        'chronicle', 'journal', 'observer', 'examiner', 'courier', 'press',
        'local', 'regional', 'community', 'county', 'city'
    ]
    
    # Check each category
    for term in mainstream:
        if term in source_lower:
            return "Mainstream Media"
    
    for term in trade_press:
        if term in source_lower:
            return "Trade Press"
    
    for term in government_academic:
        if term in source_lower:
            return "Government/Academic"
    
    for term in ngo_thinktank:
        if term in source_lower:
            return "NGO/Think Tank"
    
    for term in blogs:
        if term in source_lower:
            return "Blogs/Independent"
    
    for term in local_regional:
        if term in source_lower:
            return "Local/Regional"
    
    # Default category
    return "Other"


def parse_boolean_search(search_term):
    """
    Parse boolean search into Google News format
    Supports: AND, OR, NOT operators
    Examples:
    - "climate AND policy" → "climate policy"
    - "tesla OR spacex" → "tesla OR spacex"  
    - "AI NOT crypto" → "AI -crypto"
    """
    # Replace NOT with - (Google's exclude operator)
    search_term = search_term.replace(' NOT ', ' -')
    # AND is implicit in Google, but we keep it for clarity
    search_term = search_term.replace(' AND ', ' ')
    # OR stays as is (Google supports OR)
    return search_term


@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_google_news_rss(keyword):
    """Fetch articles from Google News RSS for a specific keyword"""
    articles = []
    # Parse boolean operators
    parsed_keyword = parse_boolean_search(keyword)
    url = f"https://news.google.com/rss/search?q={quote_plus(parsed_keyword)}&hl=en-US&gl=US&ceid=US:en"
    
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
            
            source_name = entry.get('source', {}).get('title', 'Unknown')
            
            article = {
                'Keyword': keyword,
                'Title': entry.get('title', ''),
                'URL': entry.get('link', ''),
                'Published': published_str,
                'Published_Date': published_date,
                'Source': source_name,
                'Source_Category': categorize_source(source_name),
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
    st.markdown("Collect and analyze RSS feeds from Google News with custom keywords and boolean search")
    
    # Sidebar
    st.sidebar.header("⚙️ Keyword Management")
    
    # Add new keyword
    with st.sidebar.expander("➕ Add New Keyword", expanded=False):
        st.markdown("""
        **Boolean Search Operators:**
        - `AND` - both terms must appear (e.g., `climate AND policy`)
        - `OR` - either term can appear (e.g., `solar OR wind`)
        - `NOT` - exclude term (e.g., `EV NOT Tesla`)
        
        You can combine operators: `(climate OR environment) AND policy NOT Trump`
        """)
        new_keyword = st.text_input("Enter keyword to monitor:", key="new_keyword_input", 
                                    placeholder="e.g., climate AND policy")
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
    This app collects RSS feeds from Google News for your custom keywords with boolean search support.
    
    **How to use:**
    1. Add keywords (with boolean operators) in the sidebar
    2. Collect articles using your keywords
    3. Filter by source category and download results
    
    **Boolean Examples:**
    - `Tesla AND production`
    - `solar OR wind`
    - `climate NOT politics`
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
            - Simple: `Tesla`, `Microsoft`
            - Boolean AND: `Tesla AND production`
            - Boolean OR: `solar OR wind OR hydro`
            - Boolean NOT: `climate NOT politics`
            - Complex: `(EV OR electric vehicle) AND battery NOT Tesla`
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
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Articles", len(df))
                    with col2:
                        st.metric("Keywords Searched", len(st.session_state['custom_keywords']))
                    with col3:
                        st.metric("Unique Sources", df['Source'].nunique())
                    with col4:
                        st.metric("Source Categories", df['Source_Category'].nunique())
                    
                    # Articles by keyword
                    st.subheader("Articles by Keyword")
                    keyword_counts = df['Keyword'].value_counts()
                    st.bar_chart(keyword_counts)
                    
                    # Articles by source category
                    st.subheader("Articles by Source Category")
                    category_counts = df['Source_Category'].value_counts()
                    st.bar_chart(category_counts)
                    
                    # Show breakdown of categories
                    st.subheader("📂 Source Category Breakdown")
                    for category in sorted(df['Source_Category'].unique()):
                        with st.expander(f"{category} ({len(df[df['Source_Category'] == category])} articles)"):
                            sources_in_category = df[df['Source_Category'] == category]['Source'].value_counts()
                            st.write(sources_in_category)
                    
                    # Display articles
                    st.subheader("📰 Recent Articles")
                    display_df = df[['Title', 'Source', 'Source_Category', 'Keyword', 'Published', 'URL']].head(20)
                    
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
            
            # Source category filter
            selected_categories = st.multiselect(
                "Filter by source category",
                options=sorted(df['Source_Category'].unique().tolist()),
                default=[]
            )
            
            # Source filter
            selected_sources = st.multiselect(
                "Filter by specific source",
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
            
            if selected_categories:
                filtered_df = filtered_df[filtered_df['Source_Category'].isin(selected_categories)]
            
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
            if selected_categories:
                active_filters.append(f"Categories: {', '.join(selected_categories)}")
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
                    if selected_categories:
                        temp_df = temp_df[temp_df['Source_Category'].isin(selected_categories)]
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
                
                # Show category breakdown of results
                st.subheader("📂 Results by Category")
                category_counts = filtered_df['Source_Category'].value_counts()
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.bar_chart(category_counts)
                with col2:
                    st.dataframe(category_counts.reset_index().rename(columns={'index': 'Category', 'Source_Category': 'Count'}), 
                               hide_index=True)
                
                display_df = filtered_df[['Title', 'Source', 'Source_Category', 'Keyword', 'Published', 'URL']]
                
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
        
        #### 1. Manage Your Keywords (with Boolean Search!)
        - In the **sidebar**, click **"➕ Add New Keyword"**
        - Type your keyword with optional boolean operators:
          - `climate AND policy` - both terms must appear
          - `solar OR wind` - either term can appear
          - `EV NOT Tesla` - exclude Tesla from EV results
          - `(climate OR environment) AND policy` - combine operators
        - Click **"Add Keyword"**
        - Remove keywords by clicking the 🗑️ button next to them
        - Use **"🗑️ Clear All Keywords"** to delete all keywords at once
        
        #### 2. Collect Articles
        - Go to the **"📥 Collect Feeds"** tab
        - Review the keywords that will be searched
        - Click the **"🚀 Collect Articles"** button
        - Wait 10-30 seconds while articles are fetched
        - View the results and summary with source categorization
        
        #### 3. Download Your Data
        After collection, you can download the data in two formats:
        - **CSV**: Open in Excel or Google Sheets (includes Source_Category column)
        - **JSON**: For programming or further processing
        
        #### 4. Search & Filter
        - Go to the **"🔍 Search & Filter"** tab
        - Use the date range picker or quick filter buttons
        - Search for specific terms
        - Filter by keyword, source category, or specific news source
        - Download filtered results
        
        ### Source Categories Explained
        
        Articles are automatically categorized into:
        
        - **Mainstream Media**: CNN, BBC, Reuters, NYT, WSJ, etc.
        - **Trade Press**: TechCrunch, Wired, CleanTechnica, industry publications
        - **Blogs/Independent**: Medium, Substack, personal blogs
        - **Government/Academic**: .gov sites, universities, research journals
        - **NGO/Think Tank**: Greenpeace, Brookings, RAND, etc.
        - **Local/Regional**: Local newspapers and regional news outlets
        - **Other**: Sources that don't fit above categories
        
        ### Boolean Search Examples
        
        **Simple Boolean:**
        - `Tesla AND production` - both words must appear
        - `solar OR wind` - either word can appear
        - `climate NOT politics` - exclude politics
        
        **Advanced Boolean:**
        - `(EV OR "electric vehicle") AND battery` - parentheses for grouping
        - `renewable energy NOT oil` - exclude specific topics
        - `Microsoft AND (Azure OR cloud)` - multiple OR conditions
        - `climate policy AND (EU OR Europe) NOT Brexit` - complex queries
        
        ### Example Keywords You Can Add
        
        **Simple keywords:**
        - "Apple", "Google", "Tesla", "Microsoft"
        - "climate change", "artificial intelligence"
        
        **Boolean keywords:**
        - "Tesla AND (production OR delivery)"
        - "climate AND policy NOT Trump"
        - "(solar OR wind) AND energy storage"
        - "Microsoft AND AI NOT gaming"
        - "EV OR electric vehicle OR battery electric"
        
        ### Tips for Better Results
        - **Use boolean AND** for precise results: "climate AND Africa"
        - **Use boolean OR** for comprehensive coverage: "solar OR photovoltaic OR PV"
        - **Use boolean NOT** to exclude: "Apple NOT iPhone" (just the company news)
        - **Combine operators**: "(climate OR environment) AND policy AND (Africa OR Kenya)"
        - **Filter by category** after collection to focus on specific source types
        - **Track mainstream vs trade press** separately for different perspectives
        
        ### Data Freshness
        - Articles are fetched from Google News RSS feeds
        - Data is cached for 1 hour to avoid excessive requests
        - Click "Collect Articles" again to refresh
        - Keywords are saved during your session only
        - Download your data regularly to build a historical database
        
        ### About This Tool
        This RSS collector helps you monitor media coverage with advanced search and categorization.
        Perfect for:
        - Media monitoring and PR tracking
        - Competitive intelligence
        - Market research across different source types
        - Industry trend analysis
        - Policy and regulatory tracking
        - ESG and sustainability reporting
        - Academic research
        - Investment research
        
        ### Frequently Asked Questions
        
        **Q: How do boolean operators work?**  
        A: They work like Google search. AND narrows results, OR expands them, NOT excludes terms.
        
        **Q: Can I see which sources are in each category?**  
        A: Yes! After collection, expand the "Source Category Breakdown" section.
        
        **Q: How many keywords can I add?**  
        A: As many as you want! More keywords = longer collection time (1-2 seconds per keyword).
        
        **Q: Are my keywords saved permanently?**  
        A: No, keywords reset when you refresh the page. Keep a list saved elsewhere.
        
        **Q: Can I collect historical articles?**  
        A: Google News RSS typically shows recent articles (last 24-48 hours). Collect regularly.
        
        **Q: Why are some sources categorized as "Other"?**  
        A: The categorization uses pattern matching. Uncommon sources may not match any category.
        
        **Q: Can I customize the source categories?**  
        A: Not in the UI, but you can modify the `categorize_source()` function in the code.
        """)
        
        st.divider()
        
        st.subheader("🎯 Quick Start Example")
        st.markdown("""
        **Scenario**: You want to monitor mainstream media coverage of electric vehicles, excluding Tesla
        
        1. **Add keyword with boolean**: 
           - Sidebar → "➕ Add New Keyword"
           - Type: `(EV OR "electric vehicle") NOT Tesla`
           - Add Keyword
        
        2. **Collect**: Click "🚀 Collect Articles"
        
        3. **Filter by category**: 
           - Go to "Search & Filter"
           - Select "Mainstream Media" in category filter
        
        4. **Download**: Click "📄 Download Filtered Results (CSV)"
        
        5. **Analyze**: Open in Excel and see what mainstream outlets are saying
        
        That's it! You now have targeted media coverage data.
        """)


if __name__ == "__main__":
    main()
