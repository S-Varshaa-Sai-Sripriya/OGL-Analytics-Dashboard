import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Page configuration
st.set_page_config(
    page_title="OGL Dashboard",
    page_icon="🐺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SBU Colors
SBU_RED = "#990000"
SBU_DARK_RED = "#660000"
SBU_GRAY = "#5E5E5E"
SBU_WHITE = "#FFFFFF"

# Custom CSS with SBU colors
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #f8f8f8;
    }}
    .main-header {{
        background: linear-gradient(135deg, {SBU_RED} 0%, {SBU_DARK_RED} 100%);
        padding: 25px 40px;
        border-radius: 12px;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(153, 0, 0, 0.3);
    }}
    .main-title {{
        color: {SBU_WHITE};
        font-size: 2.5em;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        letter-spacing: 2px;
    }}
    div[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {SBU_RED} 0%, {SBU_DARK_RED} 100%);
    }}
    div[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: {SBU_WHITE};
    }}
    div[data-testid="stSidebar"] .stButton > button {{
        background-color: {SBU_WHITE};
        color: {SBU_RED};
        border: none;
        font-weight: bold;
    }}
    div[data-testid="stSidebar"] .stButton > button:hover {{
        background-color: #f0f0f0;
        color: {SBU_DARK_RED};
    }}
    .stButton > button[kind="primary"] {{
        background-color: {SBU_RED};
        color: white;
        border: none;
        font-weight: bold;
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: {SBU_DARK_RED};
    }}
    h3 {{
        color: {SBU_RED};
    }}
    </style>
""", unsafe_allow_html=True)

# Header - Clean banner
st.markdown("""
    <div class="main-header">
        <h1 class="main-title">🐺 OGL Dashboard</h1>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'df' not in st.session_state:
    st.session_state.df = None
if 'sheets' not in st.session_state:
    st.session_state.sheets = []
if 'current_sheet' not in st.session_state:
    st.session_state.current_sheet = None
if 'file_loaded' not in st.session_state:
    st.session_state.file_loaded = False
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
if 'generated' not in st.session_state:
    st.session_state.generated = False
if 'plot_df' not in st.session_state:
    st.session_state.plot_df = None
if 'fig' not in st.session_state:
    st.session_state.fig = None
if 'selected_filters' not in st.session_state:
    st.session_state.selected_filters = []
if 'filtered_line_items' not in st.session_state:
    st.session_state.filtered_line_items = None

def clean_dataframe(df):
    """Clean dataframe - handle unnamed columns and empty rows"""
    df = df.dropna(how='all')
    
    unnamed_cols = [col for col in df.columns if 'Unnamed' in str(col)]
    if len(unnamed_cols) > len(df.columns) / 2 and len(df) > 0:
        new_header = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True)
        df.columns = [str(col).strip() if pd.notna(col) else f'Column_{i}' 
                      for i, col in enumerate(new_header)]
    
    valid_cols = [col for col in df.columns if 'Unnamed' not in str(col) and str(col).strip()]
    if valid_cols:
        df = df[valid_cols]
    
    df.columns = [str(col).strip() for col in df.columns]
    df = df.dropna(axis=1, how='all')
    
    return df

def load_file(file_path_or_buffer, is_uploaded=False):
    """Load Excel or CSV file"""
    try:
        if is_uploaded:
            file_name = file_path_or_buffer.name
        else:
            file_name = file_path_or_buffer
            
        if file_name.endswith('.csv'):
            df = pd.read_csv(file_path_or_buffer)
            df = clean_dataframe(df)
            return {'Sheet1': df}, ['Sheet1']
        else:
            xl = pd.ExcelFile(file_path_or_buffer)
            sheets = xl.sheet_names
            data = {}
            for sheet in sheets:
                df = pd.read_excel(xl, sheet_name=sheet)
                data[sheet] = clean_dataframe(df)
            return data, sheets
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None, []

def find_status_column(columns):
    """Find SBU developer status column by common name patterns."""
    normalized_map = {str(col).strip().lower(): col for col in columns}
    preferred_names = [
        "sbu developer status",
        "developer status",
        "sbu status",
        "status"
    ]

    for name in preferred_names:
        if name in normalized_map:
            return normalized_map[name]

    for norm_name, original_name in normalized_map.items():
        if "status" in norm_name and "developer" in norm_name:
            return original_name

    return None

