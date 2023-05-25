# Repo for replicating paper: Beyond Speculation: Payment Stablecoins for RTGS

- Create a `api_key.py` file under `code` folder with a `CMC_API_KEY` variable that stores your CoinmarketCap API key.
- Download historical data by going into `code` folder and run `python utils.py`. This will download historical market cap and volume data for USDC, USDT and BUSD and store under `data` folder.
- To replicate the leverage figure for example, go to `code` folder and run `python figure_leverage.py`

Dune data source

- Compound V2: [Messari Dashboard](<https://dune.com/messari/Messari%3A-Compound-Micro-Financial-Statements-(per-Token)>)
