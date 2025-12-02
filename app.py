"""
Medical Website Readability Analyzer
Main Streamlit application
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
import time

# Add modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from modules import search_serpapi, scraper, classifier, readability, statistics, visualization, data_manager
from modules import data_validator, reanalysis_pipeline
import config

# Page configuration
st.set_page_config(
    page_title="Medical Readability Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'stats' not in st.session_state:
    st.session_state.stats = None
if 'figures' not in st.session_state:
    st.session_state.figures = []


def main():
    """Main application function."""
    
    # Sidebar configuration
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        st.markdown("### API Credentials")
        st.markdown("🔗 **Get your API keys:**")
        st.markdown("- [Google API Key](https://console.cloud.google.com/apis/credentials) - Enable Custom Search API")
        st.markdown("- [SerpAPI Key](https://serpapi.com/users/sign_up) - Free tier: 100 searches/month")
        
        api_key = st.text_input(
            "Google API Key (Optional)",
            value=config.GOOGLE_API_KEY,
            type="password",
            help="Get your Google Custom Search API key from Google Cloud Console"
        )
        
        search_engine_id = st.text_input(
            "Search Engine ID (Optional)",
            value=config.SEARCH_ENGINE_ID,
            help="Create a Custom Search Engine at https://cse.google.com/"
        )
        
        st.divider()
        
        st.markdown("### Analysis Options")
        num_results = st.slider(
            "Number of Results",
            min_value=10,
            max_value=100,
            value=100,
            step=10,
            help="Number of Google search results to analyze"
        )
        
        generate_figs = st.checkbox("Generate Visualizations", value=True)
        run_stats = st.checkbox("Statistical Analysis", value=True)
        
        st.divider()
        st.markdown("### About")
        st.markdown("""
        **Medical Readability Analyzer v1.0**
        
        Analyzes readability of online medical information using:
        - Gunning Fog Index (GFI)
        - SMOG Index
        - Flesch-Kincaid Grade (FKG)
        - Automated Readability Index (ARI)
        """)
    
    # Main content
    st.title("🏥 Medical Website Readability Analyzer")
    st.markdown("""
    Analyze the readability of online medical information by searching Google and evaluating 
    the first 100 results using validated readability metrics.
    """)
    
    # Mode selector
    st.header("1. Select Analysis Mode")
    analysis_mode = st.radio(
        "Choose how you want to analyze data:",
        ["🔍 New Analysis - Search Google", "📊 Re-analyze Data - Upload File"],
        horizontal=True,
        help="New Analysis: Search Google and analyze results\nRe-analyze Data: Upload a previously downloaded Excel file with your corrections"
    )
    
    st.divider()
    
    # Display appropriate interface based on mode
    if analysis_mode == "🔍 New Analysis - Search Google":
        display_new_analysis_interface(api_key, search_engine_id, num_results, generate_figs, run_stats)
    else:
        display_reanalysis_interface(generate_figs, run_stats)


def display_new_analysis_interface(api_key, search_engine_id, num_results, generate_figs, run_stats):
    """Display interface for new Google search analysis."""
    
    # Input section
    st.header("2. Enter Search Term")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input(
            "Medical Topic",
            placeholder="e.g., hypertension, diabetes, migraine",
            help="Enter any medical condition or health topic",
            label_visibility="collapsed"
        )
    
    with col2:
        analyze_button = st.button("🔍 Start Analysis", type="primary", use_container_width=True)
    
    # Analysis execution
    if analyze_button:
        if not search_term:
            st.error("⚠️ Please enter a search term")
            return
        
        if not api_key or not search_engine_id:
            st.error("⚠️ Please configure API credentials in the sidebar")
            return
        
        # Run the analysis
        run_full_analysis(search_term, api_key, search_engine_id, num_results, generate_figs, run_stats)
    
    # Display results if available
    if st.session_state.results is not None:
        display_results()


def display_reanalysis_interface(generate_figs, run_stats):
    """Display interface for re-analyzing uploaded data."""
    
    st.header("2. Upload Revised Excel File")
    
    # Instructions
    with st.expander("📖 Instructions - Click to expand", expanded=True):
        st.markdown("""
        **How to use the Re-analysis feature:**
        
        1. **Download** an existing Excel report from a previous analysis
        2. **Open** the file in Excel or similar spreadsheet software
        3. **Edit** the Readability_Data sheet:
           - Correct source classifications (Institutional ↔ Private)
           - Remove problematic URLs (delete entire rows)
           - Update readability scores if needed
        4. **Save** the file (keep it as .xlsx format)
        5. **Upload** it below
        6. **Enter** the search term
        7. **Click** "Re-Run Analysis"
        
        **What this feature does:**
        - ✅ Skips Google search and web scraping
        - ✅ Runs statistics on your corrected data
        - ✅ Generates new visualizations
        - ✅ Creates updated Excel report
        
        **What you can edit:**
        - Source classifications (change Institutional ↔ Private)
        - Remove entire rows
        - Readability scores (if you have corrections)
        
        **Don't modify:**
        - Column names (keep exactly as: url, domain, source_type, GFI, SMOG, FKG, ARI)
        - File format (must remain .xlsx)
        - Sheet name (must be 'Readability_Data')
        """)
    
    # File uploader
    st.markdown("### Upload File")
    uploaded_file = st.file_uploader(
        "Choose your revised Excel file",
        type=['xlsx'],
        help="Upload the Excel file containing the Readability_Data sheet from a previous analysis"
    )
    
    # Search term input
    st.markdown("### Search Term")
    search_term = st.text_input(
        "Enter the medical topic",
        placeholder="e.g., hypertension, diabetes, migraine",
        help="This will be used for naming output files and labeling visualizations",
        key="reanalysis_search_term"
    )
    
    # Analyze button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_button = st.button(
            "🔄 Re-Run Analysis",
            type="primary",
            use_container_width=True,
            disabled=(uploaded_file is None or not search_term)
        )
    
    # Run reanalysis if button clicked
    if analyze_button and uploaded_file and search_term:
        run_reanalysis(uploaded_file, search_term, generate_figs, run_stats)
    
    # Display results if available
    if st.session_state.results is not None:
        display_results()


def run_reanalysis(uploaded_file, search_term, generate_figs, run_stats):
    """Execute re-analysis on uploaded file."""
    
    st.header("3. Re-analysis Progress")
    
    progress_bar = st.progress(0)
    status = st.empty()
    
    try:
        # Step 1: Save uploaded file temporarily
        status.info("📁 Processing uploaded file...")
        temp_path = os.path.join("results/data", f"temp_{uploaded_file.name}")
        os.makedirs("results/data", exist_ok=True)
        
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        progress_bar.progress(10)
        
        # Step 2: Validate file
        status.info("✓ Validating file structure...")
        is_valid, message, df = data_validator.validate_uploaded_file(temp_path)
        
        progress_bar.progress(20)
        
        if not is_valid:
            st.error(message)
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return
        
        # Show validation success
        st.success(message)
        progress_bar.progress(30)
        
        # Step 3: Prepare data
        status.info("🔧 Preparing data for analysis...")
        df_prepared = data_validator.prepare_dataframe_for_analysis(df)
        progress_bar.progress(40)
        st.success("✓ Data prepared")
        
        # Step 4: Run reanalysis pipeline
        status.info("📊 Running re-analysis pipeline...")
        results = reanalysis_pipeline.run_reanalysis_pipeline(
            df_prepared,
            search_term,
            generate_figs,
            run_stats
        )
        
        progress_bar.progress(100)
        status.success("✅ Re-analysis complete!")
        
        # Store results in session state
        st.session_state.results = results
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        time.sleep(1)  # Brief pause to show completion
        
    except Exception as e:
        st.error(f"❌ Error during re-analysis: {str(e)}")
        st.exception(e)
        
        # Clean up temp file on error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)


def run_full_analysis(search_term, api_key, engine_id, num_results, generate_figs, run_stats):
    """Execute the complete analysis pipeline."""
    
    st.header("2. Analysis Progress")
    
    progress_bar = st.progress(0)
    status = st.empty()
    
    try:
        # Step 1: Search Google using SerpAPI
        status.info("🔍 Searching Google via SerpAPI...")
        urls = search_serpapi.search_google_serpapi(search_term, config.SERPAPI_KEY, num_results)
        progress_bar.progress(10)
        st.success(f"✓ Found {len(urls)} results")
        
        # Step 2: Extract domains
        for url_data in urls:
            from modules.search_serpapi import search_google_fallback
            from urllib.parse import urlparse
            parsed = urlparse(url_data['url'])
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            url_data['domain'] = domain
        
        # Step 3: Scraping
        status.info("📄 Extracting webpage content...")
        results = []
        
        for i, url_data in enumerate(urls):
            scraped = scraper.scrape_webpage(url_data['url'])
            url_data.update(scraped)
            results.append(url_data)
            
            # Update progress
            progress = 10 + int((i / len(urls)) * 40)
            progress_bar.progress(progress)
            
            if (i + 1) % 10 == 0:
                status.info(f"📄 Processed {i+1}/{len(urls)} pages...")
        
        successful = len([r for r in results if r.get('status') == 'success'])
        st.success(f"✓ Extracted {successful} pages successfully")
        
        # Step 4: Classification
        status.info("🏷️ Classifying sources...")
        for result in results:
            classification, confidence = classifier.classify_source(
                result['url'],
                result.get('title', ''),
                result.get('domain', '')
            )
            result['source_type'] = classification
            result['classification_confidence'] = confidence
        
        progress_bar.progress(60)
        st.success("✓ Sources classified")
        
        # Step 5: Readability
        status.info("📊 Calculating readability metrics...")
        for i, result in enumerate(results):
            if result.get('content') and result.get('status') == 'success':
                metrics = readability.calculate_readability(result['content'])
                if metrics:
                    result.update(metrics)
            
            progress = 60 + int((i / len(results)) * 20)
            progress_bar.progress(progress)
        
        st.success("✓ Readability calculated")
        
        # Step 6: Statistics
        stats = None
        if run_stats:
            status.info("📈 Performing statistical analysis...")
            df = pd.DataFrame(results)
            stats = statistics.perform_statistical_analysis(df)
            progress_bar.progress(85)
            st.success("✓ Statistical analysis complete")
        
        # Step 7: Visualizations
        figures = []
        if generate_figs:
            status.info("📊 Creating visualizations...")
            df = pd.DataFrame(results)
            output_dir = f"results/figures"
            os.makedirs(output_dir, exist_ok=True)
            figures = visualization.create_all_visualizations(df, stats, output_dir, search_term)
            progress_bar.progress(95)
            st.success(f"✓ Generated {len(figures)} figures")
        
        # Step 8: Export
        status.info("💾 Generating Excel report...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"{search_term.replace(' ', '_')}_{timestamp}.xlsx"
        excel_path = os.path.join("results/data", excel_filename)
        os.makedirs("results/data", exist_ok=True)
        
        data_manager.export_to_excel(results, stats, search_term, excel_path)
        progress_bar.progress(100)
        status.success("✅ Analysis complete!")
        
        # Store results in session state
        st.session_state.results = {
            'df': pd.DataFrame(results),
            'stats': stats,
            'figures': figures,
            'excel_path': excel_path,
            'search_term': search_term
        }
        
        time.sleep(1)  # Brief pause to show completion
        
    except Exception as e:
        st.error(f"❌ Error during analysis: {str(e)}")
        st.exception(e)


def display_results():
    """Display analysis results."""
    
    if st.session_state.results is None:
        return
    
    df = st.session_state.results['df']
    stats = st.session_state.results['stats']
    figures = st.session_state.results['figures']
    excel_path = st.session_state.results['excel_path']
    search_term = st.session_state.results['search_term']
    
    st.header("3. Analysis Results")
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total = len(df)
    inst = len(df[df['source_type'] == 'Institutional']) if 'source_type' in df.columns else 0
    priv = len(df[df['source_type'] == 'Private']) if 'source_type' in df.columns else 0
    
    with col1:
        st.metric("Total URLs", total)
    with col2:
        st.metric("Institutional", f"{inst} ({inst/total*100:.0f}%)")
    with col3:
        st.metric("Private", f"{priv} ({priv/total*100:.0f}%)")
    with col4:
        if 'mean_readability' in df.columns:
            mean_read = df['mean_readability'].mean()
            st.metric("Mean Readability", f"{mean_read:.1f}")
    with col5:
        if 'mean_readability' in df.columns:
            universal = len(df[df['mean_readability'] <= 8])
            st.metric("Universal (≤8)", f"{universal} ({universal/total*100:.0f}%)")
    
    # Tabbed interface
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Overview",
        "📊 Statistics",
        "📄 Data Table",
        "🖼️ Visualizations",
        "⬇️ Download"
    ])
    
    with tab1:
        show_overview(df, stats)
    
    with tab2:
        show_statistics(stats)
    
    with tab3:
        show_data_table(df)
    
    with tab4:
        show_visualizations(figures)
    
    with tab5:
        show_downloads(excel_path, search_term, df)


def show_overview(df, stats):
    """Display overview tab."""
    st.subheader("Key Findings")
    
    if 'mean_readability' in df.columns:
        st.markdown("#### Overall Readability")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Mean", f"{df['mean_readability'].mean():.2f}")
            st.metric("Median", f"{df['mean_readability'].median():.2f}")
        
        with col2:
            st.metric("Std Dev", f"{df['mean_readability'].std():.2f}")
            st.metric("Range", f"{df['mean_readability'].min():.1f} - {df['mean_readability'].max():.1f}")
    
    if 'source_type' in df.columns:
        st.markdown("#### By Source Type")
        comparison = df.groupby('source_type')['mean_readability'].agg([
            ('Mean', 'mean'),
            ('Median', 'median'),
            ('Std Dev', 'std'),
            ('Count', 'count')
        ]).round(2)
        st.dataframe(comparison, use_container_width=True)


def show_statistics(stats):
    """Display statistics tab."""
    if not stats:
        st.info("Statistical analysis was not performed")
        return
    
    st.subheader("Statistical Analysis Results")
    
    # Group comparisons
    st.markdown("### Institutional vs. Private Comparison")
    
    comparison_data = []
    for metric in ['GFI', 'SMOG', 'FKG', 'ARI']:
        if metric in stats.get('comparisons', {}):
            comp = stats['comparisons'][metric]
            comparison_data.append({
                'Metric': metric,
                'Test': comp.get('test_used', ''),
                'Institutional Mean': f"{comp.get('group1_mean', 0):.2f}",
                'Private Mean': f"{comp.get('group2_mean', 0):.2f}",
                'P-value': f"{comp.get('p_value', 0):.4f}",
                'Significant': '✓' if comp.get('significant') else '✗',
                'Effect Size': f"{comp.get('effect_size', 0):.3f}"
            })
    
    if comparison_data:
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)


def show_data_table(df):
    """Display data table tab."""
    st.subheader("Complete Data Table")
    
    # Column selector
    default_cols = ['rank', 'url', 'source_type', 'GFI', 'SMOG', 'FKG', 'ARI', 'mean_readability']
    available_cols = [col for col in default_cols if col in df.columns]
    
    display_df = df[available_cols].copy()
    
    # Format numeric columns
    for col in ['GFI', 'SMOG', 'FKG', 'ARI', 'mean_readability']:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(1)
    
    st.dataframe(display_df, width='stretch', height=500)


def show_visualizations(figures):
    """Display visualizations tab."""
    if not figures:
        st.info("Visualizations were not generated")
        return
    
    st.subheader("Visualizations")
    
    st.markdown("#### Box Plots - Group Comparisons")
    box_plots = [f for f in figures if 'boxplot' in f]
    if box_plots:
        cols = st.columns(2)
        for i, fig_path in enumerate(box_plots):
            with cols[i % 2]:
                st.image(fig_path)
    
    st.markdown("#### Distributions")
    histograms = [f for f in figures if 'histogram' in f]
    if histograms:
        cols = st.columns(2)
        for i, fig_path in enumerate(histograms):
            with cols[i % 2]:
                st.image(fig_path)
    
    st.markdown("#### Summary Comparison")
    summary = [f for f in figures if 'comparison' in f or 'summary' in f]
    for fig_path in summary:
        st.image(fig_path)


def show_downloads(excel_path, search_term, df):
    """Display downloads tab."""
    st.subheader("Download Results")
    
    # Excel download
    st.markdown("#### 📊 Excel Report")
    st.markdown("""
    Comprehensive Excel workbook containing:
    - Summary statistics
    - Complete data table  
    - Statistical test results
    - Full webpage text
    - Classification details
    """)
    
    if os.path.exists(excel_path):
        with open(excel_path, 'rb') as f:
            st.download_button(
                label="⬇️ Download Excel Report",
                data=f,
                file_name=os.path.basename(excel_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    # CSV download
    st.markdown("#### 📄 CSV Data")
    csv_data = df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download CSV Data",
        data=csv_data,
        file_name=f"{search_term.replace(' ', '_')}_data.csv",
        mime="text/csv",
        use_container_width=True
    )


if __name__ == "__main__":
    main()