def build_status_color_map(status_values):
    """Return a deterministic color map for status values."""
    color_map = {}
    fallback_colors = ['#1f77b4', '#9467bd', '#ff7f0e', '#17becf', '#8c564b', '#7f7f7f']
    fallback_idx = 0

    for status in status_values:
        status_text = str(status).strip().lower()
        if status_text == "pass":
            color_map[status] = '#2E8B57'
        elif status_text == "fail":
            color_map[status] = '#D62728'
        else:
            color_map[status] = fallback_colors[fallback_idx % len(fallback_colors)]
            fallback_idx += 1

    return color_map

def build_series_color_map(series_values):
    """Color map for combined labels like 'Custom - Pass' based on trailing status token."""
    color_map = {}
    fallback_colors = ['#1f77b4', '#9467bd', '#ff7f0e', '#17becf', '#8c564b', '#7f7f7f']
    fallback_idx = 0

    for value in series_values:
        value_text = str(value).strip()
        status_text = value_text.split(' - ')[-1].strip().lower()
        if status_text == 'pass':
            color_map[value] = '#2E8B57'
        elif status_text == 'fail':
            color_map[value] = '#D62728'
        else:
            color_map[value] = fallback_colors[fallback_idx % len(fallback_colors)]
            fallback_idx += 1

    return color_map

# Sidebar for file operations
with st.sidebar:
    st.markdown("### 📁 Data Source")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Upload Excel/CSV File",
        type=['xlsx', 'xls', 'csv'],
        help="Upload your data file",
        key="file_uploader"
    )
    
    st.markdown("---")
    
    default_file_path = os.path.join("Dataset", "OGL_Consolidated.xlsx")
    if st.button("📂 Load Default File", use_container_width=True, key="load_default"):
        if os.path.exists(default_file_path):
            with st.spinner("Loading..."):
                data, sheets = load_file(default_file_path)
                if data:
                    st.session_state.data = data
                    st.session_state.sheets = sheets
                    st.session_state.current_sheet = sheets[0]
                    st.session_state.df = data[sheets[0]]
                    st.session_state.file_loaded = True
                    st.session_state.file_name = "OGL_Consolidated.xlsx"
                    st.session_state.generated = False
        else:
            st.error("Default file not found!")
    
    if uploaded_file is not None:
        if st.session_state.file_name != uploaded_file.name:
            with st.spinner("Loading..."):
                data, sheets = load_file(uploaded_file, is_uploaded=True)
                if data:
                    st.session_state.data = data
                    st.session_state.sheets = sheets
                    st.session_state.current_sheet = sheets[0]
                    st.session_state.df = data[sheets[0]]
                    st.session_state.file_loaded = True
                    st.session_state.file_name = uploaded_file.name
                    st.session_state.generated = False
    
    if st.session_state.file_loaded:
        st.markdown("---")
        st.success(f"✅ {st.session_state.file_name}")

