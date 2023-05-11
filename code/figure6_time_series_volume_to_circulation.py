import requests
import pandas as pd
import datetime
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.pyplot import figure

# Create a api_key.py file in the same directory and add your CMC API key
from api_key import CMC_API_KEY
from utils import fetch_cmc_data


def plot_ts_speculative_ratio(
    start_date=datetime.datetime(2019, 1, 1), end_date=datetime.datetime(2023, 3, 31)
):
    # Fetch daily USDC, USDT, and BUSD market cap data from CMC
    usdc_data = fetch_cmc_data("USDC").loc[start_date:end_date]
    usdt_data = fetch_cmc_data("USDT").loc[start_date:end_date]
    busd_data = fetch_cmc_data("BUSD").loc[start_date:end_date]

    ts_data = usdt_data.merge(busd_data, left_index=True, right_index=True, how="outer")
    ts_data.fillna(0, inplace=True)
    ts_data["ts_market_cap"] = ts_data["USDT_market_cap"] + ts_data["BUSD_market_cap"]
    ts_data["ts_volume"] = ts_data["USDT_volume"] + ts_data["BUSD_volume"]

    # Calculate to ratio and resample to monthly
    dryT = (
        pd.DataFrame(
            {"Trading Stablecoins": (ts_data["ts_volume"]) / (ts_data["ts_market_cap"])}
        )
        .resample("Y", label="left")
        .mean()
    )

    dryT = dryT.loc[datetime.datetime(2019, 1, 1) :]
    dryT.index = dryT.index.year
    dryT.name = "Trading Stablecoins"

    dry = (
        (usdc_data["USDC_volume"] / usdc_data["USDC_market_cap"])
        .resample("Y", label="left")
        .mean()
    )
    dry = dry.loc[datetime.datetime(2019, 1, 1) :]
    dry.index = dry.index.year
    dry.name = "USDC"

    figure(figsize=(18, 12), dpi=300)
    ax = plt.axes()
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)
    ax.yaxis.grid(False)

    combined = pd.concat([dry, dryT], axis=1)

    color_dict = {"USDC": "#2775ca", "Trading Stablecoins": "#c7c5d1"}
    combined = combined[["USDC", "Trading Stablecoins"]]

    combined.plot(
        kind="bar",
        ax=ax,
        color=list(color_dict.values()),
        width=0.75,
        legend=True,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.xticks(rotation=0, fontsize=30)
    plt.xticks(fontsize=25)
    plt.legend(bbox_to_anchor=(0.5, -0.05), loc="upper center", ncol=2, fontsize=30)

    plt.savefig("../output/Figure6.png", bbox_inches="tight")


if __name__ == "__main__":
    plot_ts_speculative_ratio()
