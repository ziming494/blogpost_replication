# -------- Prepare the data --------
import pandas as pd
import pandas_datareader.data as web
import requests
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

from api_key import CMC_API_KEY
from utils import fetch_cmc_data


def plot_circulation_corr(start_date, end_date):
    read_start_date = start_date - datetime.timedelta(days=5)

    m2_data = (
        web.DataReader("WM2NS", "fred", read_start_date, end_date)
        .fillna(method="ffill")
        .loc[start_date:end_date]
    )
    spx_data = (
        web.DataReader("SP500", "fred", read_start_date, end_date)
        .fillna(method="ffill")
        .loc[start_date:end_date]
    )

    # # Merge M2 and SPX datasets

    # Fetch daily Bitcoin price data from FRED
    btc_data = web.DataReader("CBBTCUSD", "fred", start_date, end_date)
    btc_data.fillna(method="ffill", inplace=True)

    # Fetch daily USDC, USDT, and BUSD market cap data from CMC
    usdc_data = fetch_cmc_data("USDC").loc[start_date:end_date]
    usdt_data = fetch_cmc_data("USDT").loc[start_date:end_date]
    busd_data = fetch_cmc_data("BUSD").loc[start_date:end_date]

    # Combine USDT & BUSD as traidng stablecoins (ts)
    ts_data = usdt_data.merge(busd_data, left_index=True, right_index=True, how="outer")
    ts_data.fillna(0, inplace=True)
    ts_data["ts_market_cap"] = ts_data["USDT_market_cap"] + ts_data["BUSD_market_cap"]

    # -------- Calculate the correlation between M2 and SPX --------
    # Left join for resample purpose
    spx_m2 = m2_data.merge(spx_data, left_index=True, right_index=True, how="left")
    spx_m2.sort_index(inplace=True)
    spx_m2["m2_logchange"] = np.log(spx_m2["WM2NS"] / (spx_m2["WM2NS"].shift(1)))
    spx_m2["sp_logchange"] = np.log(spx_m2["SP500"] / (spx_m2["SP500"].shift(1)))

    corr_m2_spx = spx_m2[["m2_logchange", "sp_logchange"]].corr().iloc[0, 1]

    # -------- Calculate the correlation between USDC and BTC --------
    usdc_btc = usdc_data.merge(btc_data, left_index=True, right_index=True, how="inner")
    # Resample to weekly
    usdc_btc_weekly = usdc_btc.resample("W-MON").asfreq().loc[start_date:end_date]
    usdc_btc_weekly.dropna(how="any", axis=0, inplace=True)
    usdc_btc_weekly.sort_index(inplace=True)
    usdc_btc_weekly["usdc_mktcap_logchange"] = np.log(
        usdc_btc_weekly["USDC_market_cap"]
        / (usdc_btc_weekly["USDC_market_cap"].shift(1))
    )
    usdc_btc_weekly["btc_logchange"] = np.log(
        usdc_btc_weekly["CBBTCUSD"] / (usdc_btc_weekly["CBBTCUSD"].shift(1))
    )

    corr_usdc_btc = (
        usdc_btc_weekly[["usdc_mktcap_logchange", "btc_logchange"]].corr().iloc[0, 1]
    )

    # -------- Calculate the correlation between Trading stablecoins and BTC --------
    ts_btc = ts_data.merge(btc_data, left_index=True, right_index=True, how="inner")
    # Resample to weekly
    ts_btc_weekly = ts_btc.resample("W-MON").asfreq().loc[start_date:end_date]
    ts_btc_weekly.sort_index(inplace=True)
    ts_btc_weekly["ts_mktcap_logchange"] = np.log(
        ts_btc_weekly["ts_market_cap"] / (ts_btc_weekly["ts_market_cap"].shift(1))
    )
    ts_btc_weekly["btc_logchange"] = np.log(
        ts_btc_weekly["CBBTCUSD"] / (ts_btc_weekly["CBBTCUSD"].shift(1))
    )
    ts_btc_weekly.dropna(how="any", axis=0, inplace=True)

    corr_ts_btc = (
        ts_btc_weekly[["ts_mktcap_logchange", "btc_logchange"]].corr().iloc[0, 1]
    )

    # plot bar graph
    figure(figsize=(4, 3))

    ax = plt.axes()
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)
    ax.yaxis.grid(False)
    plt.axhline(y=0, color="gray", linestyle="-")

    bars = plt.bar(
        ["USDC & BTC", "M2 & SPX", "Trading Stablecoins & BTC"],
        [corr_usdc_btc, corr_m2_spx, corr_ts_btc],
        width=0.75,
    )
    bars[0].set_color("#2775ca")
    bars[1].set_color("#c7c5d1")
    bars[2].set_color("#c7c5d1")
    ax.set_xticklabels(
        ["USDC &\nBTC", "U.S. Dollar (M2) &\nS&P 500", "Trading Stablecoins &\nBTC"],
        font="Proxima Nova",
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.set_yticks([0, 0.05, 0.1, 0.15, 0.2])
    ax.set_yticklabels([0, 0.05, 0.1, 0.15, 0.2], fontsize=8, font="Proxima Nova")

    plt.xticks(rotation=10, fontsize=8)

    plt.savefig("../output/Figure_corr_comp.pdf", bbox_inches="tight")


if __name__ == "__main__":
    plot_circulation_corr(
        start_date=datetime.datetime(2021, 1, 1),
        end_date=datetime.datetime(2023, 3, 31),
    )
