import threading
import queue
import time
import uuid
import logging
import math
import random
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Callable, Any, List, Optional, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HPCEngine")

class Priority(IntEnum):
    HIGH = 0
    NORMAL = 1
    LOW = 2

@dataclass(order=True)
class Task:
    priority: int
    id: str = field(compare=False)
    func: Callable = field(compare=False)
    type: str = field(default="CPU", compare=False) # CPU, IO, MIXED
    args: tuple = field(default=(), compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    on_complete: Optional[Callable] = field(default=None, compare=False)
    on_error: Optional[Callable] = field(default=None, compare=False)
    created_at: float = field(default_factory=time.time, compare=False)

class Worker(threading.Thread):
    def __init__(self, task_queue: queue.PriorityQueue, worker_id: int, pause_event: threading.Event):
        super().__init__(daemon=True)
        self.task_queue = task_queue
        self.worker_id = worker_id
        self.pause_event = pause_event
        
        # State & Stats
        self.is_busy = False
        self.running = True
        self.current_task: Optional[Task] = None
        self.tasks_completed = 0
        self.total_runtime = 0.0
        self._stop_event = threading.Event()

    def run(self):
        while self.running:
            try:
                # 1. Check Pause
                self.pause_event.wait()
                
                # 2. Get Task (Timeout to allow checking stop/pause/scale down)
                try:
                    priority, task = self.task_queue.get(timeout=0.5)
                except queue.Empty:
                    if not self.running: break
                    continue

                if task is None: # Poison Pill
                    break

                # 3. Execute
                self.is_busy = True
                self.current_task = task
                start_t = time.time()
                
                try:
                    result = task.func(*task.args, **task.kwargs)
                    if task.on_complete:
                        task.on_complete(result)
                except Exception as e:
                    logger.error(f"Task {task.id} failed: {e}")
                    if task.on_error:
                        task.on_error(e)
                finally:
                    duration = time.time() - start_t
                    self.total_runtime += duration
                    self.tasks_completed += 1
                    self.is_busy = False
                    self.current_task = None
                    self.task_queue.task_done()
            
            except Exception as e:
                logger.error(f"Worker {self.worker_id} crash: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False

class HPCThreadEngine:
    """
    HPC Engine V2: 
    - Dynamic Scaling
    - Pause/Resume
    - Detailed Metrics
    - Task Cancellation (Flush)
    """
    def __init__(self, max_workers: int = 4):
        self.task_queue = queue.PriorityQueue()
        self.workers: List[Worker] = []
        self.lock = threading.Lock()
        self.pause_event = threading.Event()
        self.pause_event.set() # Initially running
        
        # Stats history
        self.completed_tasks_history = []
        
        # Init
        self.resize_pool(max_workers)

    def resize_pool(self, new_count: int):
        """Dynamically resizes the worker pool."""
        with self.lock:
            current = len(self.workers)
            if new_count > current:
                # Add workers
                for i in range(current, new_count):
                    w = Worker(self.task_queue, i, self.pause_event)
                    w.start()
                    self.workers.append(w)
            elif new_count < current:
                # Remove workers (Stop from end)
                # We interpret "remove" as "stop taking new tasks and die"
                # We can inject Poison Pills or set running=False
                diff = current - new_count
                for _ in range(diff):
                    w = self.workers.pop()
                    w.stop() # Soft stop
                    # w.join() # Don't block UI, let them die eventually
                    
                # To be cleaner, we could also put None in queue, but priority queue makes that specific
                # Simple boolean flag check in worker loop is enough for now.

    @property
    def num_workers(self):
        return len(self.workers)

    def add_worker(self):
        self.resize_pool(len(self.workers) + 1)

    def remove_worker(self):
        if len(self.workers) > 0:
            self.resize_pool(len(self.workers) - 1)

    def pause_workload(self):
        self.pause_event.clear()

    def resume_workload(self):
        self.pause_event.set()

    def cancel_all_tasks(self):
        """Clears the pending queue."""
        with self.lock:
            # Draining the queue is safer than replacing it, because Worker objects
            # hold a reference to the specific queue instance.
            try:
                while True:
                    self.task_queue.get_nowait()
                    self.task_queue.task_done()
            except queue.Empty:
                pass
            
            # Reset pause event just in case they were stuck on pause
            # self.pause_event.set() 
            # Actually user might want to stay paused.
            # But we must ensure workers aren't stuck in a 'get' that will never return if we swapped queues (which we aren't anymore).

    def submit_task(self, func: Callable, *args, priority=Priority.NORMAL, type="CPU", on_complete=None, on_error=None, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        # Ensure we are not sending into a void if we swapped queues (fixed by draining instead)

        task = Task(
            priority=priority,
            id=task_id,
            func=func,
            type=type,
            args=args,
            kwargs=kwargs,
            on_complete=on_complete,
            on_error=on_error
        )
        self.task_queue.put((priority, task))
        return task_id

    def shutdown(self, wait=True):
        self.resize_pool(0)
        
    def get_stats(self) -> Dict:
        """Returns detailed engine statistics."""
        with self.lock:
            active_workers = sum(1 for w in self.workers if w.is_busy)
            total_completed = sum(w.tasks_completed for w in self.workers)
            
            return {
                "total_workers": len(self.workers),
                "active_workers": active_workers,
                "idle_workers": len(self.workers) - active_workers,
                "pending_tasks": self.task_queue.qsize(),
                "total_completed": total_completed,
                "is_paused": not self.pause_event.is_set()
            }

    def get_worker_details(self):
        """Returns list of detail dicts for visualization tooltips."""
        with self.lock:
            details = []
            for w in self.workers:
                current_type = w.current_task.type if w.current_task else None
                priority = None
                if w.current_task:
                    priority = w.current_task.priority
                    
                details.append({
                    "id": w.worker_id,
                    "busy": w.is_busy,
                    "completed": w.tasks_completed,
                    "current_task": current_type,
                    "priority": priority
                })
            return details

    # --- Simulation helpers ---
    def initialize_workers(self, count):
        self.resize_pool(int(count))

    def fire_workload(self, task_count=10, type="CPU", priority=Priority.NORMAL):
        def dummy_task(t_type):
            if t_type == "CPU":
                # CPU Bound
                limit = 20000 
                count = 0
                while count < limit: 
                    math.sqrt(random.randint(1,100000))
                    count+=1
                time.sleep(random.uniform(0.5, 1.2))
            elif t_type == "IO":
                # IO Bound
                time.sleep(random.uniform(1.0, 2.0))
            else:
                # Mixed
                time.sleep(0.5)
        
        for _ in range(task_count):
            self.submit_task(dummy_task, type, type=type, priority=priority)

hpc_engine = HPCThreadEngine(max_workers=0)
