import glob, re

for file_path in glob.glob('sports/*.py'):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        # Find dictionary creations like pd.DataFrame([{"match_id": ..., ...}])
        match = re.search(r'new_event = {([^}]*)}', content)
        if match:
            print(f'\n--- {file_path} ---')
            fields = re.findall(r'[\'"]([a-zA-Z0-9_]+)[\'"]\s*:', match.group(1))
            print(fields)
        else:
            match = re.search(r'new_row = {([^}]*)}', content)
            if match:
                print(f'\n--- {file_path} ---')
                fields = re.findall(r'[\'"]([a-zA-Z0-9_]+)[\'"]\s*:', match.group(1))
                print(fields)
            else:
                match = re.search(r'update_score.*?new_score = {([^}]*)}', content, re.DOTALL)
                if match:
                    print(f'\n--- {file_path} ---')
                    fields = re.findall(r'[\'"]([a-zA-Z0-9_]+)[\'"]\s*:', match.group(1))
                    print(fields)
                else:
                    match = re.search(r'update_score.*?score_data = {([^}]*)}', content, re.DOTALL)
                    if match:
                        print(f'\n--- {file_path} ---')
                        fields = re.findall(r'[\'"]([a-zA-Z0-9_]+)[\'"]\s*:', match.group(1))
                        print(fields)
