import time
import os

print("--- PROFILING STREAMLIT START ---")
start_time = time.time()

import streamlit.web.bootstrap
print(f"Import Streamlit: {time.time() - start_time:.3f}s")
