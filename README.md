# Diabetes Readmission Explorer

An interactive Streamlit app that helps hospital staff explore patient groups and factors associated with higher 30-day readmission rates, including HbA1c testing, prior hospital visits, age, diagnosis, and medication changes.

BAN 601 - Project 1

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://diabetesreadmission.streamlit.app)


## Business problem

Diabetic patients admitted to the hospital for any reason are often readmitted within 30 days, and readmissions are expensive for hospitals. Yet only about 16.7% of patients in the complete data set, and 18.3% in the cleaned data set, data received an HbA1c test during their stay. In the
data, tested patients were readmitted somewhat less often (a correlation, not proof that testing causes the difference).

**Who uses the app:** The clinician who first takes the patient's case, such
as an internal medicine doctor, cardiologist, surgeon, general practitioner,
primary care physician, or endocrinologist.

**Some questions the app answers:**

1. Are patients who get an HbA1c test readmitted less often than those who don't?
2. How do the results of the HbA1c test -- Norm, >7, >8, and None -- influence 30-day readmission rates?
3. Is the HbA1c test influenced by age?
4. How is prior emergency visit history associated with 30-day readmission?
5. For which primary diagnoses is testing linked to the biggest drop in readmissions?
6. Do medication changes increase the risk of readmission?
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

**Controls (sidebar):** HbA1c result, age group, and primary diagnosis (multi-selects), hospital stays in the prior
year (slider), and medication change (radio buttons). Test and readmission costs can be entered for the break-even check.

**Visualizations:**

* 30-day readmission rate by:
  
  -- Whether an HbA1c test was performed
  
  -- The result of the HbA1c test
  
  -- Prior inpatient stays
  
  -- Prior emergency visits
  
  -- Age group
  
  -- Medication change
  
  -- Primary diagnosis
    
* Prior hospital use by age group and readmission

* HbA1c testing rate by:
  
  -- Age group
  
  -- Primary diagnosis
    
* The largest tested vs. untested difference by primary diagnosis

Plus key numbers at the top, a break-even check, and a filtered data table
you can download.

### What we found

1. Are patients who get an HbA1c test readmitted less often than those who don't?
<img width="2560" height="1440" alt="Slide1" src="https://github.com/user-attachments/assets/da72c3b8-1f1e-458e-b283-3c6045da43fd" />
The 30-day readmission rate was 8.49% among tested patients and 9.15% among s who were not tested. This represents a difference of 0.66 percentage points.



2. How do the results of the HbA1c test -- Norm, >7, >8, and None -- influence 30-day readmission rates?
<img width="2560" height="1440" alt="Slide2" src="https://github.com/user-attachments/assets/624eba16-dfce-4f08-b56f-858c8acc158e" />
By HbA1c result, the readmission rates were 8.67% for `Norm`, 8.55% for `>7`, and 8.34% for `>8`. The not-tested group had the highest readmission rate at 9.15%.



3. Is the HbA1c test influenced by age?
<img width="2560" height="1440" alt="Slide3" src="https://github.com/user-attachments/assets/8116fbc7-fb3f-4238-96fc-a78d48d8a95c" />
There was a steady decline in HbA1c test administration based on the age of the patient. Children and adolescents were by far the most likely to receive a test. 



4. How is prior emergency visit history associated with 30-day readmission?
<img width="2560" height="1440" alt="Slide9" src="https://github.com/user-attachments/assets/ac34627f-7dc8-4451-9d6b-859c91a60362" />
There was a clear association between emergency visits in the prior year and 30-day readmission, with those who had had three or more emergency visits twice as liekly to be readmitted than those who had had no emergency visits.


   
5. For which primary diagnoses is testing linked to the biggest drop in readmissions?
<img width="2560" height="1440" alt="Slide4" src="https://github.com/user-attachments/assets/0c171b1d-362a-4e06-aca2-2c4bcf02fcd6" />
The testing gap is largest when the main diagnosis is Diabetes (10.1% vs. 7.2%), Injury (11.3% vs. 7.0%), or Respiratory (7.7% vs. 5.6%).
For Circulatory, Genitourinary, and Musculoskeletal stays, tested patients were readmitted slightly *more* often.



6. Do medication changes increase the risk of readmission?
<img width="2560" height="1440" alt="Slide6" src="https://github.com/user-attachments/assets/15f64cb3-7b7c-403c-931b-54bfd857fab2" />
Patients whose medication had been changed were slightly more likely to be readmitted. 


  
7. For a selected group, does the readmission rate justify the cost of the test?
<img width="2560" height="1440" alt="Slide7" src="https://github.com/user-attachments/assets/37f4284a-e76e-4f76-836a-c9874ad83c15" />
<img width="2560" height="1440" alt="Slide8" src="https://github.com/user-attachments/assets/a489828c-ccb3-4bc8-8917-0a52035c8173" />
While our overall consensus is that HbA1c testing should be increased, the economics can vary by age. For example, patients ages 10-19 were readmitted 5.32 percentage points more often if they had not received an HbA1c test, costing hospitals $798 per patient. In contrast, patients ages 90-99 were not readmitted less often, giving no cost case for testing. 

- Based on the dataset, The HbA1C test on average costs $15–50, while a readmission costs a hospital $10K–15K+ (and triggers CMS penalties). Even this smaller observed reduction in readmission rate would pay for the test many times over across a population.
  
- A chi-square test produced a p-value of 0.0213. Since this is less than 0.05, HbA1c testing status was statistically associated with 30-day readmission.
  
- The HbA1C test is a modest but real indicator of reduced readmission risk for diabetic patients (correlation not causation).


#### Business recommendation

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






