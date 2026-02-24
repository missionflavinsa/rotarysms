import fitz
try:
    f = fitz.Font("Arial")
    print("Arial works")
except Exception as e:
    print("Arial error:", e)
