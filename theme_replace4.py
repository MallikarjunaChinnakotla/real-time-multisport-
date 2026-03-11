import os
import glob

dir_path = r"c:\Users\DELL\OneDrive\Desktop\pro\frontend\src\components\modules\scoring"
files = glob.glob(os.path.join(dir_path, "*.tsx"))

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace("text-white", "text-gray-900")
    content = content.replace("hover:text-white", "hover:text-gray-900")
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Done remaining text-white replacements.")
