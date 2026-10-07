"""
Diabetes Readmission Explorer
Streamlit app for BAN 601 - Project 1

Data: diabetic_data_corrected.csv (cleaned by diabetes_data_corrected.py),
loaded and labeled by data_prep.py.

Run with:
    streamlit run app.py
"""

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from scipy.stats import chi2_contingency

from data_prep import (A1C_ORDER, AGE_ORDER, DX_ORDER, add_app_columns,
                       load_data)

st.set_page_config(page_title="Diabetes Readmission Explorer",
                   layout="wide")

# Chart colors (kept the same across every chart so a color always means
# the same thing: orange = not tested, blue = tested)
BLUE = "#2a78d6"
ORANGE = "#eb6834"
VIOLET = "#4a3aa7"
# colors for the three prior-visit types (outpatient, emergency, inpatient)
VISIT_COLORS = ["#1baf7a", "#eda100", "#4a3aa7"]
TEXT = "#52514e"
GRID = "#e4e3df"

MIN_GROUP_SIZE = 30  # hide bars based on fewer patients than this

# A1Cresult codes as they appear in the dataset, with a plain-English note
A1C_CODE = {
    "Normal (<7%)": "Norm (under 7%)",
    "Elevated (7-8%)": ">7 (7-8%)",
    "High (>8%)": ">8 (over 8%)",
    "Not tested": "None (not tested)",
}
# order the team asked for: Norm, >7, >8, None
A1C_CODE_ORDER = ["Normal (<7%)", "Elevated (7-8%)", "High (>8%)", "Not tested"]

TESTING_ORDER = ["Tested", "Not tested"]


# ------------------------------------------------------------------
# Load data (cached so it only runs once)
# ------------------------------------------------------------------
@st.cache_data
def get_data():
    raw = load_data()
    return add_app_columns(raw)


df_all = get_data()


# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------
def readmit_rate_table(data, group_col, order):
    """Patients and 30-day readmission rate (%) for each group."""
    table = data.groupby(group_col)["readmit_30"].agg(["size", "mean"])
    table.columns = ["patients", "rate"]
    table["rate"] = table["rate"] * 100
    table = table.reindex([g for g in order if g in table.index])
    return table


def summary_table(data, group_col, order, labels, label_name):
    """Patients, share of patients, readmissions and readmission rate per group."""
    table = data.groupby(group_col)["readmit_30"].agg(["size", "sum", "mean"])
    table = table.reindex([g for g in order if g in table.index])
    out = pd.DataFrame({
        label_name: [labels[g] for g in table.index],
        "Patients": table["size"].map("{:,}".format),
        "% of all": (table["size"] / len(data) * 100).map("{:.2f}%".format),
        "Readmitted (30 days)": table["sum"].map("{:,}".format),
        "Readmission rate": (table["mean"] * 100).map("{:.2f}%".format),
    })
    return out


def testing_rate_table(data, group_col, order):
    """Patients and HbA1c testing rate (%) for each group."""
    data = data.assign(is_tested=(data["testing_status"] == "Tested"))
    table = data.groupby(group_col)["is_tested"].agg(["size", "mean"])
    table.columns = ["patients", "rate"]
    table["rate"] = table["rate"] * 100
    table = table.reindex([g for g in order if g in table.index])
    return table


def style_axes(ax, ylabel):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=TEXT, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_ylabel(ylabel, color=TEXT)


