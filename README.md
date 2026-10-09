# Diabetes Readmission Explorer

An interactive Streamlit app that helps hospital staff explore patient groups and factors associated with higher 30-day readmission rates, including HbA1c testing, prior hospital visits, age, diagnosis, and medication changes.

BAN 601 - Project 1

## Business problem

Diabetic patients admitted to the hospital for any reason are often readmitted
within 30 days, and readmissions are expensive for hospitals. Yet only about
16.7% of patients in the complete data set, and 18.3% in the cleaned data set, data received an HbA1c test during their stay. In the
data, tested patients were readmitted somewhat less often (a correlation, not proof that testing causes the difference).

**Who uses the app:** The clinician who first takes the patient's case, such
as an internal medicine doctor, cardiologist, surgeon, general practitioner,
primary care physician, or endocrinologist.

**Questions the app answers:**

1. Are patients who get an HbA1c test readmitted less often than those who don't?
2. How is prior emergency-visit history associated with 30-day readmission?
3. Is the HbA1c test influenced by age?
4. For which primary diagnoses is testing linked to the biggest drop in readmissions?
5. What are common medication changes that can increase the risk of readmission?
6. How do the results of the HbA1c test -- Norm, >7, >8, and None -- influence 30-day readmission rates?
7. For a selected group, does the readmission rate justify the cost of the test?

## Dataset

**Diabetes 130-US Hospitals for Years 1999-2008**, UCI Machine Learning Repository
(CC BY 4.0): https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008

- Initial data: 101,766 hospital stays of diabetic patients, 50 columns
- Cleaned data: 68,071 hospital stays of diabetic patients, 50 columns 
- Numeric: time in hospital, lab procedures, procedures, diagnoses, prior
  out / emergency / in visits
- Categorical: race, gender, age group, diagnoses, HbA1c result, insulin,
  medication change, discharge type, readmission


diabetic_data_corrected.csv and IDS_mapping.csv are included in the repository root.
If they are missing, download the zip from the link above and put both CSV
files in the `data/` folder.

### Cleaning steps (`diabetes_data_cleaning.py`)

- Read `?` as missing and replaced it with a true missing value
- Dropped `weight` (~97% missing), `medical_specialty` (~49%) and `payer_code` (~40%), which were too sparse to use
- Removed stays that ended in death or hospice (discharge codes 11, 13, 14, 19, 20, 21), since those patients cannot be readmitted
- Kept only each patient's first stay (by `encounter_id`), so frequent visitors are not counted many times (71,518 unique patients in the original data)
- Dropped rows with a missing `race`; filled the few missing `diag_1`, `diag_2` and `diag_3` codes with a "Missing" category so those rows were kept
- Did not impute `A1Cresult` or `max_glu_serum`. A blank means the test was not performed, so we created flags instead: `a1c_tested` = 1 when the result is `>7`, `>8` or `Norm` (0 if not tested), and `glucose_tested` is coded the same way for `max_glu_serum`
- Target: readmit_30 = 1 when readmitted is <30, otherwise 0. The app creates this binary target from the original readmitted column.
- Result: 68,071 rows (one per patient), 12,465 tested (18.3%), 9.0% readmitted within 30 days

## The app

**Controls (sidebar):** count each  once (checkbox), HbA1c result,
age group, and primary diagnosis (multi-selects), hospital stays in the prior
year (slider), and medication change (radio buttons). Test and readmission
costs can be entered for the break-even check.

**Visualizations:**

1. 30-day readmission rate by HbA1c result
2. 30-day readmission rate by number of hospital stays in the prior year
3. Tested vs. untested readmission rate for each primary diagnosis

Plus key numbers at the top, a break-even check, and a filtered data table
you can download.

### What we found (first stay per patient , all filters open)

- 18.3% of s had an HbA1c test.
- Untested patients: 9.1% readmitted within 30 days, vs. 8.5% for the tested groups (p = 0.021). 
- Prior hospital stays are the strongest warning sign: 8.1% readmitted with no prior stays, 35.6% with 5 or more.
- The testing gap is largest when the main diagnosis is Diabetes (10.2% vs. 7.2%), Injury (11.3% vs. 7.3%), or Respiratory (7.7% vs. 5.6%).
  For Circulatory, Genitourinary, and Musculoskeletal stays,tested patients were readmitted slightly *more* often.
- The HbA1C test is a modest but real indicator of reduced readmission risk for diabetic patients (correlation not causation).
- Based on the dataset, The HbA1C test on average costs $15–50, while a readmission costs a hospital $10K–15K+ (and triggers CMS penalties). Even this smaller observed reduction in readmission rate would pay for the test many times over across a  population.
  #### HbA1c Testing and 30-Day Readmission Analysis
> **Important note:** These results are based on the cleaned dataset of 68,071  encounters and do not apply the first-stay-per- filter.
> 
- The cleaned dataset contained 68,071  encounters. HbA1c testing was recorded for 12,465 s (18.31%), while 55,606 s (81.69%) did not have a recorded HbA1c test.
- The 30-day readmission rate was 8.49% among tested patients and 9.15% among s who were not tested. This represents a difference of 0.66 percentage points.
- By HbA1c result, the readmission rates were 8.67% for `Norm`, 8.55% for `>7`, and 8.34% for `>8`. The not-tested group had the highest readmission rate at 9.15%.
- A chi-square test produced a p-value of 0.0213. Since this is less than 0.05, HbA1c testing status was statistically associated with 30-day readmission.
- This result shows an association, not causation. The analysis does not prove that HbA1c testing directly reduces readmission.

#### Business Recommendation

- The hospital should strengthen HbA1c testing and documentation for eligible s, particularly those without a recent HbA1c result.
- HbA1c testing status may be used as one indicator for identifying s who could benefit from diabetes education, medication review, and post-discharge follow-up.
- Because the observed difference was relatively small and this was an observational analysis, HbA1c testing should be combined with other factors, such as age, prior hospital visits, diagnoses, and medication history, when planning interventions.

  
## How to run

```bash
# 1. Clone the repo
git clone https://github.com/BretteFitzgibbon/Diabetes_Hospitalization_Readmission.git
cd Diabetes_Hospitalization_Readmission

# 2. Install the libraries
pip install -r requirements.txt

# 3. Start the app
streamlit run app.py
```

The app opens at http://localhost:8501. To check the cleaning step on its own, run `python data_prep.py`.

## Files

```
app.py            Streamlit app
diabetes_data_cleaning.py      Loading, cleaning, and new columns
requirements.txt  Python libraries
Data:
-- diabetic_data_corrected.csv
-- IDS_mapping.csv
Screenshots:
-- overview_and_filters.png
-- charts.png
-- break_even_check.png
-- filtered_med_changed.png 
```

## Screenshots

<img width="2160" height="1350" alt="image" src="https://github.com/user-attachments/assets/3211da8c-c4c5-44c8-9920-c1a6961a7f58" />

<img width="2160" height="1350" alt="image" src="https://github.com/user-attachments/assets/52ddfe4e-1fa0-4dde-9892-8f659f0e985c" />

<img width="2160" height="1350" alt="image" src="https://github.com/user-attachments/assets/5aa0a044-4a2e-41ed-9a42-38715538589a" />

<img width="2160" height="1350" alt="image" src="https://github.com/user-attachments/assets/6314f12a-a56c-4e6b-b2cc-9759def87c2a" />





