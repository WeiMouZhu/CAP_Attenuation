# CVP_attenuation_Anatolia
Cappadocia Volcanic Province: Data Acquisition and Preprocessing for Seismic Attenuation Imaging

This is for seismic data acquiring and pre-processing procedure of MuRAT


## Prerequisites

- [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

## Setting up the environment

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. Create the Conda environment:
   ```
   conda env create -f environment.yml
   ```

3. Activate the environment:
   ```
   conda activate your-env-name
   ```

## Usage
This process consists of 8 steps in total, and is still undergoing improvements.

## Step-0: Acquiring the seismic event catalog
`0_event_catlog_acquire.py`
`0_KOERI_catlog.py`

`01_events_plot.py`: visualizing the seismic event distribution

## Step-1: Mass downloading the metadata
`1_mass_download.py`

## Step-2: Remove Response and Pre-processing
`2_remove_response.py`

## Step-3: Delete Events with Sparse SAC file and Extract Station Lists
`3_delete_less_5.py`

## Step-4: Set Theoretical Arrivals and Prepare SAC Files for AI tools Picking
`4_TauP_PS.py`

#PhaseNet#

`python phasenet/predict.py --model=model/190703-214543 --data_list=CAP_SAC/results/sac.csv --data_dir=CAP_SAC --format=sac --batch_size=1 --plot_figure --result_dir=CAP_SAC/results`

## Step-5: Filter Picking Results 
`5_filter.py`

## Step-6: Change SAC headers
`6_change_header.py`

## Step-7: Picks Outlier
`7_picks_outlier.ipynb`

## Step-8: QC-Visualizing Check 
`8_check_visualizing.ipynb`



