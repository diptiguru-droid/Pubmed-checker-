import streamlit as st
from Bio import Entrez
import pandas as pd

# Set your NCBI email (required by NCBI guidelines)
Entrez.email = "your.email@example.com"

st.set_page_config(page_title="PubMed Research Tracker", layout="wide")

st.title("🔬 PubMed Literature Checker")
st.markdown("Search government biomedical databases instantly for any ingredient, antioxidant, or health term.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Search Parameters")

# Flexible search box for any term (Ubiquinol, Tocopherols, etc.)
search_query = st.sidebar.text_input(
    "Enter Search Term:",
    value="Ubiquinol",
    help="Type any ingredient or keyword you want to search on PubMed."
)

# Dropdown for sorting (Best Match / Relevance or Most Recent)
sort_option = st.sidebar.selectbox(
    "Sort Results By:",
    ["Relevance / Best Match", "Most Recent"]
)

# Number of results to fetch
ret_max = st.sidebar.slider("Number of results to display:", min_value=5, max_value=50, value=10, step=5)

# Date filter options
date_filter = st.sidebar.selectbox(
    "Timeframe:",
    ["All Time", "Past Year", "Past 5 Years"]
)

search_button = st.sidebar.button("Run PubMed Search", type="primary")


# --- SEARCH FUNCTION ---
@st.cache_data(ttl=3600)
def fetch_pubmed_articles(query, sort_by, max_results, timeframe):
    try:
        # Map sort selection to PubMed sort parameters ('relevance' or 'pub_date')
        sort_param = "relevance" if sort_by == "Relevance / Best Match" else "pub_date"
        
        # Build date range filter if applicable
        full_query = query
        if timeframe == "Past Year":
            full_query = f"{query} AND (\"2025/01/01\"[Date - Publication] : \"3000\"[Date - Publication])"
        elif timeframe == "Past 5 Years":
            full_query = f"{query} AND (\"2021/01/01\"[Date - Publication] : \"3000\"[Date - Publication])"

        # Step 1: Search PubMed IDs
        handle = Entrez.esearch(db="pubmed", term=full_query, retmax=max_results, sort=sort_param)
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record.get("IdList", [])
        if not id_list:
            return []

        # Step 2: Fetch article summaries
        handle = Entrez.esummary(db="pubmed", id=",".join(id_list))
        summaries = Entrez.read(handle)
        handle.close()

        articles = []
        for article in summaries:
            pmid = article.get('Id')
            title = article.get('Title')
            source = article.get('Source')
            pub_date = article.get('PubDate')
            
            # Format authors list
            authors = article.get('AuthorList', [])
            authors_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "") if authors else "N/A"
            
            articles.append({
                "PMID": pmid,
                "Title": title,
                "Journal": source,
                "Publication Date": pub_date,
                "Authors": authors_str,
                "URL": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })
            
        return articles
    except Exception as e:
        st.error(f"An error occurred while connecting to PubMed: {e}")
        return []


# --- MAIN DISPLAY AREA ---
if search_button:
    if not search_query.strip():
        st.warning("Please enter a valid search term.")
    else:
        with st.spinner(f"Querying PubMed for '{search_query}'..."):
            results = fetch_pubmed_articles(search_query, sort_option, ret_max, date_filter)
            
            if results:
                st.success(f"Found {len(results)} articles for **{search_query}** (Sorted by: *{sort_option}*).")
                st.markdown("---")
                
                for idx, art in enumerate(results, 1):
                    st.markdown(f"### {idx}. [{art['Title']}]({art['URL']})")
                    st.write(f"**Journal:** {art['Journal']} | **Published:** {art['Publication Date']}")
                    st.write(f"**Authors:** {art['Authors']}")
                    st.markdown(f"[View on PubMed ↗]({art['URL']})")
                    st.markdown("---")
            else:
                st.info("No matching articles found for your criteria. Try adjusting your timeframe or search terms.")
else:
    st.info("👈 Enter your search term and parameters in the sidebar, then click **Run PubMed Search** to begin.")
