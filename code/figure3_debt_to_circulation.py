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


def fetch_repo_market_data(start_date="2022-04-01", end_date="2023-03-31"):
    # fetch repo data
    url = "https://data.financialresearch.gov/v1/series/multifull"
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "mnemonics": "REPO-TRI_TV_TOT-P,REPO-DVP_TV_TOT-P,REPO-GCF_TV_TOT-P",
    }
    response = requests.get(url, params=params)
    data = response.json()

    # clean data
    tri = pd.DataFrame(data["REPO-TRI_TV_TOT-P"]["timeseries"]["aggregation"])
    tri = tri.rename({0: "date", 1: "tri value"}, axis=1)

    dvp = pd.DataFrame(data["REPO-DVP_TV_TOT-P"]["timeseries"]["aggregation"])
    dvp = dvp.rename({0: "date", 1: "dvp value"}, axis=1)

    gcf = pd.DataFrame(data["REPO-GCF_TV_TOT-P"]["timeseries"]["aggregation"])
    gcf = gcf.rename({0: "date", 1: "gcf value"}, axis=1)

    # merge dfs
    repo = tri.merge(dvp, on=["date"], how="left")
    repo = repo.merge(gcf, on=["date"], how="left")

    # fillna and to_datetime
    repo["date"] = pd.to_datetime(repo["date"])
    repo.set_index("date", inplace=True)
    repo.sort_index(inplace=True)

    repo.fillna(method="ffill", inplace=True)

    # create total column
    repo["total value"] = repo["tri value"] + repo["dvp value"] + repo["gcf value"]
    return repo


def fetch_m2_data_and_calculate_ratio(
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
    avg_ratio = compare["repo_m2_ratio"].mean()
    return avg_ratio


def read_lending_pool_data():
    # Read in lending pool data
    aave_v2 = pd.read_csv("../data/aave_v2.csv", parse_dates=["ds"])
    aave_v2.rename(columns={"current_variable_debt": "aave_v2_debt"}, inplace=True)
    aave_v3 = pd.read_csv("../data/aave_v3.csv", parse_dates=["ds"])
    aave_v3.rename(columns={"current_variable_debt": "aave_v3_debt"}, inplace=True)
    compound_v2 = pd.read_csv("../data/compound_v2.csv", parse_dates=["ds"])
    compound_v2.rename(
        columns={"current_variable_debt": "compound_v2_debt"}, inplace=True
    )
    # Merge data
    merge_aave = aave_v2.merge(aave_v3, on=["symbol", "ds"], how="outer")
    lending_pool = merge_aave.merge(compound_v2, on=["symbol", "ds"], how="outer")
    lending_pool.fillna(0, inplace=True)
    lending_pool["debt_outstanding"] = (
        lending_pool["aave_v2_debt"]
        + lending_pool["aave_v3_debt"]
        + lending_pool["compound_v2_debt"]
    )

    usdc_lendingpool = lending_pool.loc[lending_pool["symbol"] == "USDC"]
    return usdc_lendingpool


def plot_debt_to_circulation(start_date, end_date):
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
    # print(usdc_lending)

    usdc_debt_to_mktcap_ratio = usdc_lending["usdc_debt_to_mktcap"].mean()
    m2_ratio = fetch_m2_data_and_calculate_ratio(start_date, end_date)

    print(m2_ratio, usdc_debt_to_mktcap_ratio)

    # Plot bar graph
    figure(figsize=(18, 12), dpi=300)

    ax = plt.axes()
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)
    ax.yaxis.grid(False)

    bars = plt.bar(
        ["USDC Borrowing /n Circulation", "Repo Borrowing /n U.S. Dollar (M2)"],
        [usdc_debt_to_mktcap_ratio, m2_ratio],
        width=0.75,
    )
    bars[0].set_color("#2775ca")
    bars[1].set_color("#c7c5d1")
    ax.set_xticklabels(
        ["USDC Borrowing /\nCirculation", "Repo Borrowing /\nU.S. Dollar (M2)"],
        fontsize=30,
        font="Proxima Nova",
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.set_yticks([0, 0.05, 0.1, 0.15, 0.2])
    ax.set_yticklabels([0, 0.05, 0.1, 0.15, 0.2], fontsize=25, font="Proxima Nova")
    # plt.show()
    plt.savefig("../output/Figure3.png", format="png", dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    plot_debt_to_circulation(
        start_date=datetime.datetime(2022, 4, 1),
        end_date=datetime.datetime(2023, 3, 31),
    )
