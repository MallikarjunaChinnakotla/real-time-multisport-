import os
import glob

files = glob.glob(r'c:\Users\DELL\OneDrive\Desktop\pro\frontend\src\components\modules\*.tsx')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if 'searchTerm' in content and 'const [searchTerm, setSearchTerm]' not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'const [' in line and 'useState' in line:
                lines.insert(i + 1, "  const [searchTerm, setSearchTerm] = useState('');")
                break
        new_content = '\n'.join(lines)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Fixed {f}')
