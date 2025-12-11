
import psutil
import pandas as pd
from typing import List, Dict, Any

def get_system_metrics() -> Dict[str, Any]:
    """Get high-level system metrics."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_percent": psutil.virtual_memory().percent,
        "total_threads": sum(p.num_threads() for p in psutil.process_iter(['num_threads'])),
    }

def get_process_list(limit: int = 50, filter_name: str = "") -> pd.DataFrame:
    """Get list of running processes."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'num_threads', 'cpu_percent', 'memory_percent']):
        try:
            pinfo = proc.info
            if filter_name and filter_name.lower() not in pinfo['name'].lower():
                continue
            processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    df = pd.DataFrame(processes)
    if not df.empty:
        # Sort by CPU usage descending
        df = df.sort_values(by='cpu_percent', ascending=False).head(limit)
        # Rename columns for display
        df = df.rename(columns={
            'pid': 'PID',
            'name': 'Name',
            'num_threads': 'Threads',
            'cpu_percent': 'CPU %',
            'memory_percent': 'Memory %'
        })
    return df
