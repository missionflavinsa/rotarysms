import time
import cProfile
import pstats
import io

start = time.time()
print("Importing app...")
import app
print(f"Imported in {time.time() - start:.3f}s")