def label_bars(ax, bars, fmt="{:.1f}%"):
    top = ax.get_ylim()[1]
    tallest = max([b.get_height() for b in bars if not pd.isna(b.get_height())] + [0])
    ax.set_ylim(0, max(top, tallest * 1.15))
    for bar in bars:
        height = bar.get_height()
        if pd.isna(height):
            continue
        ax.annotate(fmt.format(height),
                    (bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9, color=TEXT)


def simple_bar_chart(labels, values, color, ylabel, xlabel="", size=(6, 3.6),
                     fmt="{:.1f}%"):
    """One bar per group, with the value printed on top of each bar."""
    fig, ax = plt.subplots(figsize=size)
    bars = ax.bar(labels, values, color=color, width=0.6)
    label_bars(ax, bars, fmt)
    style_axes(ax, ylabel)
    if xlabel:
        ax.set_xlabel(xlabel, color=TEXT)
    st.pyplot(fig)
    plt.close(fig)


def tested_colors(groups):
    """Orange for 'Not tested', blue for everything else."""
    colors = []
    for group in groups:
        if group == "Not tested":
            colors.append(ORANGE)
        else:
            colors.append(BLUE)
    return colors


# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------
st.title("Diabetes Readmission Explorer")
st.markdown(
    "**Identify patient groups and factors associated with higher 30-day "
    "readmission risk, and see whether HbA1c testing may be useful.** "
    "Diabetic patients admitted to the hospital for any reason are often "
    "readmitted within 30 days, and readmissions are costly for hospitals. "
    "Only about 18% of patients in this data had an HbA1c (blood sugar) test."
)
st.caption(
    "Data: UCI Diabetes 130-US Hospitals, 1999-2008, cleaned by the team "
    "(68,071 patients, first hospital stay per patient; patients who died or "
    "were sent to hospice are excluded). These are associations, not proof "
    "that testing causes fewer readmissions."
)

# ------------------------------------------------------------------
# Sidebar controls
# ------------------------------------------------------------------
st.sidebar.header("Filter patients")
st.sidebar.caption("Each patient is counted once (their first hospital stay).")

a1c_choice = st.sidebar.multiselect(
    "HbA1c test result (A1Cresult)", A1C_ORDER, default=A1C_ORDER,
    format_func=lambda status: A1C_CODE[status],
    help="'None' means no HbA1c test was done during the stay.")

age_choice = st.sidebar.multiselect(
    "Age group", AGE_ORDER, default=AGE_ORDER)

dx_choice = st.sidebar.multiselect(
    "Primary diagnosis (reason for the stay)", DX_ORDER, default=DX_ORDER)

inpatient_range = st.sidebar.slider(
    "Hospital stays in the prior year", min_value=0, max_value=5,
    value=(0, 5), help="5 means 5 or more stays.")

med_choice = st.sidebar.radio(
    "Diabetes medication changed during stay?",
    ["All patients", "Changed", "Not changed"])

# Apply the filters
df = df_all.copy()
df = df[df["a1c_status"].isin(a1c_choice)]
df = df[df["age_group"].isin(age_choice)]
df = df[df["primary_dx"].isin(dx_choice)]
df = df[(df["prior_inpatient"] >= inpatient_range[0]) &
        (df["prior_inpatient"] <= inpatient_range[1])]
if med_choice != "All patients":
    df = df[df["med_change"] == med_choice]

if len(df) == 0:
    st.warning("No patients match these filters. Try selecting more options "
               "in the sidebar.")
    st.stop()

tested = df[df["testing_status"] == "Tested"]
not_tested = df[df["testing_status"] == "Not tested"]
both_groups = len(tested) >= MIN_GROUP_SIZE and len(not_tested) >= MIN_GROUP_SIZE

# ------------------------------------------------------------------
# 1. Overview (key numbers)
# ------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Patients in selection", f"{len(df):,}")
col2.metric("30-day readmission rate", f"{df['readmit_30'].mean() * 100:.2f}%")
col3.metric("Had an HbA1c test", f"{len(tested) / len(df) * 100:.2f}%")
if len(tested) > 0 and len(not_tested) > 0:
    gap = (not_tested["readmit_30"].mean() - tested["readmit_30"].mean()) * 100
    col4.metric("Gap: untested vs. tested",
                f"{gap:+.2f} pts",
                help="Positive means untested patients came back more often.")
else:
    col4.metric("Gap: untested vs. tested", "n/a",
                help="Select both tested and untested patients to compare.")

tab_a1c, tab_risk, tab_patterns, tab_business = st.tabs([
    "HbA1c analysis",
    "Patient risk factors",
    "HbA1c testing patterns",
    "Business recommendation",
])

# ------------------------------------------------------------------
# 2. HbA1c analysis
# ------------------------------------------------------------------
with tab_a1c:
    st.subheader("HbA1c testing: tested vs. not tested")
    st.caption("How many patients had an HbA1c test, and how often each group "
               "was readmitted within 30 days.")

    left, right = st.columns([1.4, 1])
    with left:
        test_table = summary_table(df, "testing_status", TESTING_ORDER,
                                   {"Tested": "Tested", "Not tested": "Not tested"},
                                   "HbA1c testing")
        st.dataframe(test_table, hide_index=True, width="stretch")
        st.caption("'Tested' = A1Cresult is Norm, >7, or >8. "
                   "'Not tested' = A1Cresult is None.")

        # Chi-square test: is testing status associated with readmission?
        if both_groups:
            counts = pd.crosstab(df["testing_status"], df["readmit_30"])
            chi2, p_value, dof, expected = chi2_contingency(counts)
            if p_value < 0.05:
                result = ("statistically associated with 30-day readmission "
                          "at the 5% level")
            else:
                result = ("not statistically associated with 30-day "
                          "readmission at the 5% level")
            st.markdown(f"**Chi-square test:** p-value = {p_value:.4f}. "
                        f"For the patients selected, HbA1c testing status is "
                        f"{result}.")
            st.caption("An association does not prove that testing causes "
                       "fewer readmissions.")

    with right:
        test_rates = readmit_rate_table(df, "testing_status", TESTING_ORDER)
        test_rates = test_rates[test_rates["patients"] >= MIN_GROUP_SIZE]
        if len(test_rates) > 0:
            simple_bar_chart(test_rates.index, test_rates["rate"],
                             tested_colors(test_rates.index),
                             "Readmitted within 30 days (%)", fmt="{:.2f}%")

    st.subheader("Breakdown by HbA1c result (A1Cresult)")
    st.caption("Patients and 30-day readmission rate for each HbA1c result: "
               "Norm, >7, >8, and None.")

    left, right = st.columns([1.4, 1])
    with left:
        a1c_summary = summary_table(df, "a1c_status", A1C_CODE_ORDER, A1C_CODE,
                                    "HbA1c result (A1Cresult)")
        st.dataframe(a1c_summary, hide_index=True, width="stretch")

    with right:
        a1c_table = readmit_rate_table(df, "a1c_status", A1C_CODE_ORDER)
        a1c_table = a1c_table[a1c_table["patients"] >= MIN_GROUP_SIZE]
        if len(a1c_table) > 0:
            bar_labels = [A1C_CODE[s].replace(" (", "\n(") for s in a1c_table.index]
            simple_bar_chart(bar_labels, a1c_table["rate"],
                             tested_colors(a1c_table.index),
                             "Readmitted within 30 days (%)", fmt="{:.2f}%")

    st.caption("Orange = not tested, blue = tested. "
               "Bars with fewer than 30 patients are hidden.")

# ------------------------------------------------------------------
# 3. Patient risk factors
# ------------------------------------------------------------------
with tab_risk:
    st.caption("Share of patients readmitted within 30 days for different "
               "patient groups. Bars with fewer than 30 patients are hidden.")

    # Prior inpatient stays and prior emergency visits
    left, right = st.columns(2)
    with left:
        st.subheader("Prior inpatient stays and 30-day readmission")
        visit_table = readmit_rate_table(df, "prior_inpatient", [0, 1, 2, 3, 4, 5])
        visit_table = visit_table[visit_table["patients"] >= MIN_GROUP_SIZE]
        labels = ["5+" if v == 5 else str(v) for v in visit_table.index]
        simple_bar_chart(labels, visit_table["rate"], VIOLET,
                         "Readmitted within 30 days (%)",
                         xlabel="Hospital stays in the prior year")

    with right:
        st.subheader("Prior emergency visits and 30-day readmission")
        er_table = readmit_rate_table(df, "prior_emergency", [0, 1, 2, 3])
        er_table = er_table[er_table["patients"] >= MIN_GROUP_SIZE]
        labels = ["3+" if v == 3 else str(v) for v in er_table.index]
        simple_bar_chart(labels, er_table["rate"], VIOLET,
                         "Readmitted within 30 days (%)",
                         xlabel="Emergency visits in the prior year")
        st.caption("number_emergency counts emergency visits in the year "
                   "before this stay. It does not show where a future "
                   "readmission happened.")

    # Age group and medication change
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Age group and 30-day readmission")
        age_table = readmit_rate_table(df, "age_group", AGE_ORDER)
        age_table = age_table[age_table["patients"] >= MIN_GROUP_SIZE]
        simple_bar_chart(age_table.index, age_table["rate"], VIOLET,
                         "Readmitted within 30 days (%)", xlabel="Age group",
                         size=(8, 3.6))

    with right:
        st.subheader("Medication change and 30-day readmission")
        med_table = readmit_rate_table(df, "med_change", ["Changed", "Not changed"])
        med_table = med_table[med_table["patients"] >= MIN_GROUP_SIZE]
        simple_bar_chart(med_table.index, med_table["rate"], VIOLET,
                         "Readmitted within 30 days (%)", size=(4, 3.6))

    # Primary diagnosis: tested vs not tested
    st.subheader("Primary diagnosis: tested vs. untested readmission")
    st.caption("30-day readmission rate for tested vs. untested patients, "
               "split by the main reason for the hospital stay.")

    by_dx = df.groupby(["primary_dx", "testing_status"])["readmit_30"].agg(["size", "mean"])
    by_dx = by_dx.reset_index()
    by_dx = by_dx[by_dx["size"] >= MIN_GROUP_SIZE]
    by_dx["rate"] = by_dx["mean"] * 100
    rates = by_dx.pivot(index="primary_dx", columns="testing_status", values="rate")
    rates = rates.reindex([d for d in DX_ORDER if d in rates.index])

    if len(rates) == 0:
        st.info("Not enough patients in this selection to compare diagnoses.")
    else:
        fig, ax = plt.subplots(figsize=(12, 4))
        positions = range(len(rates))
        width = 0.38
        if "Not tested" in rates.columns:
            bars = ax.bar([p - width / 2 for p in positions], rates["Not tested"],
                          width=width, color=ORANGE, label="Not tested")
            label_bars(ax, bars)
        if "Tested" in rates.columns:
            bars = ax.bar([p + width / 2 for p in positions], rates["Tested"],
                          width=width, color=BLUE, label="Tested")
            label_bars(ax, bars)
        ax.set_xticks(list(positions))
        ax.set_xticklabels(rates.index)
        style_axes(ax, "Readmitted within 30 days (%)")
        ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
        st.pyplot(fig)
        plt.close(fig)
        st.caption("Look for diagnoses where the blue bar is clearly lower "
                   "than the orange bar.")

    # Prior visits by age group and by readmission (Dickson's analysis)
    st.subheader("Prior hospital use by age group and readmission")
    st.caption("Average number of outpatient, emergency, and inpatient visits "
               "in the year before the stay.")

    visit_cols = ["number_outpatient", "number_emergency", "number_inpatient"]
    visit_names = ["Outpatient", "Emergency", "Inpatient"]

    def grouped_visit_chart(avg_table, xlabel, size):
        fig, ax = plt.subplots(figsize=size)
        positions = list(range(len(avg_table)))
        width = 0.27
        for i, col in enumerate(visit_cols):
            ax.bar([p + (i - 1) * width for p in positions], avg_table[col],
                   width=width, color=VISIT_COLORS[i], label=visit_names[i])
        ax.set_xticks(positions)
        ax.set_xticklabels(avg_table.index)
        style_axes(ax, "Average visits per patient")
        ax.set_xlabel(xlabel, color=TEXT)
        ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3)
        st.pyplot(fig)
        plt.close(fig)

    left, right = st.columns([1.4, 1])
    with left:
        age_counts = df["age_group"].value_counts()
        big_ages = [a for a in AGE_ORDER if age_counts.get(a, 0) >= MIN_GROUP_SIZE]
        avg_by_age = df.groupby("age_group")[visit_cols].mean().reindex(big_ages)
        if len(avg_by_age) > 0:
            grouped_visit_chart(avg_by_age, "Age group", (7, 3.8))

    with right:
        readmit_label = df["readmit_30"].map({1: "Within 30 days",
                                              0: "Not within 30 days"})
        avg_by_readmit = df.groupby(readmit_label)[visit_cols].mean()
        avg_by_readmit = avg_by_readmit.reindex(
            [g for g in ["Within 30 days", "Not within 30 days"]
             if g in avg_by_readmit.index])
        grouped_visit_chart(avg_by_readmit, "Readmitted", (5, 3.8))

    with st.expander("View these averages as a table"):
        table = df.groupby("age_group")[visit_cols].mean().reindex(big_ages)
        table.columns = visit_names
        st.dataframe(table.round(2), width="stretch")

