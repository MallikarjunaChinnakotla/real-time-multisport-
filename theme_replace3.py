import os
import glob
import re

dir_path = r"c:\Users\DELL\OneDrive\Desktop\pro\frontend\src\components\modules\scoring"
files = glob.glob(os.path.join(dir_path, "*.tsx"))

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # If the button has a light bg and text-white, replace text-white with text-gray-900 or similar
    content = re.sub(r'bg-green-50(.*?)text-white', r'bg-green-50\1text-green-800', content)
    content = re.sub(r'bg-blue-50(.*?)text-white', r'bg-blue-50\1text-blue-800', content)
    content = re.sub(r'bg-yellow-50(.*?)text-white', r'bg-yellow-50\1text-yellow-800', content)
    content = re.sub(r'bg-red-50(.*?)text-white', r'bg-red-50\1text-red-800', content)
    content = re.sub(r'bg-orange-50(.*?)text-white', r'bg-orange-50\1text-orange-800', content)
    
    # Just to be safe, any other text-white on light bgs
    content = re.sub(r'bg-gray-50(.*?)text-white', r'bg-gray-50\1text-gray-900', content)
    content = re.sub(r'bg-white(.*?)text-white', r'bg-white\1text-gray-900', content)

    # Some old hardcoded team color logic:
    # "text-[#FAFAFA]" was global, we changed it to text-gray-900, but some might be missed
    content = re.sub(r'text-\[\#FAFAFA\]', 'text-gray-900', content)
    content = re.sub(r'text-\[\#A2C7E5\]', 'text-blue-700', content)
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Done text-white replacements.")
