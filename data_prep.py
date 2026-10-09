"""
Data preparation for the Diabetes Readmission Explorer.

The cleaning itself is done in Shivani's diabetes_data_corrected.py, which
creates diabetic_data_corrected.csv (68,071 patients). That script:
    - turns "?" into missing values
    - drops weight, payer_code and medical_specialty (mostly missing)
    - removes stays that ended in death or hospice (cannot be readmitted)
    - keeps only the first hospital stay for each patient
    - removes rows with missing race and fills missing diagnoses with "Missing"
    - adds a1c_tested (1 = HbA1c test done) and readmitted_30d (1 = back
      within 30 days)

This file loads that CSV, checks the two flags, and adds a few easy-to-read
columns the app uses:

    readmit_30       1 if the patient came back within 30 days, else 0
    testing_status   "Tested" or "Not tested"
    a1c_status       readable HbA1c result ("Not tested", "Normal (<7%)", ...)
    age_group        "70-79" instead of "[70-80)"
    primary_dx       diagnosis group for diag_1 (Circulatory, Diabetes, ...)
    prior_inpatient  hospital stays in the year before, capped at 5 ("5+")
    prior_emergency  emergency visits in the year before, capped at 3 ("3+")
    med_change       "Changed" or "Not changed"

Run this file directly to print a quick data check:
    python data_prep.py
"""

import os

import pandas as pd

# Build the path from this file's folder so the app finds the data no matter
# which folder it is started from (Streamlit Cloud starts from the repo root).
APP_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(APP_FOLDER, "diabetic_data_corrected.csv")

A1C_LABELS = {
    "Norm": "Normal (<7%)",
    ">7": "Elevated (7-8%)",
    ">8": "High (>8%)",
}
A1C_ORDER = ["Not tested", "Normal (<7%)", "Elevated (7-8%)", "High (>8%)"]

AGE_ORDER = ["0-9", "10-19", "20-29", "30-39", "40-49",
             "50-59", "60-69", "70-79", "80-89", "90-99"]

DX_ORDER = ["Circulatory", "Respiratory", "Digestive", "Diabetes", "Injury",
            "Musculoskeletal", "Genitourinary", "Other"]


def load_data(filepath=DATA_PATH):
    # In the cleaned file a blank A1Cresult means the test was not done.
    df = pd.read_csv(filepath, low_memory=False)
    return df


def check_flags(df):
    """Make sure the file uses the team's agreed definitions.

    a1c_tested should be 1 only when A1Cresult is Norm, >7 or >8, and
    readmitted_30d should be 1 only when readmitted is "<30". (An older
    version of the cleaned file had a1c_tested = 1 for every patient.)
    """
    expected_a1c = df["A1Cresult"].isin(["Norm", ">7", ">8"]).astype(int)
    expected_30d = (df["readmitted"] == "<30").astype(int)
    if not (df["a1c_tested"] == expected_a1c).all():
      raise ValueError("a1c_tested does not match A1Cresult. "
                         "Use the latest diabetic_data_corrected.csv.")
    if "readmitted_30d" in df.columns:
         if not df["readmitted_30d"].eq(expected_30d).all():
             raise ValueError("readmitted_30d does not match readmitted.")

def diagnosis_group(code):
    """Turn an ICD-9 code like '428' or '250.83' into a readable group."""
    if pd.isna(code) or code == "Missing":
        return "Other"
    code = str(code).strip()
    # V and E codes are supplementary codes, not a disease group
    if code.startswith("V") or code.startswith("E"):
        return "Other"
    number = float(code)
    if code.startswith("250"):
        return "Diabetes"
    if (390 <= number <= 459) or number == 785:
        return "Circulatory"
    if (460 <= number <= 519) or number == 786:
        return "Respiratory"
    if (520 <= number <= 579) or number == 787:
        return "Digestive"
    if 800 <= number <= 999:
        return "Injury"
    if 710 <= number <= 739:
        return "Musculoskeletal"
    if (580 <= number <= 629) or number == 788:
        return "Genitourinary"
    return "Other"


def age_label(age_text):
    """'[70-80)' -> '70-79'"""
    age_text = age_text.replace("[", "").replace(")", "")
    low, high = age_text.split("-")
    return low + "-" + str(int(high) - 1)


def add_app_columns(df):
    check_flags(df)
    df = df.copy()

   # Canonical app target:
   # 1 = readmitted within 30 days, 0 = otherwise
    df["readmit_30"] = (df["readmitted"] == "<30").astype(int)

    # HbA1c testing and result
    df["testing_status"] = "Not tested"
    df.loc[df["a1c_tested"] == 1, "testing_status"] = "Tested"
    df["a1c_status"] = df["A1Cresult"].map(A1C_LABELS).fillna("Not tested")

    # readable age groups
    df["age_group"] = df["age"].apply(age_label)

    # primary diagnosis group
    df["primary_dx"] = df["diag_1"].apply(diagnosis_group)

    # prior visits, with the rare high counts grouped together
    df["prior_inpatient"] = df["number_inpatient"].clip(upper=5)
    df["prior_emergency"] = df["number_emergency"].clip(upper=3)

    # medication change
    df["med_change"] = "Not changed"
    df.loc[df["change"] == "Ch", "med_change"] = "Changed"

    df = df.reset_index(drop=True)
    return df


if __name__ == "__main__":
    raw = load_data()
    print("Rows in diabetic_data_corrected.csv:", raw.shape)
    print("Duplicate patients:", raw["patient_nbr"].duplicated().sum())

    df = add_app_columns(raw)
    print("Flags match the agreed definitions.")
    print("30-day readmission rate:", round(df["readmit_30"].mean() * 100, 2), "%")
    print("HbA1c tested:", round((df["testing_status"] == "Tested").mean() * 100, 2), "%")
    print(df.groupby("testing_status")["readmit_30"].mean().mul(100).round(2))
