import os

modules_dir = r"c:\Users\DELL\OneDrive\Desktop\pro\frontend\src\components\modules"

def add_search(file_path, state_var, array_var, fields_to_search):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "const [search, setSearch] = useState('');" in content or "const [searchTerm, setSearchTerm]" in content:
        return # Already has search
        
    # Add state
    content = content.replace(f"const [{state_var}, set{state_var.capitalize()}]", 
                              f"const [{state_var}, set{state_var.capitalize()}] = useState<any[]>([]);\n  const [searchTerm, setSearchTerm] = useState('');\n  // DUMMY")
    
    # Add input field just below the View heading
    search_input = f"""
        <div className="mb-4">
          <input 
            type="text" 
            placeholder="Search..." 
            className="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500 outline-none"
            value={{searchTerm}}
            onChange={{e => setSearchTerm(e.target.value)}}
          />
        </div>
"""
    content = content.replace(f'<div className="overflow-x-auto">', search_input + '\n        <div className="overflow-x-auto">')
    
    # Add filter logic
    filter_logic = f"""{array_var}.filter(item => JSON.stringify(item).toLowerCase().includes(searchTerm.toLowerCase())).map"""
    content = content.replace(f"{array_var}.map", filter_logic)
    
    # Clean up dummy
    content = content.replace("= useState<any[]>([]);\n  const [searchTerm, setSearchTerm] = useState('');\n  // DUMMY", "")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {file_path}")

try:
    add_search(os.path.join(modules_dir, "Tournaments.tsx"), "tournaments", "tournaments", [])
    add_search(os.path.join(modules_dir, "Teams.tsx"), "teams", "teams", [])
    add_search(os.path.join(modules_dir, "Players.tsx"), "players", "players", [])
    add_search(os.path.join(modules_dir, "Schedule.tsx"), "matches", "matches", [])
except Exception as e:
    print(f"Error: {e}")
