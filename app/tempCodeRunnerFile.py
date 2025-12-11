
import time

import pandas as pd
import streamlit as st

from threadlib import ThreadPool, ThreadPoolStats


st.set_page_config(page_title="Thread Management Demo", layout="wide")


# Sidebar controls
st.sidebar.title("Thread Pool Settings")

demo_type = st.sidebar.radio(
    "Select demo workload",
    ["CPU-bound (sum)", "Placeholder"],
)

min_workers = st.sidebar.slider("Min workers", 1, 32, 4)
max_workers = st.sidebar.slider("Max workers", min_workers, 64, min_workers)
num_tasks = st.sidebar.slider("Number of tasks", 10, 1000, 100, step=10)
work_size = st.sidebar.slider("Work size per task", 1_000, 500_000, 100_000, step=1_000)

run_btn = st.sidebar.button("Run benchmark")

st.title("Scalable Thread Management Library – Demo")

tab_overview, tab_logs, tab_about = st.tabs(["Overview", "Task Details", "About"])

if "log_rows" not in st.session_state:
    st.session_state.log_rows = []
if "last_results" not in st.session_state:
    st.session_state.last_results = None


def demo_task(task_id: int, size: int) -> dict:
    """Very simple CPU-bound task used by the UI demo."""
    total = 0
    for i in range(size):
        total += (i * i) % 97
    return {"task_id": task_id, "result": total}


if run_btn:
    pool = ThreadPool(min_workers=min_workers, max_workers=max_workers)
    futures = []
    start_time = time.time()

    st.session_state.log_rows = []

    for i in range(num_tasks):
        futures.append(pool.submit(demo_task, i, work_size))

    for f in futures:
        res = f.result()
        st.session_state.log_rows.append(
            {
                "task_id": res["task_id"],
                "status": "OK",
            }
        )

    pool.shutdown(wait=True)
    end_time = time.time()

    total_time = end_time - start_time
    stats: ThreadPoolStats = pool.get_stats()

    st.session_state.last_results = {
        "total_time": total_time,
        "stats": stats,
        "num_tasks": num_tasks,
        "min_workers": min_workers,
        "max_workers": max_workers,
    }

with tab_overview:
    st.subheader("Summary")

    col1, col2, col3, col4 = st.columns(4)
    if st.session_state.last_results is not None:
        stats = st.session_state.last_results["stats"]
        col1.metric("Total submitted", stats.total_submitted)
        col2.metric("Total completed", stats.total_completed)
        col3.metric("Active threads (last)", stats.current_running)
        col4.metric("Avg task time (s)", round(stats.avg_exec_time, 6))

        st.write(
            f"**Total benchmark time:** {st.session_state.last_results['total_time']:.4f} s"
        )

        df_perf = pd.DataFrame(
            {
                "Threads": [st.session_state.last_results["min_workers"]],
                "Time (s)": [st.session_state.last_results["total_time"]],
            }
        )
        df_perf = df_perf.set_index("Threads")
        st.bar_chart(df_perf)
    else:
        st.info("Run a benchmark from the sidebar to see results.")

with tab_logs:
    st.subheader("Task Logs")
    if st.session_state.log_rows:
        df_logs = pd.DataFrame(st.session_state.log_rows)
        st.dataframe(df_logs)
    else:
        st.info("No tasks have been run yet.")

with tab_about:
    st.subheader("About this Project")
    st.markdown(
        """
        This app demonstrates a **Scalable Thread Management Library** implemented in Python.

        **Key components:**

        - `ThreadPool` — custom implementation using `threading.Thread` and `queue.Queue`.
        - `Future` — simple object for retrieving asynchronous results.
        - `ThreadPoolStats` — provides basic metrics such as submitted/completed tasks and average execution time.
        - `sync_primitives` — small wrappers for mutex, read-write lock, and barrier.

        You can extend this project further by:

        - Adding autoscaling for worker threads based on queue length.
        - Implementing IO-bound workloads in the demo.
        - Adding real-time charts that show queue size and active workers over time.
        """
    )
