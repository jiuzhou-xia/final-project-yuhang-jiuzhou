# Chicago Housing Affordability Analysis

This project processes and visualizes Chicago housing affordability using FRED and Zillow data.

## Project Structure

```
data/
  raw-data/                   # Raw data files
    CHXRSA.csv                # Chicago Home Price Index (FRED)
    MORTGAGE30US.csv          # 30-Year Fixed Mortgage Rate (FRED)
    MHIIL17000A052NCEN.csv    # Median Household Income (FRED)
    RPIPC16980.csv            # Real Per Capita Personal Income (FRED)
    CHIC917BPPRIVSA.csv       # Building Permits (FRED)
    Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv # Zillow ZHVI (large file; download separately)
  derived-data/               # Processed data and output plots
    merged_annual_updated.csv # Annual merged affordability dataset
code/
  preprocessing.py            # Cleans, annualizes, and merges source data
  plot_fires.py               # Generates project visualizations
```


## Usage

1. Download the large Zillow file and place it here:

```
`data/raw-data/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`
```

Download link:

```
https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv?t=1772398440
```



