import re
import json

def parse_json(message):
    """
    Extract JSON content from a message and convert it to a dictionary.
    Updated to handle specific JSON structures with subtasks.
    """

    # Initialize a dictionary to hold the extracted data
    data = {}

    # Use regex to find JSON content in the message
    json_match = re.search(r"```json\n(.*?)\n```", message, re.DOTALL)
    if json_match:
        json_content = json_match.group(1)
        # Attempt to parse the message directly as JSON
        data = json.loads(json_content)

    # Validate the structure of the JSON
    if "subtasks" in data and isinstance(data["subtasks"], list):
        for subtask in data["subtasks"]:
            if not all(key in subtask for key in ["name", "description", "steps"]):
                raise ValueError("Invalid subtask structure")
            if not isinstance(subtask["steps"], list):
                raise ValueError("Steps should be a list")
        return data
    else:
        raise ValueError("Invalid JSON structure: Missing 'subtasks' or incorrect type")


def parse_markdown(markdown_text):
    # Split by '---' while ignoring empty sections
    sections = [section.strip() for section in markdown_text.split('---') if section.strip()]

    # regex patterns
    name_pattern = re.compile(r'##\s*Name\s*\n([^\n]+)', re.DOTALL)
    desc_pattern = re.compile(r'##\s*Description\s*\n(.+?)(?=\n##|\Z)', re.DOTALL)
    steps_pattern = re.compile(r'##\s*Steps\s*\n(.+)', re.DOTALL)

    parsed_subtasks = []

    for section in sections:
        # Extract Name
        name_match = name_pattern.search(section)
        # Extract Description
        desc_match = desc_pattern.search(section)
        # Extract Steps block
        steps_match = steps_pattern.search(section)

        # Validate the presence of Name, Description, Steps
        if name_match and desc_match and steps_match:
            name = name_match.group(1).strip()
            description = desc_match.group(1).strip()

            # Extract steps as a list by splitting on numbered lines
            raw_steps = steps_match.group(1).strip()
            steps = [step.strip() for step in re.findall(r'\d+\.\s*(.+)', raw_steps)]

            parsed_subtasks.append({
                "name": name,
                "description": description,
                "steps": steps,
                "text": section
            })

    if abs(len(parsed_subtasks) - len(sections)) > 1:
        raise ValueError("Invalid markdown format: Each section must contain '## Name', '## Description', and '## Steps'.")

    return parsed_subtasks