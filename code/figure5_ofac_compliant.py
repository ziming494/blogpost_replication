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


def plot_sanction_compliant():
    df = pd.read_csv(
        "../data/other_data_source.csv",
        parse_dates=["As_of"],
        usecols=["Fields", "Value", "As_of"],
    )

    usdc_ofac_tracable = (
        df.loc[df["Fields"] == "usdc_ofac_compliant", "Value"]
    ).values[0]

    usd_m2 = (df.loc[df["Fields"] == "usd_m2_march_2023", "Value"]).values[0]
    usd_currcir = (df.loc[df["Fields"] == "usd_currcir_march_2023", "Value"]).values[0]

    usd_ofac_tracable = (usd_m2 - usd_currcir) / usd_m2

    # Plot bar graph
    figure(figsize=(18, 12), dpi=300)

    ax = plt.axes()
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)
    ax.yaxis.grid(False)

    bars = plt.bar(
        ["U.S. Dollar (M2)", "USDC"],
        [usd_ofac_tracable, usdc_ofac_tracable],
        width=0.75,
    )
    bars[0].set_color("#c7c5d1")
    bars[1].set_color("#2775ca")

    ax.set_xticklabels(
        ["U.S. Dollar (M2)", "USDC"],
        fontsize=30,
        font="Proxima Nova",
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(
        ["0", "20%", "40%", "60%", "80%", "100%"],
        fontsize=25,
        font="Proxima Nova",
    )
    plt.savefig("../output/Figure5.png", format="png", dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    plot_sanction_compliant()
