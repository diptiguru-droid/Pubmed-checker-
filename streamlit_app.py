import streamlit as st
from Bio import Entrez
import pandas as pd
import requests

# Set your NCBI email for PubMed
Entrez.email = "your.email@example.com"

st.set_page_config(page_title="Multi-Source Research Tracker", layout="wide")

# Apply Modern Helvetica Font Styling
st.markdown("""
    <style>
    .stApp, .stApp *, [data-testid="stSidebar"] *, h1, h2, h3, h4, h5, h6, p, span, label, div {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🔬 Multi-Source Scientific & Clinical Literature Checker")
st.markdown("Search across PubMed, Europe PMC, and ClinicalTrials.gov instantly from one clean interface.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Search Parameters")

# Database Source Selector
data_source = st.sidebar.selectbox(
    "Select Database Source:",
    [
        "All Databases (Combined)",
        "PubMed (Published Literature)",
        "Europe PMC (Global Research & Preprints)",
        "ClinicalTrials.gov (Registered Studies)"
    ]
)

# Flexible search box
search_query = st.sidebar.text_input(
    "Enter Search Term:",
    value="Ubiquinol",
    help="Type any ingredient, condition, or keyword."
)

sort_option = st.sidebar.selectbox(
    "Sort Results By:",
    ["Relevance / Best Match", "Most Recent"]
)

ret_max = st.sidebar.slider("Number of results to display:", min_value=5, max_value=50, value=10, step=5)

search_button = st.sidebar.button("Run Research Search", type="primary")


# --- SEARCH FUNCTIONS ---

# 1. PubMed Fetcher
def fetch_pubmed(query, sort_by, max_results):
    sort_param = "relevance" if sort_by == "Relevance / Best Match" else "pub_date"
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort=sort_param)
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record.get("IdList", [])
        if not id_list:
            return []

        handle = Entrez.esummary(db="pubmed", id=",".join(id_list))
        summaries = Entrez.read(handle)
        handle.close()

        articles = []
        for article in summaries:
            pmid = article.get('Id')
            title = article.get('Title')
            source = article.get('Source')
            pub_date = article.get('PubDate')
            articles.append({
                "Title": title,
                "Source/Journal": source if source else "PubMed",
                "Date": pub_date if pub_date else "N/A",
                "URL": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })
        return articles
    except Exception as e:
        st.error(f"PubMed Error: {e}")
        return []

# 2. Europe PMC Fetcher
def fetch_europe_pmc(query, sort_by, max_results):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": query,
        "format": "json",
        "pageSize": max_results
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        result_list = data.get("resultList", {}).get("result", [])
        
        articles = []
        for item in result_list:
            title = item.get("title")
            journal = item.get("journalTitle", "Europe PMC Source")
            pub_year = item.get("pubYear", "N/A")
            pmid = item.get("pmid")
            source_id = pmid if pmid else item.get("id")
            url = f"https://europepmc.org/article/MED/{pmid}" if pmid else f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={source_id}"
            
            articles.append({
                "Title": title,
                "Source/Journal": journal,
                "Date": str(pub_year),
                "URL": url
            })
        return articles
    except Exception as e:
        st.error(f"Europe PMC Error: {e}")
        return []

# 3. ClinicalTrials.gov Fetcher
def fetch_clinical_trials(query, max_results):
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": query,
        "pageSize": max_results
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        studies = data.get("studies", [])
        
        results = []
        for study in studies:
            protocol = study.get("protocolSection", {})
            brief_title = protocol.get("identificationModule", {}).get("briefTitle", "No Title Available")
            nct_id = protocol.get("identificationModule", {}).get("nctId", "")
            status = protocol.get("statusModule", {}).get("overallStatus", "Unknown")
            
            results.append({
                "Title": f"[{status}] {brief_title}",
                "Source/Journal": "ClinicalTrials.gov Registry",
                "Date": status,
                "URL": f"https://clinicaltrials.gov/study/{nct_id}"
            })
        return results
    except Exception as e:
        st.error(f"ClinicalTrials Error: {e}")
        return []


# --- MAIN EXECUTION AREA ---
if search_button:
    if not search_query.strip():
        st.warning("Please enter a valid search term.")
    else:
        with st.spinner(f"Querying research databases for '{search_query}'..."):
            results = []
            if "All Databases" in data_source:
                pub_res = fetch_pubmed(search_query, sort_option, ret_max)
                eur_res = fetch_europe_pmc(search_query, sort_option, ret_max)
                trial_res = fetch_clinical_trials(search_query, ret_max)
                results = pub_res + eur_res + trial_res
            elif "PubMed" in data_source:
                results = fetch_pubmed(search_query, sort_option, ret_max)
            elif "Europe PMC" in data_source:
                results = fetch_europe_pmc(search_query, sort_option, ret_max)
            else:
                results = fetch_clinical_trials(search_query, ret_max)
            
            if results:
                st.success(f"Found {len(results)} total records for **{search_query}**.")
                st.markdown("---")
                
                for idx, item in enumerate(results, 1):
                    st.markdown(f"### {idx}. [{item['Title']}]({item['URL']})")
                    st.write(f"**Origin:** {item['Source/Journal']} | **Marker/Status:** {item['Date']}")
                    st.markdown(f"[Access Full Record ↗]({item['URL']})")
                    st.markdown("---")
            else:
                st.info("No matching records found across the selected sources. Try modifying your search terms.")
else:
    st.info("👈 Choose a database source and parameter in the sidebar, then click **Run Research Search**.")
