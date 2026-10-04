# Setup
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os

import pandas as pd

df = pd.read_csv("diabetic_data_corrected.csv")


def analyze_readmission_vs_hospital_visits(dataframe):
    """
    Analyzes the average prior outpatient, emergency, and inpatient visits
    based on readmission status.

    Args:
        dataframe (pd.DataFrame): The input DataFrame containing 'readmitted',
                                  'number_outpatient', 'number_emergency', and
                                  'number_inpatient' columns.

    Returns:
        pd.DataFrame: A DataFrame showing the average number of visits grouped by 'readmitted' status.
    """
    hospitalization_metrics = ['number_outpatient',
                               'number_emergency', 'number_inpatient']
    avg_visits_by_readmitted = dataframe.groupby(
        'readmitted')[hospitalization_metrics].mean()
    return avg_visits_by_readmitted


# Demonstrate the use of the function
print("Average Hospitalization Visits by Readmitted Status:")
avg_visits_by_readmitted_df = analyze_readmission_vs_hospital_visits(df)
print(avg_visits_by_readmitted_df)

# Melt the DataFrame to long format for easier plotting with seaborn
hospitalization_readmitted_melted = avg_visits_by_readmitted_df.reset_index().melt(
    id_vars='readmitted',
    var_name='Visit_Type',
    value_name='Average_Count'
)

# Create the grouped bar chart
plt.figure(figsize=(12, 7))
sns.barplot(x='readmitted', y='Average_Count', hue='Visit_Type',
            data=hospitalization_readmitted_melted, palette='tab10')
plt.title('Average Hospitalization Visits by Readmitted Status')
plt.xlabel('Readmitted Status')
plt.ylabel('Average Number of Visits')
plt.legend(title='Visit Type')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()


# time in hopital as a function of outpatient, inpatient and emergency visits
# Calculate the average time_in_hospital for each readmitted status
avg_time_by_readmitted = df.groupby(
    'readmitted')['time_in_hospital'].mean().reset_index()

print("Average Time in Hospital by Readmitted Status:")
print(avg_time_by_readmitted)

# Create a bar plot to visualize the relationship
plt.figure(figsize=(8, 6))
sns.barplot(x='readmitted', y='time_in_hospital',
            data=avg_time_by_readmitted, palette='viridis')
plt.title('Average Time in Hospital by Readmitted Status')
plt.xlabel('Readmitted Status')
plt.ylabel('Average Time in Hospital (Days)')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()
