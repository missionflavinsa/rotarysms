import re

with open("src/views/teacher_classes.py", "r") as f:
    lines = f.readlines()

for i in range(227, 278):
    # lines are 0-indexed, so lines[227] is line 228
    if lines[i].startswith(" " * 60):
        lines[i] = lines[i].replace(" " * 60, " " * 56, 1)

with open("src/views/teacher_classes.py", "w") as f:
    f.writelines(lines)
