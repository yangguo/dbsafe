# DBSafe - 外管局监管处罚分析 (Regulatory Enforcement Analysis)

A Streamlit application for scraping, analyzing, and visualizing regulatory enforcement cases from Chinese financial regulatory authorities.

## Features

- 📊 **Data Visualization**: Interactive charts and maps to analyze enforcement patterns
- 🔍 **Advanced Search**: Filter cases by date, amount, keywords, and region
- 📥 **Data Scraping**: Automated collection of case data from regulatory websites
- 📈 **Summary Statistics**: Overview of case counts, penalties, and regional distributions
- 💾 **Data Export**: Download search results and case details as CSV files

## Installation

### Prerequisites

- Python 3.8+
- Chrome browser (for web scraping functionality)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/dbsafe.git
   cd dbsafe
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

2. Open your browser at the URL displayed in the terminal (typically http://localhost:8501)

## Project Structure

```
dbsafe/
├── app.py                  # Main Streamlit application
├── data_processing.py      # Data processing utilities
├── dbsafe.py               # Core functionality and data display
├── requirements.txt        # Project dependencies
├── scraper.py              # Web scraping functionality
├── snapshot.py             # Browser automation utilities
├── utils.py                # General utility functions
├── visualization.py        # Data visualization components
├── map/                    # Geographic data for map visualizations
│   └── chinageo.json       # China GeoJSON for maps
├── safe/                   # Data storage directory (auto-created)
└── temp/                   # Temporary files directory (auto-created)
```

## Features Documentation

### Case Summary

View aggregate statistics about enforcement cases, including total count, date ranges, and regional breakdowns.

### Case Search

Search for specific cases using various criteria:
- Date range
- Document number keywords
- Entity name keywords
- Case description keywords
- Penalty amount thresholds
- Region selection

### Case Update

Update the database with new cases from regulatory websites:
- Select specific regulatory bodies to update
- Update case listings and detailed information
- Track pending updates across regions

### Data Export

Download case data as CSV files:
- Export by region or aggregate data
- Export both summary and detailed information

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.