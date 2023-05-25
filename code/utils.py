import requests
from api_key import CMC_API_KEY
import pandas as pd


def download_cmc_data(symbol):
    url = "https://pro-api.coinmarketcap.com/v3/cryptocurrency/quotes/historical"
    params = {
        "symbol": "{}".format(symbol),
        "interval": "daily",
        "count": 1825,
        "convert": "USD",
        "aux": "volume,market_cap",
    }
    print(params)
    # Add the API key to the headers
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY, "Accepts": "application/json"}

    # Make the request
    response = requests.get(url, params=params, headers=headers)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        store_data = []
        quotes = data["data"]["{}".format(symbol)][0]["quotes"]
        for i in quotes:
            temp = pd.DataFrame(
                {
                    "{}_volume".format(symbol): [i["quote"]["USD"]["volume_24h"]],
                    "{}_market_cap".format(symbol): [i["quote"]["USD"]["market_cap"]],
                },
                index=[i["timestamp"]],
            )
            store_data.append(temp)
        agg_data = pd.concat(store_data, axis=0)
        agg_data.index = pd.to_datetime(pd.to_datetime(agg_data.index).date)
        agg_data.sort_index(inplace=True)
        # Remove 0 market cap data
        agg_data = agg_data.loc[agg_data["{}_market_cap".format(symbol)] != 0]
        # Fill NA
        agg_data.fillna(method="ffill", inplace=True)
        return agg_data
    else:
        raise (f"Request failed with status code: {response.status_code}")


def download_data():
    symbol_list = ["USDC", "USDT", "BUSD"]
    for symbol in symbol_list:
        data = download_cmc_data(symbol)
        data.to_csv(f"../data/{symbol}_data.csv")


def fetch_cmc_data(symbol):
    data = pd.read_csv(f"../data/{symbol}_data.csv", index_col=0, parse_dates=True)
    return data


if __name__ == "__main__":
    download_data()