# ------------------------------------------------------------------
# 4. HbA1c testing patterns
# ------------------------------------------------------------------
with tab_patterns:
    st.caption("Who gets an HbA1c test? Share of patients tested in each "
               "group. Bars with fewer than 30 patients are hidden.")

    left, right = st.columns(2)
    with left:
        st.subheader("HbA1c testing rate by age group")
        age_test = testing_rate_table(df, "age_group", AGE_ORDER)
        age_test = age_test[age_test["patients"] >= MIN_GROUP_SIZE]
        simple_bar_chart(age_test.index, age_test["rate"], BLUE,
                         "Patients tested (%)", xlabel="Age group")

    with right:
        st.subheader("HbA1c testing rate by primary diagnosis")
        dx_test = testing_rate_table(df, "primary_dx", DX_ORDER)
        dx_test = dx_test[dx_test["patients"] >= MIN_GROUP_SIZE]
        fig, ax = plt.subplots(figsize=(6, 3.6))
        bars = ax.bar(dx_test.index, dx_test["rate"], color=BLUE, width=0.6)
        label_bars(ax, bars)
        style_axes(ax, "Patients tested (%)")
        ax.tick_params(axis="x", labelsize=8, rotation=30)
        st.pyplot(fig)
        plt.close(fig)

    st.subheader("Which diagnoses show the largest tested vs. untested difference?")
    if len(rates) > 0 and "Tested" in rates.columns and "Not tested" in rates.columns:
        diff_table = rates.dropna().copy()
        diff_table["Difference (pts)"] = diff_table["Not tested"] - diff_table["Tested"]
        diff_table = diff_table.sort_values("Difference (pts)", ascending=False)
        diff_table = diff_table.reset_index()
        diff_table.columns = ["Primary diagnosis", "Not tested rate (%)",
                              "Tested rate (%)", "Difference (pts)"]
        st.dataframe(diff_table.round(2), hide_index=True, width="stretch")
        st.caption("Difference = untested rate minus tested rate. A positive "
                   "number means untested patients were readmitted more often. "
                   "Diagnoses with fewer than 30 patients in either group are "
                   "left out.")
    else:
        st.info("Select both tested and untested patients to compare diagnoses.")

