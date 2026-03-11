import os
import glob
import re

dir_path = r"c:\Users\DELL\OneDrive\Desktop\pro\frontend\src\components\modules\scoring"

replacements = {
    r'bg-\[\#1A1C24\]': 'bg-gray-50',
    r'bg-\[\#1B1D27\]': 'bg-gray-100',
    r'bg-\[\#262730\]': 'bg-white',
    r'bg-\[\#3D404A\]': 'bg-gray-200',
    r'bg-\[\#0E1117\]': 'bg-white',
    r'text-\[\#FAFAFA\]': 'text-gray-900',
    r'text-\[\#A2C7E5\]': 'text-blue-700',
    r'text-\[\#E5A2A2\]': 'text-red-700',
    r'border-\[\#ffffff10\]': 'border-gray-200',
    r'border-\[\#ffffff20\]': 'border-gray-300',
    r'hover:bg-\[\#3D404A\]': 'hover:bg-gray-100',
    r'hover:bg-\[\#262730\]': 'hover:bg-gray-50',
    r'text-gray-300': 'text-gray-800',
    r'text-gray-400': 'text-gray-600',
    r'text-[#CD8C8C]': 'text-red-700',
    r'bg-\[\#3A1E1E\]': 'bg-red-50',
    r'hover:bg-\[\#4A2626\]': 'hover:bg-red-100',
    r'bg-\[\#1C2C3F\]': 'bg-blue-50',
    r'hover:bg-\[\#27405A\]': 'hover:bg-blue-100',
    r'bg-\[\#1A3A2C\]': 'bg-green-50',
    r'hover:bg-\[\#1E4D38\]': 'hover:bg-green-100',
    r'bg-\[\#3A2A1A\]': 'bg-orange-50',
    r'hover:bg-\[\#5A4027\]': 'hover:bg-orange-100',
    r'border-\[\#27405A\]': 'border-blue-200',
    r'border-\[\#5A4027\]': 'border-orange-200',
    r'text-\[\#85C2A5\]': 'text-green-700',
}

files = glob.glob(os.path.join(dir_path, "*.tsx"))

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    for old, new in replacements.items():
        content = re.sub(old, new, content)

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done styling replacements.")
