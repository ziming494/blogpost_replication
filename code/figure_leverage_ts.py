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
from figure3_debt_to_circulation import (
    fetch_repo_market_data,
    read_lending_pool_data,
)


def fetch_ts_m2_data_and_calculate_ratio(
    start_date=datetime.datetime(2022, 4, 1), end_date=datetime.datetime(2023, 3, 31)
):
    # Fetch repo data
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    repo = fetch_repo_market_data(start_date_str, end_date_str)
    repo_weekly = repo.resample("W-MON").asfreq()
    repo_weekly.dropna(how="any", axis=0, inplace=True)
    repo_weekly.sort_index(inplace=True)

    # Fetch weekly M2 data
    read_start_date = start_date - datetime.timedelta(days=5)
    m2_data = (
        web.DataReader("WM2NS", "fred", read_start_date, end_date)
        .fillna(method="ffill")
        .loc[start_date:end_date]
    )

    # Calculate ratio
    compare = m2_data.merge(repo_weekly, left_index=True, right_index=True)
    compare["repo_m2_ratio"] = compare["total value"] / (compare["WM2NS"] * 1e9)
    return compare


def plot_ts_debt_to_circulation(start_date, end_date):
    usdc_data = (
        fetch_cmc_data("USDC")
        .loc[start_date:end_date]
        .reset_index()
        .rename(columns={"index": "ds"})
    )
    usdc_lendingpool = read_lending_pool_data()
    usdc_lending = usdc_data.merge(usdc_lendingpool, how="left", on=["ds"])
    usdc_lending["usdc_debt_to_mktcap"] = (
        usdc_lending["debt_outstanding"] / usdc_lending["USDC_market_cap"]
    )
    usdc_lending.set_index("ds", inplace=True)
    usdc_debt_to_mktcap_ratio = usdc_lending[["usdc_debt_to_mktcap"]]
    m2_ratio = fetch_ts_m2_data_and_calculate_ratio(start_date, end_date)
    combined = m2_ratio.merge(
        usdc_debt_to_mktcap_ratio, how="left", left_index=True, right_index=True
    )
    combined = combined[["repo_m2_ratio", "usdc_debt_to_mktcap"]]
    combined.rename(
        columns={"usdc_debt_to_mktcap": "USDC", "repo_m2_ratio": "Repo"}, inplace=True
    )
    resampled_combined = combined.resample("Y").mean()
    resampled_combined.index = resampled_combined.index.year

    # Plot bar graph
    figure(figsize=(4, 3))

    ax = plt.axes()
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)
    ax.yaxis.grid(False)

    color_dict = {"USDC": "#2775ca", "Repo": "#c7c5d1"}
    resampled_combined = resampled_combined[["USDC", "Repo"]]
    bars = resampled_combined.plot(
        kind="bar",
        ax=ax,
        color=list(color_dict.values()),
        width=0.75,
        legend=True,
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.set_yticks([0, 0.05, 0.1, 0.15, 0.2])
    ax.set_yticklabels([0, 0.05, 0.1, 0.15, 0.2], fontsize=10, font="Proxima Nova")
    plt.xticks(rotation=0, fontsize=10)
    plt.xticks(fontsize=10)
    plt.legend(loc="upper right", fontsize=10, frameon=False)
    plt.savefig("../output/Figure_leverage_ts.pdf", bbox_inches="tight")


if __name__ == "__main__":
    plot_ts_debt_to_circulation(
        start_date=datetime.datetime(2020, 12, 2),
        end_date=datetime.datetime(2023, 3, 31),
    )
