"""
Data Cleaning & Wrangling — Diabetes 130-US Hospitals (1999-2008)
Structured to match the Week 6 Lab notebook sections:
1. Load the Data
2. Diagnose Data Quality Issues
3. Clean & Standardize Data
4. Handling Missing Data
5. Validate
"""

import pandas as pd
import numpy as np

# =====================================================================
# 1. Load the Data
# =====================================================================
DATA_DIR = ''  # change if the CSV is in a subfolder
diabetic_data = pd.read_csv(f'{DATA_DIR}diabetic_data.csv')

print('diabetic_data', diabetic_data.shape)
diabetic_data.head()


# =====================================================================
# 2. Diagnose Data Quality Issues
# =====================================================================
print(diabetic_data.head(3).to_string(index=False))
print(diabetic_data.info())
print('Duplicates (full rows):', diabetic_data.duplicated().sum())

# This dataset encodes missing values as the string '?', not blank/NaN,
# so .isna() alone would undercount missingness. Check for '?' directly.
missing_as_question_mark = (diabetic_data == '?').sum()
print('Columns with "?" as missing marker:\n',
      missing_as_question_mark[missing_as_question_mark > 0])

# Repeat encounters: some patients appear more than once
print('Unique patients:', diabetic_data['patient_nbr'].nunique())
print('Total encounters:', diabetic_data.shape[0])

# Unique values in key categoricals / target
print('readmitted values:', diabetic_data['readmitted'].unique())
print('gender values:', diabetic_data['gender'].unique())
print('race values:', diabetic_data['race'].unique())
print('age values:', sorted(diabetic_data['age'].unique()))

"""
Observations:
- Missing values are encoded as '?', not NaN
- weight, payer_code, medical_specialty are mostly missing (97%, 40%, 49%)
- race has a small number of '?' values
- Some patients have multiple encounters (101,766 rows, 71,518 unique patients)
- gender has an 'Unknown/Invalid' category (small N)
- Some encounters end in death/hospice (discharge_disposition_id) —
  these can't be "readmitted" and would bias the target
"""


# =====================================================================
# 3. Clean & Standardize Data
# =====================================================================
diabetic_clean = diabetic_data.copy()

# Replace '?' with actual NaN across the dataframe
diabetic_clean = diabetic_clean.replace('?', np.nan)

# Drop columns that are missing too much to use reliably
diabetic_clean = diabetic_clean.drop(columns=['weight', 'payer_code', 'medical_specialty'])

# Standardize categorical text (strip whitespace, consistent casing)
categorical_cols = ['race', 'gender', 'age', 'max_glu_serum', 'A1Cresult',
                     'change', 'diabetesMed', 'insulin']
for col in categorical_cols:
    diabetic_clean[col] = diabetic_clean[col].astype(str).str.strip()

# Drop encounters where the patient died or was discharged to hospice —
# they cannot be readmitted, so keeping them would distort the target
expired_or_hospice_codes = [11, 13, 14, 19, 20, 21]
diabetic_clean = diabetic_clean[~diabetic_clean['discharge_disposition_id'].isin(expired_or_hospice_codes)]

# Keep only the first encounter per patient, so one frequently-hospitalized
# patient doesn't dominate the analysis (standard practice for this dataset)
diabetic_clean = diabetic_clean.sort_values('encounter_id').drop_duplicates(
    subset='patient_nbr', keep='first'
)

# Identify duplicates after cleaning
print('duplicates after cleaning:', diabetic_clean.duplicated().sum())

diabetic_clean.head()

"""
Decisions made:
- Replaced '?' with NaN so missingness is handled consistently by pandas
- Dropped weight/payer_code/medical_specialty: too sparse to impute safely
- Standardized categorical text via strip (no case inconsistencies found,
  unlike the customers/orders lab data)
- Dropped expired/hospice discharges: not eligible for readmission
- Kept first encounter per patient only: avoids one patient's repeat visits
  skewing the readmission rate
"""


# =====================================================================
# 4. Handling Missing Data
# =====================================================================
print('Missing values after cleaning:\n', diabetic_clean.isna().sum()[diabetic_clean.isna().sum() > 0])

# race: small number missing, safe to drop those rows
diabetic_clean = diabetic_clean.dropna(subset=['race'])

# diag_1/2/3: small number missing, fill with 'Missing' category rather
# than dropping rows (keeps the diagnosis feature usable)
for col in ['diag_1', 'diag_2', 'diag_3']:
    diabetic_clean[col] = diabetic_clean[col].fillna('Missing')

# max_glu_serum / A1Cresult: NaN here doesn't mean "unknown" — it means
# the test was not ordered. Leave as-is and instead create explicit
# "was tested" flags rather than imputing a fake result.
# NOTE: comparing against the string 'nan' does not work here -- pandas'
# nullable string dtype keeps missing values as actual <NA>, even after
# .astype(str), so that comparison silently matched every row (bug found
# during review). Fixed by checking membership in the known result
# categories directly instead.
diabetic_clean['a1c_tested'] = diabetic_clean['A1Cresult'].isin(['>7', '>8', 'Norm']).astype(int)
diabetic_clean['glucose_tested'] = diabetic_clean['max_glu_serum'].isin(['>200', '>300', 'Norm']).astype(int)

print('Missing values remaining:\n', diabetic_clean.isna().sum()[diabetic_clean.isna().sum() > 0])

"""
Decisions made:
- Dropped rows missing race (small N, no reliable way to impute)
- Filled missing diag_1/2/3 with 'Missing' rather than dropping rows
  (only ~1% of rows affected, and dropping would lose otherwise-good data)
- Did NOT impute A1Cresult/max_glu_serum missingness — a missing lab
  result here means "not tested," which is itself meaningful, so it's
  captured as a flag (a1c_tested / glucose_tested) instead of guessing
  a value
"""


# =====================================================================
# 5. Validate
# =====================================================================
# Confirm no duplicate patients remain
print('Duplicate patients remaining:', diabetic_clean['patient_nbr'].duplicated().sum())

# Confirm target variable is clean
print('readmitted values after cleaning:', diabetic_clean['readmitted'].unique())

# Binarize target for the business question: readmitted within 30 days
diabetic_clean['readmitted_30d'] = (diabetic_clean['readmitted'] == '<30').astype(int)

print('\nFinal shape:', diabetic_clean.shape)
print('Readmitted within 30 days:', diabetic_clean['readmitted_30d'].sum(),
      f"({diabetic_clean['readmitted_30d'].mean():.1%})")

# Save cleaned file
diabetic_clean.to_csv(f'{DATA_DIR}diabetic_data_clean.csv', index=False)
print('\nSaved diabetic_data_clean.csv')
