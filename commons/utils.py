from pathlib import Path

def list_perf_event_log_files(data_dir: Path):
    csv_files = list(data_dir.glob("**/*.csv"))
    
    # Filter CSV files that end with "perf_event_log"
    perf_event_log_files = [file for file in csv_files if file.stem.endswith("perf_event_log")]
    
    if not perf_event_log_files:
        print(f"Error: no csvs ending in perf_event_log found in data_dir: {data_dir}")
        
    return perf_event_log_files