# Main content area
if st.session_state.file_loaded and st.session_state.df is not None:
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### ⚙️ Configuration")
        
        # Sheet selection
        sheet_index = st.session_state.sheets.index(st.session_state.current_sheet) if st.session_state.current_sheet in st.session_state.sheets else 0
        selected_sheet = st.selectbox(
            "📋 Select Sheet",
            options=st.session_state.sheets,
            index=sheet_index,
            key="sheet_select"
        )
        
        if selected_sheet != st.session_state.current_sheet:
            st.session_state.current_sheet = selected_sheet
            st.session_state.df = st.session_state.data[selected_sheet]
            st.session_state.generated = False
        
        df = st.session_state.df
        columns = [col for col in df.columns.tolist() if col and str(col).strip()]
        
        if not columns:
            st.warning("No valid columns found.")
            columns = df.columns.tolist()

        status_col = find_status_column(columns)
        
        st.markdown("---")
        
        # Graph type selection - Added Stacked Bar
        graph_types = {
            "📊 Bar Chart": "bar",
            "📊 Stacked Bar Chart": "stacked_bar",
            "📊 Horizontal Bar": "barh",
            "📊 Stacked Horizontal Bar": "stacked_barh",
            "🥧 Pie Chart": "pie",
            "🎯 Donut Chart": "donut",
            "📈 Line Chart": "line",
            "🔵 Scatter Plot": "scatter",
            "📉 Area Chart": "area"
        }
        
        selected_graph = st.selectbox(
            "📈 Graph Type",
            options=list(graph_types.keys()),
            key="graph_type"
        )
        graph_type = graph_types[selected_graph]
        
        st.markdown("---")
        st.markdown("### 🔢 Filter Fields")
        
        # Number of filters selection (1-5)
        num_filters = st.slider(
            "How many fields to filter/group by?",
            min_value=1,
            max_value=5,
            value=1,
            key="num_filters",
            help="Select 1-5 columns to group your data"
        )
        
        st.markdown("---")
        
        # Dynamic filter dropdowns based on selected number
        selected_filters = []
        filter_labels = ["Primary (X-Axis)", "Secondary (Color/Stack)", "Third", "Fourth", "Fifth"]
        
        for i in range(num_filters):
            # Exclude already selected columns from options
            available_cols = [c for c in columns if c not in selected_filters]
            if available_cols:
                default_idx = min(i, len(available_cols) - 1)
                selected_col = st.selectbox(
                    f"🔹 {filter_labels[i]} Field",
                    options=available_cols,
                    index=default_idx,
                    key=f"filter_{i}"
                )
                selected_filters.append(selected_col)
        
        st.session_state.selected_filters = selected_filters
        
        # Show selected filters summary
        if len(selected_filters) > 1:
            filter_chain = " → ".join(selected_filters)
            st.caption(f"📊 Grouping: **{filter_chain}**")

        if status_col:
            st.caption(f"✅ Status split column detected: **{status_col}**")
        else:
            st.warning("⚠️ Could not detect `SBU Developer Status` column. Status split will be skipped.")

        st.markdown("---")
        st.markdown("### 🔍 Additional Filters")
        
        # Top X filter with SLIDER
        use_top_x = st.checkbox("🏆 Filter Top X Records", value=False, key="use_top_x")
        top_x = 10
        if use_top_x:
            max_val = min(len(df), 100)
            top_x = st.slider("Number of top records", min_value=1, max_value=max_val, value=min(10, max_val), key="top_x_slider")
        
        # Show line items checkbox
        show_line_items = st.checkbox("📋 Show Corresponding Line Items", value=False, key="show_items")
        
        st.markdown("---")
        
        # Generate Graph button
        if st.button("🚀 Generate Graph", use_container_width=True, type="primary", key="generate"):
            st.session_state.generated = True
    
    with col2:
        # Data preview
        st.markdown("### 📋 Data Preview")
        st.caption(f"Sheet: **{st.session_state.current_sheet}** | Rows: **{len(df)}** | Columns: **{len(columns)}**")
        st.dataframe(df.head(5), use_container_width=True, height=150)
        
        st.markdown("---")
        
        if st.session_state.generated and len(selected_filters) > 0:
            st.markdown("### 📊 Visualization")
            
            plot_df = df.copy()
            
            try:
                fig = None
                agg_df = None
                
                # Define colors
                colors = ['#990000', '#CC3333', '#FF6666', '#B22222', '#8B0000', '#CD5C5C', '#DC143C', '#A52A2A', '#BC8F8F', '#F08080', 
                          '#800000', '#A52A2A', '#CD5C5C', '#E9967A', '#FA8072', '#F08080', '#FFA07A', '#FF7F50', '#FF6347', '#FF4500']
                
                primary_col = selected_filters[0]
                # Normalize selected columns used for grouping
                group_cols = selected_filters.copy()
                if status_col and status_col not in group_cols:
                    group_cols.append(status_col)

                for col in group_cols:
                    plot_df[col] = (
                        plot_df[col]
                        .astype(object)
                        .where(plot_df[col].notna(), 'Unknown')
                        .astype(str)
                        .str.strip()
                        .replace('', 'Unknown')
                    )

                agg_df = plot_df.groupby(group_cols, dropna=False).size().reset_index(name='Count')

                # Apply Top X based on primary column totals
                if use_top_x:
                    top_primary = (
                        agg_df.groupby(primary_col)['Count']
                        .sum()
                        .sort_values(ascending=False)
                        .head(top_x)
                        .index
                        .tolist()
                    )
                    agg_df = agg_df[agg_df[primary_col].isin(top_primary)]
                    plot_df = plot_df[plot_df[primary_col].isin(top_primary)]

                # Build stacked/group legend label using selected fields after primary
                stack_parts = selected_filters[1:]
                if status_col and status_col not in stack_parts:
                    stack_parts.append(status_col)

                if stack_parts:
                    agg_df['Stack Series'] = agg_df[stack_parts].astype(str).agg(' - '.join, axis=1)
                    color_col = 'Stack Series'
                elif status_col and status_col in agg_df.columns:
                    color_col = status_col
                else:
                    color_col = None

                agg_df = agg_df.sort_values('Count', ascending=False)
                st.session_state.filtered_line_items = plot_df.copy()
                
                # Create chart based on type
                is_stacked = graph_type in ['stacked_bar', 'stacked_barh']
                is_pie = graph_type in ['pie', 'donut']
                if color_col and color_col in agg_df.columns:
                    series_values = sorted(agg_df[color_col].unique().tolist())
                    series_color_map = build_series_color_map(series_values)
                elif status_col and status_col in agg_df.columns:
                    status_values = sorted(agg_df[status_col].unique().tolist())
                    series_color_map = build_status_color_map(status_values)
                else:
                    series_color_map = None
                
                if agg_df is not None and not agg_df.empty and is_pie:
                    if color_col and color_col in agg_df.columns:
                        agg_df['Slice'] = agg_df[primary_col].astype(str) + ' | ' + agg_df[color_col].astype(str)
                    else:
                        agg_df['Slice'] = agg_df[primary_col].astype(str)

                    if graph_type == "pie":
                        fig = px.pie(
                            agg_df,
                            names='Slice',
                            values='Count',
                            color=color_col if color_col in agg_df.columns else None,
                            title=f"Distribution by {' → '.join(selected_filters)}",
                            color_discrete_map=series_color_map if series_color_map else None,
                            color_discrete_sequence=colors if not series_color_map else None
                        )
                    else:  # donut
                        fig = px.pie(
                            agg_df,
                            names='Slice',
                            values='Count',
                            color=color_col if color_col in agg_df.columns else None,
                            title=f"Distribution by {' → '.join(selected_filters)}",
                            hole=0.4,
                            color_discrete_map=series_color_map if series_color_map else None,
                            color_discrete_sequence=colors if not series_color_map else None
                        )
                
                elif agg_df is not None and not agg_df.empty and graph_type in ["bar", "stacked_bar"]:
                    fig = px.bar(
                        agg_df,
                        x=primary_col,
                        y='Count',
                        color=color_col if color_col in agg_df.columns else None,
                        title=f"Count by {' → '.join(selected_filters)}" + (f" split by {status_col}" if status_col else ""),
                        color_discrete_map=series_color_map if series_color_map else None,
                        color_discrete_sequence=colors if not series_color_map else None,
                        barmode='stack' if is_stacked else 'group'
                    )
                
                elif agg_df is not None and not agg_df.empty and graph_type in ["barh", "stacked_barh"]:
                    fig = px.bar(
                        agg_df,
                        x='Count',
                        y=primary_col,
                        color=color_col if color_col in agg_df.columns else None,
                        title=f"Count by {' → '.join(selected_filters)}" + (f" split by {status_col}" if status_col else ""),
                        orientation='h',
                        color_discrete_map=series_color_map if series_color_map else None,
                        color_discrete_sequence=colors if not series_color_map else None,
                        barmode='stack' if is_stacked else 'group'
                    )
                
                elif agg_df is not None and not agg_df.empty and graph_type == "line":
                    fig = px.line(
                        agg_df,
                        x=primary_col,
                        y='Count',
                        color=color_col if color_col in agg_df.columns else None,
                        title=f"Count by {' → '.join(selected_filters)}" + (f" split by {status_col}" if status_col else ""),
                        markers=True,
                        color_discrete_map=series_color_map if series_color_map else None,
                        color_discrete_sequence=[SBU_RED] if not series_color_map else None
                    )
                
                elif agg_df is not None and not agg_df.empty and graph_type == "scatter":
                    fig = px.scatter(
                        agg_df,
                        x=primary_col,
                        y='Count',
                        color=color_col if color_col in agg_df.columns else None,
                        title=f"Count by {' → '.join(selected_filters)}" + (f" split by {status_col}" if status_col else ""),
                        color_discrete_map=series_color_map if series_color_map else None,
                        color_discrete_sequence=[SBU_RED] if not series_color_map else None
                    )
                    fig.update_traces(marker=dict(size=12))
                
                elif agg_df is not None and not agg_df.empty and graph_type == "area":
                    fig = px.area(
                        agg_df,
                        x=primary_col,
                        y='Count',
                        color=color_col if color_col in agg_df.columns else None,
                        title=f"Count by {' → '.join(selected_filters)}" + (f" split by {status_col}" if status_col else ""),
                        color_discrete_map=series_color_map if series_color_map else None,
                        color_discrete_sequence=[SBU_RED] if not series_color_map else None
                    )
                
                st.session_state.plot_df = agg_df
                
                # Display the chart
                if fig:
                    fig.update_layout(
                        font=dict(family="Arial", size=14, color='black'),
                        title_font=dict(size=22, color=SBU_RED),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        height=500,
                        legend=dict(
                            font=dict(color='black', size=12),
                            bgcolor='rgba(255,255,255,0.9)'
                        ),
                        xaxis=dict(
                            tickfont=dict(color='black', size=11),
                            title_font=dict(color='black', size=14),
                            tickangle=-45
                        ),
                        yaxis=dict(
                            tickfont=dict(color='black', size=12),
                            title_font=dict(color='black', size=14)
                        )
                    )
                    # Ensure pie chart labels are visible
                    if is_pie:
                        fig.update_traces(
                            textfont=dict(color='black', size=12),
                            outsidetextfont=dict(color='black', size=12)
                        )
                    st.plotly_chart(fig, use_container_width=True)
                    st.session_state.fig = fig
                    
                    # Show aggregated data table
                    st.markdown("#### 📊 Aggregated Data")
                    st.dataframe(agg_df, use_container_width=True, height=200)
                elif agg_df is not None and agg_df.empty:
                    st.warning("No chart data available after applying filters.")
                        
            except Exception as e:
                st.error(f"Error creating graph: {str(e)}")
                st.info("💡 Try selecting different columns.")
        
        # Show corresponding line items - WORKS INDEPENDENTLY
        if show_line_items and st.session_state.generated and st.session_state.plot_df is not None and len(selected_filters) > 0:
            st.markdown("---")
            st.markdown("### 📋 Corresponding Line Items")

            if st.session_state.filtered_line_items is not None:
                line_items_df = st.session_state.filtered_line_items.copy()
                st.caption(f"Showing **{len(line_items_df)}** records matching the active filters")
                st.dataframe(line_items_df, use_container_width=True, height=300)

                csv = line_items_df.to_csv(index=False)
                st.download_button("📥 Download Line Items as CSV", data=csv, file_name="line_items.csv", mime="text/csv")

