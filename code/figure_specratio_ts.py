import requests
import pandas as pd
import datetime
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.pyplot import figure
import matplotlib.dates as mdates

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

    ts_data = ts_data.merge(usdc_data, left_index=True, right_index=True, how="outer")

    # Fetch daily Bitcoin price data from FRED
    btc_data = web.DataReader("CBBTCUSD", "fred", start_date, end_date)
    btc_data.fillna(method="ffill", inplace=True)
    btc_price_monthly = btc_data["CBBTCUSD"].resample("M").mean()
    btc_price_monthly.sort_index(inplace=True)
    btc_price_monthly = btc_price_monthly.reset_index()
    btc_price_monthly["year"] = btc_price_monthly["DATE"].dt.year
    dtplot = (
        ts_data.resample("Y")
        .mean()
        .assign(
            Trading_Stablecoins=lambda x: x.ts_volume / x.ts_market_cap,
            USDC=lambda x: x.USDC_volume / x.USDC_market_cap,
        )
    )
    # dtplot.index = dtplot.index.year
    combined = dtplot[["USDC", "Trading_Stablecoins"]].rename(
        columns={"Trading_Stablecoins": "Trading\nStablecoins"}
    )
    combined["year"] = combined.index.year
    combined_btc = btc_price_monthly.merge(combined, on="year", how="left")

    df_yearly = combined_btc.loc[
        (combined_btc["DATE"].dt.month == 1) & (combined_btc["DATE"].dt.day == 31)
    ]
    df_yearly["DATE"] = pd.to_datetime(df_yearly["DATE"], format="%Y")
    # Change all dates to 1 for easy to plot purpose
    df_yearly["DATE"] = pd.to_datetime(
        {
            "year": df_yearly["DATE"].dt.year,
            "month": df_yearly["DATE"].dt.month,
            "day": 1,
        }
    )

    # Start
    fig, ax1 = plt.subplots(figsize=(4, 3))  #    figure(figsize=(4, 3))
    ax2 = ax1.twinx()
    ax2.plot(
        combined_btc["DATE"],
        combined_btc["CBBTCUSD"],
        color="#ADD8E6",
        label="BTC",
        linestyle="dashed",
        linewidth=0.5,
    )
    ax2.set_xlabel("Date")
    # ax2.tick_params("y")

    # We will add/subtract a timedelta to each date for the bars to appear side by side.
    width = pd.to_timedelta(60, unit="D")  # Change this to adjust the width of bars

    ax1.bar(
        df_yearly["DATE"] - width,  # subtract width/2 from each date for the first plot
        df_yearly["USDC"],
        color="#2775ca",
        width=2 * width,  # width in terms of days
        label="USDC",
        align="center",
    )

    ax1.bar(
        df_yearly["DATE"] + width,  # add width/2 to each date for the second plot
        df_yearly["Trading\nStablecoins"],
        color="#c7c5d1",
        width=2 * width,  # width in terms of days
        label="Trading Stablecoins",
        align="center",
    )

    # ax1.tick_params("y")

    # Format x-axis to display years only
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Add a legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    plt.xticks(rotation=0, fontsize=10)
    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        prop={"size": 8},
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        ncol=3,
    )

    # plt.legend(loc="best", fontsize=10, frameon=False)

    plt.savefig("../output/Figure_specratio_ts.pdf", bbox_inches="tight")


if __name__ == "__main__":
    plot_ts_speculative_ratio()
