# Polymarket Analyst

A Streamlit-based web application for analyzing and visualizing Polymarket prediction markets data. This tool provides real-time insights into market activity, trading volumes, and category distributions across various prediction markets.

## Features

- Real-time data fetching from Polymarket's Gamma API
- Interactive filtering by:
  - Date ranges (Today, This Week, Later than One Week, All Time)
  - Market categories
  - Trading volume
- Visual analytics:
  - Trading volume by category
  - Market distribution by category
- Detailed market information display
- Key metrics tracking:
  - Total number of markets
  - Total trading volume
  - Average liquidity

## Installation

1. Clone the repository:
```bash
git clone https://github.com/kaljuvee/polymarket-analyst.git
cd polymarket-analyst
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run Home.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

3. Click "Fetch Latest Data" to load current market data

4. Use the sidebar filters to analyze specific markets or time periods

## Data Structure

The application fetches data from Polymarket's Gamma API (`https://gamma-api.polymarket.com/markets`). Each market object contains:

### Basic Information
- `id`: Unique identifier for the market
- `question`: The prediction market question
- `slug`: URL-friendly version of the question
- `description`: Detailed description of the market
- `category`: Market category (e.g., "Crypto", "US-current-affairs", "Pop-Culture")
- `endDate`: ISO timestamp when the market closes
- `active`: Boolean indicating if the market is currently active

### Market Details
- `outcomes`: Array of possible outcomes
- `outcomePrices`: Array of prices for each outcome
- `volume`: Total trading volume
- `liquidity`: Available liquidity in the market

### Additional Metadata
- `createdAt`: Timestamp of market creation
- `updatedAt`: Timestamp of last update

## Requirements

- Python 3.8+
- Streamlit
- Pandas
- Plotly
- Requests

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 