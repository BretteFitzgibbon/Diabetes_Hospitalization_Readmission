"""Analyze HbA1c testing and 30-day readmission.

This script is Priya's Member 2 contribution to the team project.
It creates summary tables, a chi-square test, and three visualizations.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import chi2_contingency


DATA_FILE = Path(__file__).with_name("diabetic_data_corrected.csv")
OUTPUT_DIR = Path(__file__).with_name("outputs")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load the final cleaned dataset.
    df = pd.read_csv(DATA_FILE)

    required_columns = {
        "A1Cresult",
        "a1c_tested",
        "readmitted",
        "readmitted_30d",
    }
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    # Confirm the team's agreed definitions.
    expected_a1c_flag = df["A1Cresult"].isin([">7", ">8", "Norm"]).astype(int)
    expected_readmission_flag = df["readmitted"].eq("<30").astype(int)

    if not df["a1c_tested"].eq(expected_a1c_flag).all():
        raise ValueError("The a1c_tested column does not match the agreed definition.")
    if not df["readmitted_30d"].eq(expected_readmission_flag).all():
        raise ValueError("The readmitted_30d column does not match the agreed definition.")

    # Add readable labels for tables and charts.
    df["HbA1c testing status"] = df["a1c_tested"].map(
        {0: "Not tested", 1: "Tested"}
    )
    df["30-day readmission status"] = df["readmitted_30d"].map(
        {0: "Not readmitted", 1: "Readmitted"}
    )

    # 1. Overall HbA1c testing summary.
    testing_summary = (
        df["HbA1c testing status"]
        .value_counts()
        .rename_axis("HbA1c testing status")
        .to_frame("Patients")
    )
    testing_summary["Percentage"] = testing_summary["Patients"] / len(df) * 100
    testing_summary.to_csv(OUTPUT_DIR / "hba1c_testing_summary.csv")

    # 2. Readmission rates for tested versus not-tested patients.
    readmission_summary = (
        df.groupby("HbA1c testing status", sort=False)["readmitted_30d"]
        .agg(Patients="size", Readmissions="sum", Readmission_rate="mean")
    )
    readmission_summary["Patient_percentage"] = (
        readmission_summary["Patients"] / len(df) * 100
    )
    readmission_summary["Readmission_rate"] *= 100
    readmission_summary.to_csv(OUTPUT_DIR / "hba1c_readmission_summary.csv")

    # 3. Chi-square test of association.
    contingency_table = pd.crosstab(
        df["HbA1c testing status"], df["30-day readmission status"]
    ).reindex(
        index=["Tested", "Not tested"],
        columns=["Readmitted", "Not readmitted"],
        fill_value=0,
    )
    chi2, p_value, degrees_of_freedom, expected = chi2_contingency(contingency_table)

    # 4. HbA1c result category breakdown.
    result_summary = (
        df.groupby("A1Cresult", dropna=False)["readmitted_30d"]
        .agg(Patients="size", Readmissions="sum", Readmission_rate="mean")
    )
    result_summary["Patient_percentage"] = result_summary["Patients"] / len(df) * 100
    result_summary["Readmission_rate"] *= 100
    result_summary.index = result_summary.index.fillna("Not tested")
    result_summary.to_csv(OUTPUT_DIR / "a1c_result_readmission_summary.csv")

    # Visualization 1: testing status distribution.
    ax = testing_summary["Patients"].reindex(["Tested", "Not tested"]).plot(
        kind="bar", color=["#2E86AB", "#A23B72"], figsize=(7, 5)
    )
    ax.set_title("HbA1c Testing Status")
    ax.set_xlabel("")
    ax.set_ylabel("Number of patients")
    ax.tick_params(axis="x", rotation=0)
    for container in ax.containers:
        ax.bar_label(container, fmt="%d")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "hba1c_testing_status.png", dpi=200)
    plt.close()

    # Visualization 2: readmission rates by testing status.
    ax = readmission_summary["Readmission_rate"].reindex(
        ["Tested", "Not tested"]
    ).plot(kind="bar", color=["#2E86AB", "#A23B72"], figsize=(7, 5))
    ax.set_title("30-Day Readmission Rate by HbA1c Testing Status")
    ax.set_xlabel("")
    ax.set_ylabel("Readmission rate (%)")
    ax.tick_params(axis="x", rotation=0)
    ax.set_ylim(0, max(readmission_summary["Readmission_rate"]) * 1.25)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f%%")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "hba1c_readmission_rate.png", dpi=200)
    plt.close()

    # Visualization 3: readmission rate by HbA1c result category.
    result_order = ["Norm", ">7", ">8", "Not tested"]
    ax = result_summary["Readmission_rate"].reindex(result_order).plot(
        kind="bar", color="#4C956C", figsize=(8, 5)
    )
    ax.set_title("30-Day Readmission Rate by HbA1c Result")
    ax.set_xlabel("")
    ax.set_ylabel("Readmission rate (%)")
    ax.tick_params(axis="x", rotation=0)
    ax.set_ylim(0, max(result_summary["Readmission_rate"]) * 1.25)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f%%")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "hba1c_result_readmission_rate.png", dpi=200)
    plt.close()

    print("Dataset shape:", df.shape)
    print("\nHbA1c testing summary:")
    print(testing_summary.round(2))
    print("\nReadmission summary:")
    print(readmission_summary.round(2))
    print("\nContingency table:")
    print(contingency_table)
    print("\nChi-square test:")
    print(f"Chi-square statistic: {chi2:.4f}")
    print(f"Degrees of freedom: {degrees_of_freedom}")
    print(f"p-value: {p_value:.4f}")
    print("\nConclusion at alpha = 0.05:")
    if p_value < 0.05:
        print("HbA1c testing status is statistically associated with 30-day readmission.")
    else:
        print("There is not enough evidence of an association with 30-day readmission.")
    print("This analysis shows association, not causation.")
    print(f"\nSaved tables and charts to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
