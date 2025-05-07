import pandas as pd
import numpy as np
from datetime import datetime

# Load the Excel files
plda_file = "PLDA2025.xlsx"
stats_file = "Statistics_2025.xlsx"

# Read the PLDA2025 Excel file with date parsing
plda_df = pd.read_excel(plda_file, header=2)  # Row 3 contains dates
plda_df = plda_df.iloc[3:]  # Skip to row 6 (names start at A6)
plda_df = plda_df.rename(columns={plda_df.columns[0]: 'Name'})  # Rename first column to 'Name'

# Read the Statistics_2025 Excel file with date parsing
stats_df = pd.read_excel(stats_file, header=2)  # Row 3 contains dates
stats_df = stats_df.iloc[3:]  # Skip to row 6 (names start at A6)
stats_df = stats_df.rename(columns={stats_df.columns[0]: 'Name'})  # Rename first column to 'Name'

# Reset index for both dataframes
plda_df = plda_df.reset_index(drop=True)
stats_df = stats_df.reset_index(drop=True)

# Preserve original date format
date_columns_plda = plda_df.columns[1:]
date_columns_stats = stats_df.columns[1:]

# Convert to long format for merging
plda_melted = pd.melt(plda_df, id_vars=['Name'], var_name='Date', value_name='PLDA_Value')
stats_melted = pd.melt(stats_df, id_vars=['Name'], var_name='Date', value_name='Stats_Value')

# Merge the dataframes on Name and Date
merged_df = pd.merge(plda_melted, stats_melted, on=['Name', 'Date'], how='outer')

# Sum the values from both files (treating NaN as 0)
merged_df['PLDA_Value'] = merged_df['PLDA_Value'].fillna(0)
merged_df['Stats_Value'] = merged_df['Stats_Value'].fillna(0)
merged_df['Combined_Value'] = merged_df['PLDA_Value'] + merged_df['Stats_Value']

# Create pivot tables for each type of data
plda_pivot = merged_df.pivot_table(index='Name', columns='Date', values='PLDA_Value', fill_value=0)
stats_pivot = merged_df.pivot_table(index='Name', columns='Date', values='Stats_Value', fill_value=0)
combined_pivot = merged_df.pivot_table(index='Name', columns='Date', values='Combined_Value', fill_value=0)

# Create a new Excel file with all data
with pd.ExcelWriter('Merged_Data.xlsx', engine='openpyxl', date_format='dd/mm/yyyy') as writer:
    # Write the PLDA data
    plda_pivot.to_excel(writer, sheet_name='PLDA_Data')
    
    # Write the Statistics data
    stats_pivot.to_excel(writer, sheet_name='Stats_Data')
    
    # Write the combined (summed) data
    combined_pivot.to_excel(writer, sheet_name='Combined_Data')
    
    # Format the sheets to match the original layout
    workbook = writer.book
    
    # For each sheet, adjust the layout to match the original files
    for sheet_name in writer.sheets:
        worksheet = writer.sheets[sheet_name]
        
        # Add header rows to mimic original layout
        worksheet.insert_rows(1, 3)  # Insert 3 rows at the top
        
        # Add 'Date' in row 3
        for col_idx, col_name in enumerate(plda_pivot.columns, start=2):
            worksheet.cell(row=3, column=col_idx).value = col_name

print("Merged data has been saved to 'Merged_Data.xlsx'")