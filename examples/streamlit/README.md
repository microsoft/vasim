# VASIM Autoscaling Simulator Toolkit

This is a Streamlit-based application for visualizing, simulating, and tuning autoscaling strategies using the VASIM Autoscaling Simulator Toolkit. The app allows users to interact with various algorithms, tune parameters, visualize workload performance, and manage tuning histories.

## Features

- **Workload Visualization:** Visualize CPU usage over time from selected CSV files.
- **Simulation Run:** Run autoscaling simulations with adjustable parameters like decision frequency and core count.
- **Simulation Tuning:** Tune parameters using grid or random strategies to optimize performance (WIP).
- **Simulation History:** View previous simulation tuning results and visualize Pareto frontiers (WIP).

## Requirements

- Python 3.7 or higher
- Streamlit
- Pandas
- Matplotlib
- Additional dependencies:
  - `recommender`
  - `ClusterStateConfig`
  - `simulator`
  - (Ensure these modules are included in your project)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/microsoft/vasim.git
   cd vasim
   ```
2. Install dependencies
   ```
   pip install .
   pip install examples/streamlit/requirements.txt 
   ```

3. Run. It will start your web app and output link to access via browser (e.g. Local URL: http://localhost:8501)

   ```
   streamlit run examples/streamlit/web_demo.py
   ```
