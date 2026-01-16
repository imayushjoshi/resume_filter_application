import streamlit as st
import pandas as pd
import ast

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Millennium Talent Scout",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #1E3A8A; font-weight: 700; }
    .metric-card { background-color: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 5px solid #1E3A8A; }
    .stExpander { border: 1px solid #E5E7EB; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA LOADING & CLEANING ---
@st.cache_data
def load_and_clean_data():
    try:
        df = pd.read_csv("output.csv")
        
        # Strip whitespace from column names just in case
        df.columns = [c.strip() for c in df.columns]
        
        # Map your specific column names to variables for easy reference
        # Note: Handling the typo 'candiate' from your CSV header
        col_map = {
            'sectors': 'primary sectors the candiate has worked in',
            'geography': 'Geographies the candidate has worked in',
            'companies': 'Companies that the candidate has worked in',
            'internships': 'Companies that the candidate has interned in',
            'experience': 'Total Years of Experience(Excluding Internships)',
            'strategy': 'Investment Approaches',
            'name': 'Name',
            'email': 'Email',
            'phone': 'Phone number'
        }
        
        # List columns to parse
        list_cols = [col_map['sectors'], col_map['geography'], col_map['companies'], col_map['internships']]
        
        # --- Smart List Parser ---
        def parse_list_field(x):
            if pd.isna(x) or x == "" or str(x).lower() in ["nan", "none"]:
                return []
            
            x_str = str(x).strip()
            
            # Case A: Python list string "['Item A', 'Item B']"
            if x_str.startswith('[') and x_str.endswith(']'):
                try:
                    parsed = ast.literal_eval(x_str)
                    if isinstance(parsed, list):
                        # Filter out 'None' strings if they appear in the list
                        return [str(i).strip() for i in parsed if str(i).lower() != 'none']
                except:
                    pass
            
            # Case B: Comma separated string "Item A, Item B"
            if ',' in x_str:
                return [i.strip() for i in x_str.split(',') if i.strip().lower() != 'none']
            
            # Case C: Single item
            return [x_str] if x_str.lower() != 'none' else []

        # Apply parsing
        for col in list_cols:
            if col in df.columns:
                df[col] = df[col].apply(parse_list_field)

        # Fill missing text fields
        df[col_map['name']] = df[col_map['name']].fillna("Unknown Candidate")
        df[col_map['email']] = df[col_map['email']].fillna("Not Provided")
        df[col_map['strategy']] = df[col_map['strategy']].fillna("Unclassified")
        df[col_map['experience']] = df[col_map['experience']].fillna(0)
        
        return df, col_map
        
    except FileNotFoundError:
        st.error("❌ Error: 'output.csv' not found. Please upload it to the same folder.")
        return pd.DataFrame(), {}

df, cols = load_and_clean_data()

if df.empty:
    st.stop()

# --- 3. SIDEBAR FILTERS ---
with st.sidebar:
    st.header("🔍 Search Filters")
    
    # 1. Strategy
    if cols['strategy'] in df.columns:
        strategies = sorted(df[cols['strategy']].unique().tolist())
        selected_strategies = st.multiselect("Investment Approach", strategies, default=strategies)
    else:
        selected_strategies = []

    # 2. Geography
    if cols['geography'] in df.columns:
        all_geos = sorted(list(set([item for sublist in df[cols['geography']] for item in sublist])))
        selected_geos = st.multiselect("Geographic Focus", all_geos, default=all_geos)
    else:
        selected_geos = []

    # 3. Sectors
    if cols['sectors'] in df.columns:
        all_sectors = sorted(list(set([item for sublist in df[cols['sectors']] for item in sublist])))
        selected_sectors = st.multiselect("Sectors", all_sectors, default=all_sectors)
    else:
        selected_sectors = []
    
    # 4. Experience Slider
    if cols['experience'] in df.columns:
        min_exp = int(df[cols['experience']].min())
        max_exp = int(df[cols['experience']].max())
        # Handle case where min == max
        if min_exp == max_exp:
            max_exp += 1
        exp_range = st.slider("Years Experience", min_exp, max_exp, (min_exp, max_exp))
    else:
        exp_range = (0, 20)

    st.divider()
    st.caption("Rationale hidden from view.")

# --- 4. FILTERING LOGIC ---
filtered_df = df.copy()

# Strategy
if selected_strategies:
    filtered_df = filtered_df[filtered_df[cols['strategy']].isin(selected_strategies)]

# Experience
if cols['experience'] in df.columns:
    filtered_df = filtered_df[
        (filtered_df[cols['experience']] >= exp_range[0]) & 
        (filtered_df[cols['experience']] <= exp_range[1])
    ]

# Geography (Overlap check)
if selected_geos:
    filtered_df = filtered_df[filtered_df[cols['geography']].apply(
        lambda x: bool(set(x) & set(selected_geos))
    )]

# Sector (Overlap check)
if selected_sectors:
    filtered_df = filtered_df[filtered_df[cols['sectors']].apply(
        lambda x: bool(set(x) & set(selected_sectors))
    )]

# --- 5. DASHBOARD UI ---
st.markdown('<p class="main-header">Millennium Talent Platform</p>', unsafe_allow_html=True)

# Metrics
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

# Visualization Section
if not filtered_df.empty:
    import plotly.express as px
    
    tab1, tab2 = st.tabs(["📊 Sector & Strategy", "🌍 Geography"])
    
    with tab1:
        col_a, col_b = st.columns(2)
        
        # Sector Bar Chart
        with col_a:
            sector_counts = filtered_df.explode(cols['sectors'])[cols['sectors']].value_counts().reset_index()
            sector_counts.columns = ['Sector', 'Count']
            fig_sec = px.bar(sector_counts.head(8), x='Count', y='Sector', orientation='h', title="Top Sectors", color='Count')
            st.plotly_chart(fig_sec, use_container_width=True)
            
        # Strategy Pie
        with col_b:
            fig_pie = px.pie(filtered_df, names=cols['strategy'], title="Strategy Distribution", hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        # Geography Bar Chart
        geo_counts = filtered_df.explode(cols['geography'])[cols['geography']].value_counts().reset_index()
        geo_counts.columns = ['Region', 'Count']
        fig_geo = px.bar(geo_counts, x='Region', y='Count', title="Candidate Locations", color='Region')
        st.plotly_chart(fig_geo, use_container_width=True)

# Candidate List
st.subheader("📋 Candidate Profiles")

if not filtered_df.empty:
    for _, row in filtered_df.iterrows():
        # Clean display values
        name = row[cols['name']]
        strategy = row[cols['strategy']]
        exp_years = row[cols['experience']]
        
        # Create Expander Header
        header = f"**{name}** | {strategy} | {exp_years} Years Exp"
        
        with st.expander(header):
            col_x, col_y = st.columns([1, 2])
            
            with col_x:
                st.markdown(f"**📧 Email:** {row[cols['email']]}")
                st.markdown(f"**📱 Phone:** {row[cols['phone']]}")
                
                # Geography Tags
                locs = ", ".join(row[cols['geography']])
                st.info(f"📍 **Locations:** {locs}")
                
            with col_y:
                # Sectors
                sectors = ", ".join(row[cols['sectors']])
                st.markdown(f"**🏭 Sectors:** {sectors}")
                
                # Companies
                companies = ", ".join(row[cols['companies']])
                st.markdown(f"**🏢 Work History:** {companies}")
                
                # Internships (if any)
                internships = row[cols['internships']]
                if internships:
                    st.markdown(f"**🎓 Internships:** {', '.join(internships)}")
                
                # NOTE: Rationale sections have been intentionally removed as requested.

else:
    st.info("No candidates match your filters.")