# ------------------------------------------------------------------
# 5. Business recommendation (break-even check)
# ------------------------------------------------------------------
with tab_business:
    st.subheader("Does testing make economic sense for this group?")
    st.markdown(
        "Enter your hospital's own costs. The app compares the cost of one test "
        "with the readmission cost that *might* be avoided, based on the "
        "readmission gap for the patients currently selected."
    )
    st.caption("The default costs below are assumptions for illustration, not "
               "values from the dataset.")

    cost_col1, cost_col2 = st.columns(2)
    test_cost = cost_col1.number_input(
        "Cost of one HbA1c test ($)", min_value=0, value=50, step=5,
        help="Assumed value. Replace with your hospital's actual cost.")
    readmit_cost = cost_col2.number_input(
        "Cost of one readmission ($)", min_value=0, value=15000, step=500,
        help="Assumed value. Replace with your hospital's actual cost.")

    if both_groups:
        gap_share = not_tested["readmit_30"].mean() - tested["readmit_30"].mean()
        savings_per_test = gap_share * readmit_cost
        if gap_share <= 0:
            st.info("In this selection, tested patients were **not** readmitted "
                    "less often, so the data gives no cost case for testing here.")
        elif savings_per_test >= test_cost:
            st.success(
                f"Untested patients were readmitted {gap_share * 100:.2f} "
                f"percentage points more often. At these costs that is about "
                f"**\\${savings_per_test:,.0f} of readmission cost per patient**, "
                f"more than the \\${test_cost:,} test.")
        else:
            st.warning(
                f"The readmission gap ({gap_share * 100:.2f} points) is worth about "
                f"\\${savings_per_test:,.0f} per patient, less than the "
                f"\\${test_cost:,} test.")
        st.caption("This is a rough screening check. The gap is an association: "
                   "tested patients may differ in other ways, so testing alone "
                   "may not produce the full saving.")
    else:
        st.info("Select both tested and untested patients (at least 30 of each) "
                "to run the break-even check.")

    st.subheader("Recommendation")
    st.markdown(
        """
- Strengthen HbA1c testing and documentation for eligible diabetic patients,
  especially those without a recent HbA1c result.
- Use HbA1c testing status as **one** indicator for patients who could benefit
  from diabetes education, medication review, and follow-up after discharge.
- The tested vs. untested difference is small and this is observational data,
  so consider HbA1c testing together with other risk factors, such as prior
  hospital stays, prior emergency visits, age, diagnosis, and medication
  changes.
        """
    )

