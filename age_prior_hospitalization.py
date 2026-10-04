# Analysis of the age of patients

# Setup
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os

import pandas as pd

# Build the path from this file's folder so the app finds the data no matter
# which folder it is started from (Streamlit Cloud starts from the repo root).
APP_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(APP_FOLDER, "diabetic_data_corrected.csv")


df = pd.read_csv("diabetic_data_corrected.csv")
# print(df)

# print(df.shape)


def analyze_hospitalization_by_age(dataframe):
    """
    Analyzes the average prior inpatient, outpatient, and emergency hospitalizations
    based on age group.

    Args:
        dataframe (pd.DataFrame): The input DataFrame containing 'age',
                                  'number_outpatient', 'number_emergency', and
                                  'number_inpatient' columns.

    Returns:
        pd.DataFrame: A DataFrame showing the average number of visits grouped by 'age'.
    """
    hospitalization_metrics = ['number_outpatient',
                               'number_emergency', 'number_inpatient']
    avg_visits_by_age = dataframe.groupby(
        'age')[hospitalization_metrics].mean()
    return avg_visits_by_age


# Get the DataFrame from the function call
avg_visits_by_age_df = analyze_hospitalization_by_age(df)

# Reset index to make 'age' a column for plotting
avg_visits_by_age_df = avg_visits_by_age_df.reset_index()

# Melt the DataFrame to long format for easier plotting with seaborn
hospitalization_age_melted = avg_visits_by_age_df.melt(
    id_vars='age', var_name='Visit_Type', value_name='Average_Count')

# Create the grouped bar chart
plt.figure(figsize=(14, 7))
sns.barplot(x='age', y='Average_Count', hue='Visit_Type',
            data=hospitalization_age_melted, palette='muted')
plt.title('Average Hospitalization Visits by Age Group')
plt.xlabel('Age Group')
plt.ylabel('Average Number of Visits')
plt.legend(title='Visit Type')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for readability
plt.tight_layout()  # Adjust layout
plt.show()

# Dterminantion of the correlationship between age, number of outpatient, inpatient and emergency visits

hospitalization_cols = ['age', 'number_outpatient',
                        'number_emergency', 'number_inpatient']

# Create a copy to avoid SettingWithCopyWarning if 'age' needs mapping
df_corr = df[hospitalization_cols].copy()

# For correlation calculation, we need numerical representation of 'age'
# We can map age groups to their midpoints or simply convert them to ordered categories
# For simplicity, let's map them to a numerical representation based on their order.
age_mapping = {age_group: i for i, age_group in enumerate(
    sorted(df_corr['age'].unique()))}
df_corr['age_numeric'] = df_corr['age'].map(age_mapping)

# Calculate the correlation matrix using the numerical age and hospitalization metrics
correlation_matrix = df_corr[[
    'age_numeric', 'number_outpatient', 'number_emergency', 'number_inpatient']].corr()

print("Correlation Matrix between Age (numeric) and Hospitalization Metrics:")
print(correlation_matrix)


plt.figure(figsize=(8, 6))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
plt.title('Correlation Matrix: Age (Numeric) vs. Hospitalization Metrics')
plt.show()
