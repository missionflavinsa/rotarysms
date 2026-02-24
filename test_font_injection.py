import fitz
import glob
print(len(glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)))
