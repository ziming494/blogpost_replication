import pandas as pd
import datetime
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import pandas_datareader.data as web
from utils import fetch_cmc_data


def reindex_fields(df, field_name, date_range):
    temp = (
        df.loc[
            df["Fields"] == field_name,
            ["Value", "As_of"],
        ]
    ).rename(columns={"Value": field_name})
    temp.set_index("As_of", inplace=True)
    temp = temp.reindex(date_range)
    temp.sort_index(inplace=True)
    temp.fillna(method="bfill", inplace=True)
    temp.fillna(method="ffill", inplace=True)
    return temp


def plot_speculative_ratio(start_date, end_date):
    df = pd.read_csv(
        "../data/other_data_source.csv",
        parse_dates=["As_of"],
        usecols=["Fields", "Value", "As_of"],
    )

    # Fetch daily USDC, USDT, and BUSD market cap data from CMC
    usdc_data = fetch_cmc_data("USDC").loc[start_date:end_date]
    usdt_data = fetch_cmc_data("USDT").loc[start_date:end_date]
    busd_data = fetch_cmc_data("BUSD").loc[start_date:end_date]

    # Combine USDT & BUSD as traidng stablecoins (ts)
    ts_data = usdt_data.merge(busd_data, left_index=True, right_index=True, how="outer")
    ts_data.fillna(0, inplace=True)
    ts_data["ts_market_cap"] = ts_data["USDT_market_cap"] + ts_data["BUSD_market_cap"]
    ts_data["ts_volume"] = ts_data["USDT_volume"] + ts_data["BUSD_volume"]

    # calculate stablecoin ratios
    usdc_ratio = (usdc_data["USDC_volume"] / usdc_data["USDC_market_cap"]).mean()
    trading_stablecoin_ratio = (ts_data["ts_volume"] / ts_data["ts_market_cap"]).mean()

    # --------------- calculate retail brokerage ratio ---------------
    date_range = pd.date_range(start=start_date, end=end_date)
    schwab_dats = (df.loc[df["Fields"] == "schwab_dats", ["Value", "As_of"]]).rename(
        columns={"Value": "schwab_dats"}
    )
    avg_retail_trade_size = (
        df.loc[df["Fields"] == "avg_retail_trade_size", "Value"]
    ).values[0]
    schwab_bda_balance = (
        df.loc[df["Fields"] == "schwab_bda", ["Value", "As_of"]]
    ).rename(columns={"Value": "schwab_bda"})

    schwab_df = schwab_dats.merge(schwab_bda_balance, on="As_of", how="left")
    schwab_df.sort_values(by=["As_of"], inplace=True)
    schwab_df.fillna(method="ffill", inplace=True)
    schwab_ratio = (
        (schwab_df["schwab_dats"] * 1000 * avg_retail_trade_size)
        / (schwab_df["schwab_bda"] * 1e6)
    ).mean()

    # ---------------calculate USD ratio ---------------
    # M2 data
    read_start_date = start_date - datetime.timedelta(days=5)
    m2_data = (
        web.DataReader("WM2NS", "fred", read_start_date, end_date)
        .fillna(method="ffill")
        .loc[start_date:end_date]
    )
    # Read in FX data from BIS
    fx_data = reindex_fields(
        df, "usd_denominated_fx_spot_and_forward_volume", date_range
    )

    # Read in equity data
    equity_data = reindex_fields(df, "us_equity_volume", date_range)

    # Read in fixed income data
    fixed_income_data = reindex_fields(df, "us_fixed_income_volume", date_range)

    # merge dataframes
    usd_df = m2_data.merge(fx_data, left_index=True, right_index=True, how="left")
    usd_df = usd_df.merge(equity_data, left_index=True, right_index=True, how="left")
    usd_df = usd_df.merge(
        fixed_income_data, left_index=True, right_index=True, how="left"
    )

    usd_ratio = (
        (
            usd_df["usd_denominated_fx_spot_and_forward_volume"] * 1e6
            + usd_df["us_equity_volume"] * 1e9
            + usd_df["us_fixed_income_volume"] * 1e9
        )
        / (usd_df["WM2NS"] * 1e9)
    ).mean()
    # plot bar graph
    figure(figsize=(4, 3))

    ax = plt.axes()
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)
    # ax.yaxis.grid(color="gray", linestyle="-", linewidth=0.5)

    bars = plt.bar(
        ["USDC", "U.S. Dollar", "Retail Brokerage", "Trading Stablecoins"],
        [
            usdc_ratio,
            usd_ratio,
            schwab_ratio,
            trading_stablecoin_ratio,
        ],
        width=0.75,
    )
    bars[0].set_color("#2775ca")
    bars[1].set_color("#c7c5d1")
    bars[2].set_color("#c7c5d1")
    bars[3].set_color("#c7c5d1")
    ax.set_xticklabels(
        ["USDC", "U.S. Dollar\n(M2)", "Retail\nBrokerage", "Trading\nStablecoins"],
        font="Proxima Nova",
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.yticks(
        [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2],
        labels=["0", "0.2", "0.4", "0.6", "0.8", "1.0", "1.2"],
        fontsize=8,
        font="Proxima Nova",
    )
    plt.xticks(rotation=10, fontsize=8)
    plt.savefig("../output/Figure_specratio_comp.pdf", bbox_inches="tight")


if __name__ == "__main__":
    plot_speculative_ratio(
        start_date=datetime.datetime(2021, 1, 1),
        end_date=datetime.datetime(2023, 3, 31),
    )
