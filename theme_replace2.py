import os
import glob
import re

dir_path = r"c:\Users\DELL\OneDrive\Desktop\pro\frontend\src\components\modules\scoring"

replacements = {
    r'bg-\[\#1C1F2B\]': 'bg-gray-100',
    r'hover:bg-\[\#2B2F42\]': 'hover:bg-gray-200',
    r'bg-\[\#2B2F42\]': 'bg-gray-200',
    r'bg-\[\#1A2534\]': 'bg-blue-50',
    r'bg-\[\#1F2336\]': 'bg-gray-50',
    
    r'bg-\[\#4A4222\]': 'bg-yellow-50',
    r'hover:bg-\[\#5C522B\]': 'hover:bg-yellow-100',
    r'text-\[\#FFF066\]': 'text-yellow-600',
    
    r'bg-\[\#4A2222\]': 'bg-red-50',
    r'hover:bg-\[\#5C2B2B\]': 'hover:bg-red-100',
    r'text-\[\#FF6666\]': 'text-red-600',
    
    r'text-\[\#CD8C8C\]': 'text-red-700',
    r'text-\[\#E57A7A\]': 'text-red-600',
    
    r'bg-\[\#ffffff20\]': 'bg-gray-200',
    r'hover:bg-\[\#202330\]': 'hover:bg-gray-100',
}

files = glob.glob(os.path.join(dir_path, "*.tsx"))

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    for old, new in replacements.items():
        content = re.sub(old, new, content)

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done additional replacements.")