else:
    st.markdown("""
        <div style="text-align: center; padding: 60px; background: white; border-radius: 15px; margin: 30px auto; max-width: 700px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <h2 style="color: #990000;">Welcome to OGL Dashboard! 🐺</h2>
            <p style="font-size: 1.2em; color: #5E5E5E;">Your interactive data visualization playground</p>
            <div style="background: #f8f8f8; padding: 20px; border-radius: 10px; margin-top: 20px;">
                <p><strong>👈 Get Started:</strong></p>
                <p>1. Upload an Excel or CSV file in the sidebar</p>
                <p>2. Or click <strong>"Load Default File"</strong></p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div style="background:white;padding:20px;border-radius:10px;text-align:center;border-top:4px solid {SBU_RED};"><h4 style="color:{SBU_RED};">📊 Charts</h4><p>Bar, Stacked Bar, Pie & more</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div style="background:white;padding:20px;border-radius:10px;text-align:center;border-top:4px solid {SBU_RED};"><h4 style="color:{SBU_RED};">🔍 Multi-Filters</h4><p>Up to 5 filter fields</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div style="background:white;padding:20px;border-radius:10px;text-align:center;border-top:4px solid {SBU_RED};"><h4 style="color:{SBU_RED};">📁 Multi-Sheet</h4><p>Excel multi-sheet support</p></div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown(f'<div style="text-align:center;color:{SBU_GRAY};"><p>🐺 <strong>OGL Dashboard</strong> | Stony Brook University | Go Seawolves! 🔴</p></div>', unsafe_allow_html=True)