# ------------------------------------------------------------------
# Data table and notes
# ------------------------------------------------------------------
with st.expander("View the filtered data"):
    show_cols = ["age_group", "gender", "race", "primary_dx", "a1c_status",
                 "prior_inpatient", "number_emergency", "time_in_hospital",
                 "med_change", "insulin", "readmitted"]
    st.dataframe(df[show_cols].head(500), width="stretch")
    st.caption(f"Showing the first 500 of {len(df):,} rows.")
    st.download_button("Download filtered data (CSV)",
                       df[show_cols].to_csv(index=False),
                       file_name="filtered_patients.csv", mime="text/csv")

with st.expander("About the data and definitions"):
    st.markdown(
        """
- **Source:** UCI Machine Learning Repository, *Diabetes 130-US Hospitals
  for Years 1999-2008* (101,766 hospital stays of diabetic patients).
- **Cleaned data:** `diabetic_data_corrected.csv`, 68,071 patients. Each
  patient's first stay only; stays that ended in death or hospice removed;
  rows with missing race removed.
- **30-day readmission:** the `readmitted` column equals `<30`. Readmissions
  after 30 days (`>30`) and no readmission (`NO`) both count as "not
  readmitted".
- **HbA1c test:** `A1Cresult`. "None" means no test was done.
  Norm is under 7%, >7 is 7-8%, >8 is over 8%.
- **Primary diagnosis:** ICD-9 code in `diag_1`, grouped into Circulatory
  (390-459, 785), Respiratory (460-519, 786), Digestive (520-579, 787),
  Diabetes (250.xx), Injury (800-999), Musculoskeletal (710-739),
  Genitourinary (580-629, 788), and Other.
- **Costs** in the break-even check are user-entered assumptions.
        """
    )
