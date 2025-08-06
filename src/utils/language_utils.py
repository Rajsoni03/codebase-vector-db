def detect_language(extension):
    language_map = {
        '.py': 'python', 
        '.js': 'javascript', 
        '.jsx': 'javascript', 
        '.ts': 'typescript', 
        '.tsx': 'typescript',
        '.java': 'java', 
        '.cpp': 'cpp', 
        '.c': 'c', 
        '.h': 'c', 
        '.go': 'go', 
        '.rs': 'rust', 
        '.rb': 'ruby', 
        '.php': 'php'
    }
    return language_map.get(extension, 'unknown')