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


def plot_wallet_to_wallet():
    df = pd.read_csv(
        "../data/other_data_source.csv",
        parse_dates=["As_of"],
        usecols=["Fields", "Value", "As_of"],
    )

    # --------------- USDC wallet to wallet ratio ---------------
    usdc = df.loc[df["Fields"] == "usdc_wallet2wallet_transfer", "Value"].values[0]

    # --------------- cross boarder trade to FX ---------------
    goods_trade = (
        df.loc[df["Fields"] == "global_goods_trade", ["Value", "As_of"]]
    ).rename(columns={"Value": "global_goods_trade"})

    service_trade = (
        df.loc[df["Fields"] == "global_services_trade", ["Value", "As_of"]]
    ).rename(columns={"Value": "global_services_trade"})

    cross_boarder_trade = goods_trade.merge(service_trade, on="As_of", how="inner")
    cross_boarder_trade["global_trade"] = (
        cross_boarder_trade["global_goods_trade"]
        + cross_boarder_trade["global_services_trade"]
    ) * 1e6
    cross_boarder_trade["year"] = cross_boarder_trade["As_of"].dt.year

    fx = (
        df.loc[
            df["Fields"] == "fx_volume",
            ["Value", "As_of"],
        ]
    ).rename(columns={"Value": "fx_volume"})
    fx["year"] = fx["As_of"].dt.year
    fx.drop(columns=["As_of"], inplace=True)

    combined = cross_boarder_trade.merge(fx, on="year", how="left")
    combined.sort_values(by=["As_of"], inplace=True)
    combined.bfill(inplace=True)
    cross_boarder_trade_to_fx = (
        combined["global_trade"] / (combined["fx_volume"] * 252 * 1e6)
    ).mean()

    # --------------- GDP Fed Wire ---------------

    read_start_date = datetime.datetime(2018, 12, 25)

    start_date = datetime.datetime(2020, 1, 1)
    end_date = datetime.datetime(2023, 1, 1)
    gdp_data = (
        web.DataReader("GDP", "fred", read_start_date, end_date)
        .fillna(method="ffill")
        .loc[start_date:end_date]
    )
    gdp_data = gdp_data.loc[gdp_data.index.month == 1]

    gdp_data["year"] = gdp_data.index.year - 1

    fedwire = (
        df.loc[
            df["Fields"] == "fedwire_volume",
            ["Value", "As_of"],
        ]
    ).rename(columns={"Value": "fedwire_volume"})
    fedwire["year"] = fedwire["As_of"].dt.year
    fedwire.drop(columns=["As_of"], inplace=True)

    combined_fedwire = gdp_data.merge(fedwire, on="year", how="left")

    gdp_to_fedwire = (
        (combined_fedwire["GDP"] * 1e9)
        / (combined_fedwire["fedwire_volume"] * 252 * 1e6)
    ).mean()

    # Plot bar graph
    figure(figsize=(4, 3))

    ax = plt.axes()
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)
    ax.yaxis.grid(False)

    bars = plt.bar(
        ["Cross-boarder trade to FX", "GDP to Fedwire", "USDC Wallet to Wallet"],
        [cross_boarder_trade_to_fx, gdp_to_fedwire, usdc],
        width=0.75,
    )
    bars[0].set_color("#c7c5d1")
    bars[1].set_color("#c7c5d1")
    bars[2].set_color("#2775ca")

    ax.set_xticklabels(
        [
            "Global Trade / \n Foreign Exchange Volume",
            "U.S. GDP / \n Fedwire Volume",
            "USDC*",
        ],
        font="Proxima Nova",
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.set_yticks([0, 0.05, 0.1, 0.15])
    ax.set_yticklabels([0, 0.05, 0.1, 0.15], fontsize=7, font="Proxima Nova")
    plt.xticks(rotation=10, fontsize=7)
    plt.savefig("../output/Figure_financialization.pdf", bbox_inches="tight")


if __name__ == "__main__":
    plot_wallet_to_wallet()
