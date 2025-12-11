import psutil
import time
import threading
from src.utils.helpers import bytes_to_human

class SystemMonitor:
    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.cpu_percent = 0
        self.ram_percent = 0
        self.ram_total = psutil.virtual_memory().total
        self.ram_used = 0
        self.total_threads = 0
        self.monitor_thread = None
        self.top_processes = []
    
    def start(self):
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

    def stop(self):
        self.running = False
    
    def _monitor_loop(self):
        while self.running:
            try:
                # 1. CPU & RAM (Fast)
                cpu = psutil.cpu_percent(interval=0.5)
                mem = psutil.virtual_memory()
                
                # 2. Total Threads (Slightly heavier, but okay)
                # We can approximate this or fetch it less frequently if needed, 
                # but psutil.pids() + loop is the only way to get EXACT total threads.
                # Optimization: Just count processes for speed, or do a light scan.
                # The user wants "Total Threads", which usually requires iterating all processes.
                # To avoid high CPU, we might do this every other tick or just count processes if acceptable.
                # However, prompt demanded "Efficient process scanning". 
                # Let's do a full scan but optimized.
                
                thread_count = 0
                procs = []
                
                # Iterate once for both threads count and top list
                for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'num_threads']):
                    try:
                        # Some processes might vanish during iteration
                        p_info = p.info
                        if p_info['num_threads']:
                            thread_count += p_info['num_threads']
                        
                        # Store for sorting
                        # Calculate memory in MB for sorting
                        mem_mb = (p_info['memory_info'].rss / 1024 / 1024)
                        p_info['memory_mb'] = mem_mb
                        procs.append(p_info)
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                
                # Sort by CPU usage mainly, limit to top 50
                procs.sort(key=lambda x: x['cpu_percent'], reverse=True)
                top_50 = procs[:50]

                with self.lock:
                    self.cpu_percent = cpu
                    self.ram_percent = mem.percent
                    self.ram_used = mem.used
                    self.total_threads = thread_count
                    self.top_processes = top_50

            except Exception as e:
                print(f"Monitor Warning: {e}")
                time.sleep(1)
            
            # Use interval inside cpu_percent, so no extra sleep needed here mostly, 
            # but we loop slightly slower to save Battery/CPU
            # cpu_percent(0.5) blocks for 0.5s, which constitutes our "sleep".
    
    def get_stats(self):
        """Thread-safe getter for UI."""
        with self.lock:
            return {
                'cpu': self.cpu_percent,
                'ram_percent': self.ram_percent,
                'ram_used_human': bytes_to_human(self.ram_used),
                'total_threads': self.total_threads,
                'processes': self.top_processes
            }

sys_monitor = SystemMonitor()
