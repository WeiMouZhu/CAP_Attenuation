
###############################################################################
# Description:
# This script processes PhaseNet picks, filters and sorts them,
# It includes steps for:
# 1. Processing initial picks data
# 2. Filtering for valid P and S wave pairs
# 3. Expanding records to include all three components (BHE, BHN, BHZ) with .SAC extension
# 4. Copying relevant SAC files and PNG images to new directories
# CAP from 2012 to 2013
###############################################################################

import pandas as pd
import os
import shutil
import glob

# Read the CSV file
df = pd.read_csv('./CAP_4Pick_3SAC/results/picks.csv')

# Convert begin_time and phase_time to datetime objects
df['begin_time'] = pd.to_datetime(df['begin_time'])
df['phase_time'] = pd.to_datetime(df['phase_time'])

# Group by file_name and apply filtering conditions
def filter_group(group):
    # Check if at least one phase_score is greater than 0.3
    if not group[group['phase_score'] > 0.3].empty:
        result = []
        for phase in ['P', 'S']:
            phase_group = group[group['phase_type'] == phase]
            if not phase_group.empty:
                # Select the record with the highest phase_score
                result.append(phase_group.loc[phase_group['phase_score'].idxmax()])
        return pd.DataFrame(result)
    else:
        # If no records have phase_score greater than 0.3, return an empty DataFrame
        return pd.DataFrame()

# Apply the filtering function
filtered_df = df.groupby('file_name').apply(filter_group).reset_index(drop=True)

# Sort by begin_time, then by file_name and phase_time if begin_time is the same
filtered_df = filtered_df.sort_values(['begin_time', 'file_name', 'phase_time'])

# Convert datetime columns back to original string format, keeping three zeros at the end
filtered_df['begin_time'] = filtered_df['begin_time'].dt.strftime('%Y-%m-%dT%H:%M:%S.%f').str[:-3]
filtered_df['phase_time'] = filtered_df['phase_time'].dt.strftime('%Y-%m-%dT%H:%M:%S.%f').str[:-3]

# Select and order the required columns
columns_order = ['station_id', 'begin_time', 'phase_index', 'phase_time', 'phase_score', 'phase_type', 'file_name']
filtered_df = filtered_df[columns_order]

# Save the results to a new CSV file
filtered_df.to_csv('CAP_4Pick_3SAC/results/filtered_picks.csv', index=False)

print("Initial processing complete, results saved to CAP_4Pick_3SAC/results/filtered_picks.csv")
print(f"Number of records after initial processing: {len(filtered_df)}")

# Read the newly generated CSV file
df = pd.read_csv('CAP_4Pick_3SAC/results/filtered_picks.csv')

# For each file_name, check if both P and S phases exist, and P phase is before S phase
def check_ps(group):
    if set(group['phase_type']) != {'P', 'S'}:
        return False
    
    p_time = group[group['phase_type'] == 'P']['phase_time'].iloc[0]
    s_time = group[group['phase_type'] == 'S']['phase_time'].iloc[0]
    
    return pd.to_datetime(p_time) < pd.to_datetime(s_time)

# Apply filtering, keep only SAC records with both P and S phases, and P before S
final_df = df.groupby('file_name').filter(check_ps)

# Apply sorting logic again
final_df['begin_time'] = pd.to_datetime(final_df['begin_time'])
final_df['phase_time'] = pd.to_datetime(final_df['phase_time'])
final_df = final_df.sort_values(['begin_time', 'file_name', 'phase_time'])

# Convert datetime columns back to original string format
final_df['begin_time'] = final_df['begin_time'].dt.strftime('%Y-%m-%dT%H:%M:%S.%f').str[:-3]
final_df['phase_time'] = final_df['phase_time'].dt.strftime('%Y-%m-%dT%H:%M:%S.%f').str[:-3]

print("Final processing complete")
print(f"Number of records after final processing: {len(final_df)}")

# Function to expand file_name to three components
def expand_to_components(row):
    base_name = row['file_name'][:-3]  # Remove the last 'BH*'
    return pd.DataFrame({
        'station_id': [row['station_id']] * 3,
        'begin_time': [row['begin_time']] * 3,
        'phase_index': [row['phase_index']] * 3,
        'phase_time': [row['phase_time']] * 3,
        'phase_score': [row['phase_score']] * 3,
        'phase_type': [row['phase_type']] * 3,
        'file_name': [f"{base_name}BHE.SAC", f"{base_name}BHN.SAC", f"{base_name}BHZ.SAC"]
    })

# Apply the expansion function to each row and concatenate the results
expanded_df = pd.concat([expand_to_components(row) for _, row in final_df.iterrows()], ignore_index=True)

# Save the expanded results to a new CSV file
expanded_df.to_csv('CAP_4Pick_3SAC/results/final_filtered_picks.csv', index=False)

print("Expanded results saved to CAP_4Pick_3SAC/results/final_filtered_picks.csv")
print(f"Number of records in expanded results: {len(expanded_df)}")

# Create new directories
new_sac_dir = 'CAP_5Filter_3SAC'
new_figures_dir = os.path.join(new_sac_dir, 'figures')
os.makedirs(new_sac_dir, exist_ok=True)
os.makedirs(new_figures_dir, exist_ok=True)

# Copy SAC files and PNG images
copied_files = set()
copied_pngs = set()
for _, row in expanded_df.iterrows():
    file_name = row['file_name']
    
    # Copy SAC file
    if file_name not in copied_files:
        sac_src = os.path.join('CAP_4Pick_3SAC', file_name)
        sac_dst = os.path.join(new_sac_dir, file_name)
        if os.path.exists(sac_src):
            shutil.copy2(sac_src, sac_dst)
            print(f"Copied SAC file: {file_name}")
        else:
            print(f"SAC file not found: {file_name}")
        copied_files.add(file_name)
    
    # Copy PNG image (only once per event)
    base_name = file_name[:-7]  # Remove 'BH*.SAC'
    png_name = f"{base_name}BH*.png"
    if png_name not in copied_pngs:
        png_src = os.path.join('CAP_4Pick_3SAC', 'results', 'figures', png_name)
        png_files = glob.glob(png_src)
        if png_files:
            png_file = png_files[0]  # There should be only one matching file
            png_dst = os.path.join(new_figures_dir, os.path.basename(png_file))
            shutil.copy2(png_file, png_dst)
            print(f"Copied PNG file: {os.path.basename(png_file)}")
            copied_pngs.add(png_name)
        else:
            print(f"PNG file not found: {png_name}")

print(f"Copying complete. Copied {len(copied_files)} SAC files to {new_sac_dir} directory,")
print(f"and {len(copied_pngs)} PNG images to {new_figures_dir} directory.")
