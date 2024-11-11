import pandas as pd  
from obspy import read  
import os  
import shutil  

# Read the filtered_picks.csv file  
df = pd.read_csv('CAP_5Filter_3SAC/final_filtered_picks.csv')  

# Convert begin_time and phase_time to datetime objects  
df['begin_time'] = pd.to_datetime(df['begin_time'])  
df['phase_time'] = pd.to_datetime(df['phase_time'])  

# Calculate time differences in seconds  
df['time_diff'] = (df['phase_time'] - df['begin_time']).dt.total_seconds().astype(float)  

# Separate P and S waves into different dataframes  
df_p = df[df['phase_type'] == 'P'].set_index('file_name')  
df_s = df[df['phase_type'] == 'S'].set_index('file_name')  

# Create a new directory for updated SAC files  
new_sac_folder = './CAP_6Outlier_3SAC'  
os.makedirs(new_sac_folder, exist_ok=True)  

# Create the results subdirectory  
results_folder = os.path.join(new_sac_folder, 'results')  
os.makedirs(results_folder, exist_ok=True)   

# Prepare a list to store results for CSV output  
results = []  

# Path to the original SAC files  
sac_folder = './CAP_5Filter_3SAC'  
for root, dirs, files in os.walk(sac_folder):  
    for file in files:  
        if file.endswith('.SAC'):  
            file_path = os.path.join(root, file)  
            new_file_path = os.path.join(new_sac_folder, file)  
            
            # Copy SAC file to the new directory  
            shutil.copy2(file_path, new_file_path)  
            
            # Read the newly copied SAC file  
            st = read(new_file_path)  
            tr = st[0]  
            
            # Initialize t1 and t2 values  
            t1_value = None  
            t2_value = None  
            
            # Update t1 (P wave) and t2 (S wave) if applicable  
            if file in df_p.index:  
                t1_value = 2 * float(df_p.loc[file, 'time_diff'])  
                print(f'Updating {file}: t1 = {t1_value}')  
                tr.stats.sac.t1 = t1_value  
            
            if file in df_s.index:  
                t2_value = 2 * float(df_s.loc[file, 'time_diff'])  
                print(f'Updating {file}: t2 = {t2_value}')  
                tr.stats.sac.t2 = t2_value  

            # Save the updated SAC file  
            tr.write(new_file_path, format='SAC')  

            # Append results to the list  
            results.append({  
                'file_name': file,  
                't1': t1_value,  
                't2': t2_value  
            })  

# Convert results to DataFrame  
results_df = pd.DataFrame(results)  

# Sort by t1 and t2  
results_df = results_df.sort_values(by=['t1', 't2'])  

# Save results to CSV  
output_csv_path = os.path.join(results_folder, 'sac_file_updates.csv')  
results_df.to_csv(output_csv_path, index=False)  

print(f"All SAC files have been copied and header variables updated. New files are saved in the CAP_6Outlier_3SAC directory.")  
print(f"Results saved to {output_csv_path}.")