import streamlit as st
import pandas as pd
import ast
import plotly.express as px

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Millennium Talent Scout",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #1E3A8A; font-weight: 700; }
    .metric-card { background-color: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 5px solid #1E3A8A; }
    
    .history-item { 
        padding: 12px; 
        margin-bottom: 8px; 
        background-color: #f1f5f9; 
        color: #333333 !important;
        border-radius: 6px; 
        border-left: 4px solid #1E3A8A;
        font-size: 14px;
        line-height: 1.5;
    }
    
    .intern-item {
        padding: 10px; 
        margin-bottom: 5px; 
        background-color: #fff1f2; 
        color: #333333 !important;
        border-radius: 6px; 
        border-left: 4px solid #e11d48;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA LOADING & CLEANING ---
@st.cache_data
def load_and_clean_data():
    try:
        df = pd.read_csv("Milennium Case Study Output.csv")
        df.columns = [c.strip() for c in df.columns]
        
        col_map = {
            'name': 'Name',
            'email': 'Email',
            'phone': 'Phone number',
            'geography': 'Geographies the candidate has worked in',
            'strategy': 'Investment Approaches',
            'rationale_strategy': 'Rationale for Investment Approaches classification',
            'companies': 'Companies that the candidate has worked in',
            'sectors': 'Sectors that the candidate has worked in',
            'experience': 'Total Years of Experience(Excluding Internships)',
            'work_history': 'Work History',
            'internship_history': 'Internship History'
        }
        
        def parse_field(x):
            if pd.isna(x) or x == "" or str(x).lower() in ["nan", "none"]:
                return []
            
            x_str = str(x).strip()
            
            # Python List Format
            if x_str.startswith('[') and x_str.endswith(']'):
                try:
                    parsed = ast.literal_eval(x_str)
                    if isinstance(parsed, list):
                        clean_list = []
                        for i in parsed:
                            item = str(i).strip()
                            if item.lower() not in ['none', 'n/a', 'nan', '']:
                                clean_list.append(item)
                        return clean_list
                except:
                    pass
            
            # Comma Separated Format
            if ',' in x_str:
                return [i.strip() for i in x_str.split(',') if i.strip().lower() not in ['none', 'n/a']]
            
            # Single Item
            return [x_str] if x_str.lower() not in ['none', 'n/a'] else []

        list_cols = [
            col_map['geography'], 
            col_map['sectors'], 
            col_map['companies'],
            col_map['work_history'],
            col_map['internship_history']
        ]
        
        for col in list_cols:
            if col in df.columns:
                df[col] = df[col].apply(parse_field)
        
        df[col_map['experience']] = pd.to_numeric(df[col_map['experience']], errors='coerce').fillna(0)
        df[col_map['name']] = df[col_map['name']].fillna("Unknown Candidate")
        df[col_map['strategy']] = df[col_map['strategy']].fillna("Unclassified")
        df[col_map['rationale_strategy']] = df[col_map['rationale_strategy']].fillna("No rationale provided.")
        
        return df, col_map
        
    except FileNotFoundError:
        st.error("Error: 'output.csv' not found.")
        return pd.DataFrame(), {}

df, cols = load_and_clean_data()

if df.empty:
    st.stop()

# --- 3. SIDEBAR FILTERS ---
with st.sidebar:
    st.header("🔍 Search Filters")
    
    # 1. Geographic Markets (Default Empty)
    if cols['geography'] in df.columns:
        all_geos = sorted(list(set([item for sublist in df[cols['geography']] for item in sublist])))
        selected_geos = st.multiselect("Geographic Markets", all_geos, default=[]) 
    else:
        selected_geos = []

    # 2. Sectors (Default Empty)
    if cols['sectors'] in df.columns:
        all_sectors = sorted(list(set([item for sublist in df[cols['sectors']] for item in sublist])))
        selected_sectors = st.multiselect("Sectors", all_sectors, default=[])
    else:
        selected_sectors = []

    # 3. Investment Approach (Default Empty)
    if cols['strategy'] in df.columns:
        strategies = sorted(df[cols['strategy']].astype(str).unique().tolist())
        selected_strategies = st.multiselect("Investment Approach", strategies, default=[])
    else:
        selected_strategies = []
    
    # 4. Years of Experience (Default Full Range)
    if cols['experience'] in df.columns:
        min_exp = int(df[cols['experience']].min())
        max_exp = int(df[cols['experience']].max())
        if min_exp == max_exp: max_exp += 1
        exp_range = st.slider("Years of Experience", min_exp, max_exp, (min_exp, max_exp))
    else:
        exp_range = (0, 20)

# --- 4. FILTERING LOGIC ---
filtered_df = df.copy()

# Filter: Strategy (Only apply if user selected something)
if selected_strategies:
    filtered_df = filtered_df[filtered_df[cols['strategy']].isin(selected_strategies)]

# Filter: Experience (Always applies)
if cols['experience'] in df.columns:
    filtered_df = filtered_df[
        (filtered_df[cols['experience']] >= exp_range[0]) & 
        (filtered_df[cols['experience']] <= exp_range[1])
    ]

# Filter: Geography (Only apply if user selected something)
if selected_geos:
    filtered_df = filtered_df[filtered_df[cols['geography']].apply(
        lambda x: bool(set(x) & set(selected_geos))
    )]

# Filter: Sector (Only apply if user selected something)
if selected_sectors:
    filtered_df = filtered_df[filtered_df[cols['sectors']].apply(
        lambda x: bool(set(x) & set(selected_sectors))
    )]

# --- 5. DASHBOARD MAIN AREA ---
st.markdown('<p class="main-header">Millennium Talent Platform</p>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Candidates Found", len(filtered_df))

if not filtered_df.empty:
    avg_yrs = round(filtered_df[cols['experience']].mean(), 1)
    quant_count = len(filtered_df[filtered_df[cols['strategy']] == 'Quantitative'])
else:
    avg_yrs = 0
    quant_count = 0

c2.metric("Avg. Experience", f"{avg_yrs} Yrs")
c3.metric("Quant Profiles", quant_count)

st.divider()

if not filtered_df.empty:
    tab1, tab2 = st.tabs(["📊 Sector Distribution", "🌍 Geographic Presence"])
    
    with tab1:
        sector_counts = filtered_df.explode(cols['sectors'])[cols['sectors']].value_counts().reset_index()
        sector_counts.columns = ['Sector', 'Count']
        fig_sec = px.bar(sector_counts.head(10), x='Count', y='Sector', orientation='h', title="Top Sectors", color='Count')
        st.plotly_chart(fig_sec, use_container_width=True)

    with tab2:
        geo_counts = filtered_df.explode(cols['geography'])[cols['geography']].value_counts().reset_index()
        geo_counts.columns = ['Region', 'Count']
        fig_geo = px.bar(geo_counts, x='Region', y='Count', title="Geographic Focus", color='Region')
        st.plotly_chart(fig_geo, use_container_width=True)

# --- 6. CANDIDATE PROFILES ---
st.subheader("📋 Candidate Profiles")

if not filtered_df.empty:
    for _, row in filtered_df.iterrows():
        name = row[cols['name']]
        strategy = row[cols['strategy']]
        exp = row[cols['experience']]
        email = row.get(cols['email'], 'N/A')
        phone = row.get(cols['phone'], 'N/A')
        rationale = row.get(cols['rationale_strategy'], 'No rationale provided.')
        
        with st.expander(f"**{name}** | {strategy} | {exp} Years Exp"):
            col_left, col_right = st.columns([1, 2])
            
            with col_left:
                st.markdown("#### 👤 Contact & Focus")
                st.markdown(f"**📧 Email:** {email}")
                st.markdown(f"**📱 Phone:** {phone}")
                
                st.markdown("---")
                st.markdown("**🌍 Geographic Markets:**")
                for geo in row[cols['geography']]:
                    st.caption(f"📍 {geo}")

                st.markdown("**🏭 Sectors:**")
                for sec in row[cols['sectors']]:
                    st.caption(f"🔧 {sec}")
                
                st.markdown("---")
                st.markdown("**💡 Classification Rationale:**")
                st.info(rationale)
            
            with col_right:
                st.markdown("#### 🏢 Work History")
                work_items = row[cols['work_history']]
                if work_items:
                    for item in work_items:
                        st.markdown(f'<div class="history-item">{item}</div>', unsafe_allow_html=True)
                else:
                    st.info("No work history available.")
                
                intern_items = row[cols['internship_history']]
                if intern_items:
                    st.markdown("#### 🎓 Internship History")
                    for item in intern_items:
                        st.markdown(f'<div class="intern-item">{item}</div>', unsafe_allow_html=True)

else:
    st.warning("No candidates match the selected filters.")