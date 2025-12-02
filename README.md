# Medical Website Readability Analyzer

🏥 An automated tool for analyzing the readability of online medical information using validated readability metrics.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

## 🌟 Features

- **🔍 Google Search Integration**: Search Google for medical topics via SerpAPI
- **🏷️ Source Classification**: Automatically classify sources as Institutional vs. Private
- **📊 Readability Analysis**: Calculate multiple readability metrics:
  - Gunning Fog Index (GFI)
  - SMOG Index
  - Flesch-Kincaid Grade Level (FKG)
  - Automated Readability Index (ARI)
- **📈 Statistical Analysis**: Compare readability between source types with statistical tests
- **📊 Interactive Visualizations**: Box plots, histograms, and comparison charts
- **📄 Excel Export**: Comprehensive reports with all data and analysis
- **🔄 Re-analysis Mode**: Upload and re-analyze corrected data

## 🚀 Live Demo

🔗 **[Try the Medical Readability Analyzer](https://your-app-url.streamlit.app)**

*Note: First load may take a moment as the app wakes up.*

## 📖 How It Works

1. **Enter a medical topic** (e.g., "diabetes", "hypertension", "migraine")
2. **Configure analysis settings** in the sidebar
3. **Start analysis** - the tool will:
   - Search Google for your topic
   - Scrape webpage content
   - Classify sources as institutional or private
   - Calculate readability metrics
   - Perform statistical analysis
   - Generate visualizations
4. **Review results** and download Excel reports

## 🛠️ Local Setup

### Prerequisites
- Python 3.8 - 3.12
- pip package manager

### Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/medical-readability-analyzer.git
   cd medical-readability-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**
   
   Create `.streamlit/secrets.toml` with your API keys:
   ```toml
   GOOGLE_API_KEY = "your-google-api-key"
   SEARCH_ENGINE_ID = "your-search-engine-id"
   SERPAPI_KEY = "your-serpapi-key"
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** to `http://localhost:8501`

## 🔑 API Keys Required

### SerpAPI (Required)
- **Purpose**: Primary search functionality
- **Get it**: [SerpAPI.com](https://serpapi.com/)
- **Free tier**: 100 searches/month

### Google Custom Search API (Optional)
- **Purpose**: Fallback search method
- **Get it**: [Google Cloud Console](https://console.cloud.google.com/)
- **Setup**: Enable Custom Search API and create a Custom Search Engine

## 📊 Readability Metrics Explained

### Gunning Fog Index (GFI)
- **Purpose**: Estimates years of formal education needed to understand text
- **Scale**: Lower = easier (6-8 = universal accessibility)

### SMOG Index
- **Purpose**: Simple Measure of Gobbledygook - estimates reading grade level
- **Scale**: Grade levels (8 = 8th grade reading level)

### Flesch-Kincaid Grade Level (FKG)
- **Purpose**: U.S. grade level needed to understand text
- **Scale**: Grade levels (12 = high school graduate level)

### Automated Readability Index (ARI)
- **Purpose**: Character-based readability assessment
- **Scale**: Grade levels (lower = more accessible)

### Universal Accessibility
- **Target**: ≤8th grade level for universal health literacy
- **Reference**: Health literacy best practices

## 📁 Project Structure

```
medical-readability-analyzer/
├── app.py                    # Main Streamlit application
├── config.py                 # Configuration and settings
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .gitignore               # Git ignore rules
├── .streamlit/
│   ├── secrets.toml         # API keys (not in repo)
│   └── config.toml          # Streamlit configuration
└── modules/
    ├── __init__.py          # Package initializer
    ├── search_serpapi.py    # Google search functionality
    ├── scraper.py           # Web scraping
    ├── classifier.py        # Source classification
    ├── readability.py       # Readability calculations
    ├── statistics.py        # Statistical analysis
    ├── visualization.py     # Chart generation
    ├── data_manager.py      # Data export/import
    ├── data_validator.py    # Data validation
    └── reanalysis_pipeline.py # Re-analysis workflow
```

## 🔄 Re-analysis Feature

The app supports re-analyzing previously downloaded data with corrections:

1. **Download** Excel report from initial analysis
2. **Edit** the 'Readability_Data' sheet:
   - Correct source classifications (Institutional ↔ Private)
   - Remove problematic URLs (delete entire rows)
   - Update readability scores if needed
3. **Upload** the corrected file using "Re-analyze Data" mode
4. **Get updated** statistics and visualizations

### Editable Fields
- `source_type`: Change between "Institutional" and "Private"
- `GFI`, `SMOG`, `FKG`, `ARI`: Readability scores
- Remove entire rows for URLs you want to exclude

### Don't Modify
- Column names (must match exactly)
- Sheet name (must be 'Readability_Data')
- File format (must remain .xlsx)

## 📈 Statistical Analysis

The tool performs comprehensive statistical analysis:

- **Descriptive Statistics**: Mean, median, standard deviation by source type
- **Statistical Tests**: 
  - Welch's t-test (unequal variances)
  - Mann-Whitney U test (non-parametric)
- **Effect Sizes**: Cohen's d for meaningful difference assessment
- **Significance Testing**: p < 0.05 threshold with effect size context

## 🎨 Visualizations

- **Box Plots**: Compare readability distributions between source types
- **Histograms**: Show readability score distributions
- **Summary Charts**: Overview of key findings
- **High-DPI Export**: 300 DPI PNG files for publication

## 🔒 Privacy & Security

- **No Data Storage**: All analysis is performed in real-time
- **Secure API Handling**: Keys stored in Streamlit secrets
- **HTTPS**: All communications encrypted
- **No User Tracking**: Privacy-focused design

## 📊 Example Use Cases

- **Health Communication Research**: Analyze readability of health information
- **Medical Website Auditing**: Evaluate accessibility of medical content
- **Health Literacy Studies**: Research source differences in readability
- **Content Strategy**: Optimize medical content for target audiences

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Citation

If you use this tool in research, please cite:

```bibtex
@software{medical_readability_analyzer,
  title={Medical Website Readability Analyzer},
  author={Your Name},
  year={2024},
  url={https://github.com/YOUR-USERNAME/medical-readability-analyzer}
}
```

## ⚠️ Limitations

- **API Rate Limits**: SerpAPI free tier limited to 100 searches/month
- **Language**: Currently English-only readability metrics
- **Scope**: Focuses on general medical information (not clinical/technical)
- **Classification**: Automated classification may need manual review

## 🛠️ Technical Details

- **Framework**: Streamlit 1.28+
- **Language**: Python 3.8-3.12
- **Dependencies**: See `requirements.txt`
- **Deployment**: Optimized for Streamlit Community Cloud
- **Performance**: ~10-30 seconds per analysis (varies by result count)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/YOUR-USERNAME/medical-readability-analyzer/issues)
- **Email**: your-email@example.com
- **Documentation**: This README and in-app help

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Readability Metrics**: Based on established readability formulas
- **Statistical Methods**: Following health literacy research best practices
- **UI Framework**: Built with [Streamlit](https://streamlit.io/)
- **Search API**: Powered by [SerpAPI](https://serpapi.com/)

## 📅 Version History

- **v1.0.0** (2024): Initial release with core functionality
  - Google search integration
  - Source classification
  - Multiple readability metrics
  - Statistical analysis
  - Excel export
  - Re-analysis feature

---

**Made with ❤️ for improving health information accessibility**
