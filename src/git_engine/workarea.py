from git import Repo
import xml.etree.ElementTree as ET
import re
from typing import List, Dict
from pprint import pprint
import os 
import subprocess
import requests
import json
import multiprocessing

from settings import TerminalColor, print_colored


# Parse the XML file to extract project information
def parse_xml(file_path, remote_dict, project_dict, workarea_path):
    """
    Parses the XML file to extract project and remote information.
    The XML file is expected to be in the .repo/manifests directory of the workarea.
    """
    repo_manifest_path = os.path.join(workarea_path, ".repo/manifests/")
    with open(os.path.join(repo_manifest_path, file_path), "r") as file:
        xml_content = file.read()

    root = ET.fromstring(xml_content)

    for child in root:
        if child.tag == "include":
            include_path = child.attrib.get("name")
            if include_path:
                parse_xml(include_path, remote_dict, project_dict)
            else:
                raise Exception("Error: Recursive include detected")
        elif child.tag == "project":
            path = child.attrib.get("path")
            remote = child.attrib.get("remote")
            name = child.attrib.get("name")
            revision = child.attrib.get("revision")
            project_dict[path] = {
                "name": name,
                "path": path,
                "remote": remote,
                "revision": revision
            }

        elif child.tag == "remote":
            name = child.attrib.get('name')
            remote = child.attrib.get('fetch')
            if name not in remote_dict:
                remote_dict[name] = remote
        else:
            print(child.tag)


# check the diff between the next and prod of each project
def check_repo_diff(args):
    project_name, next_dict, prod_dict, workarea_path = args
    next_project = next_dict.get(project_name)
    prod_project = prod_dict.get(project_name)

    if not next_project or not prod_project:
        print(f"Project {project_name} not found in one of the dictionaries.")
        return (project_name, None)

    next_path = next_project.get("path")
    prod_path = prod_project.get("path")

    if not next_path or not prod_path:
        print(f"Path not found for project {project_name}.")
        return (project_name, None)

    next_repo_path = os.path.join(workarea_path, next_path)
    prod_repo_path = os.path.join(workarea_path, prod_path)

    remote = next_project.get("remote")
    prod_branch = prod_project.get("revision")
    next_branch = next_project.get("revision")

    if (next_branch == prod_branch):
        print(f"Next and Prod branches are the same for project {project_name}. No diff to check.")
        return (project_name, None)
    
    try:
        next_repo = Repo(next_repo_path)
        prod_repo = Repo(prod_repo_path)

        # Check if the revision is a tag or branch
        if prod_branch.startswith("refs/tags/"):
            diff_with_prod = next_repo.git.diff(prod_branch)
        else:
            next_repo.git.fetch(remote, next_branch)
            prod_repo.git.fetch(remote, prod_branch)
            diff_with_prod = next_repo.git.diff(f"{remote}/{prod_branch}")
        print_colored(f"Adding diff for {project_name}:", TerminalColor.LIGHT_GRAY)
        return (project_name, diff_with_prod)
    except Exception as e:
        print(f"Error while checking diff for project {project_name}: {e}")
        return (project_name, None)

# Get all differences between next and prod projects using multiprocessing
def get_all_diff(next_project_dict, prod_project_dict, workarea_path):
    changes_dict = {}
    repo_names = list(next_project_dict.keys())
    args_list = [(repo_name, next_project_dict, prod_project_dict, workarea_path) for repo_name in repo_names]
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        results = pool.map(check_repo_diff, args_list)

    for name, data in results:
        if data is not None and len(data) > 0:
            changes_dict[name] = data

    return changes_dict

def detect_language(filename: str) -> str:
    """Detect language from file extension for syntax highlighting."""
    ext = os.path.splitext(filename)[1].lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".html": "html",
        ".css": "css",
        ".md": "markdown",
        ".json": "json",
        ".yml": "yaml",
        ".yaml": "yaml"
    }
    return mapping.get(ext, "")

def parse_git_diff(diff_text: str) -> List[str]:
    """
    Convert git diff string into a list of markdown strings per file
    with rich metadata for AI consumption.
    """
    # Split into chunks per file
    file_diffs = re.split(r'(?=^diff --git )', diff_text, flags=re.MULTILINE)
    markdown_files = []

    for chunk in file_diffs:
        if not chunk.strip():
            continue

        header_match = re.search(r'diff --git a/(.+?) b/(.+)', chunk)
        if not header_match:
            continue

        old_file = header_match.group(1)
        new_file = header_match.group(2)
        filename = new_file

        # Determine status
        if 'new file mode' in chunk:
            status = 'added'
        elif 'deleted file mode' in chunk:
            status = 'deleted'
        elif re.search(r'rename from', chunk):
            status = 'renamed'
        else:
            status = 'modified'

        # Count added and removed lines
        added_lines = len(re.findall(r'^\+[^+]', chunk, flags=re.MULTILINE))
        removed_lines = len(re.findall(r'^-[^-]', chunk, flags=re.MULTILINE))

        if added_lines == 0 and removed_lines == 0:
            # No changes
            continue

        # Extract code changes
        code_match = re.search(r'(@@[\s\S]+)', chunk)
        code_changes = code_match.group(1) if code_match else ''

        language = detect_language(filename)

        # YAML frontmatter metadata
        metadata = (
            "---\n"
            f"**Old Path:** {old_file}\n"
            f"**New Path:** {new_file}\n"
            f"**Status:** {status}\n"
            f"**Change Type:** {status}\n"
            f"**Lines Added:** {added_lines}\n"
            f"**Lines Removed:** {removed_lines}\n"
            f"**Language:** {language}\n"
            # f"**Tags:** [\"git-diff\", \"code-change\"]\n"
            "---\n"
        )
        
        # Parse hunks and add line numbers
        diff_lines = []
        hunks = re.split(r'(?=^@@ )', chunk, flags=re.MULTILINE)

        for hunk in hunks:
            hunk_header = re.match(r'^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', hunk)
            if not hunk_header:
                continue

            old_start, old_count, new_start, new_count = map(lambda x: int(x) if x else 0, hunk_header.groups())

            old_line = old_start
            new_line = new_start

            for line in hunk.splitlines()[1:]:
                if line.startswith('+') and not line.startswith('+++'):
                    diff_lines.append(f"{old_line:>5} | {new_line:>5} | + {line[1:]}")
                    new_line += 1
                elif line.startswith('-') and not line.startswith('---'):
                    diff_lines.append(f"{old_line:>5} | {new_line:>5} | - {line[1:]}")
                    old_line += 1
                else:
                    diff_lines.append(f"{old_line:>5} | {new_line:>5} |   {line[1:]}")
                    old_line += 1
                    new_line += 1

        # Markdown content
        markdown = (f"# File: `{filename}`\n"
                    f"## Metadata\n"
                    f"{metadata}\n"
                    "---\n"
                    f"## Code Changes with Line Numbers:\n"
                    "```diff\n"
                    " OLD   |  NEW  | CODE\n"
                    "-----------------------\n"
                    f"{chr(10).join(diff_lines)}\n"
                    "```\n"
                )

        # Optionally, provide language-specific code block if needed
        if language and status != "deleted":
            clean_code = "\n".join(line[1:] for line in code_changes.splitlines() if line.startswith('+') and not line.startswith('+++'))
            if clean_code.strip():
                markdown += f"""```\nNew Code Extract:\n{clean_code.strip()}\n```"""
        markdown_files.append(markdown)

    return markdown_files


if __name__ == "__main__":

    workarea_path = "/home/raj/Desktop/edgeai/sdk_workareas/j742s2_linux/"

    # Parse the next manifest
    print("Parsing next manifest...")
    next_remote_dict = {}
    next_project_dict = {}
    parse_xml("vision_apps_next.xml", next_remote_dict, next_project_dict, workarea_path)

    # Parse the prod manifest
    print("Parsing prod manifest...")
    prod_remote_dict = {}
    prod_project_dict = {}
    parse_xml("vision_apps_prod.xml", prod_remote_dict, prod_project_dict, workarea_path)

    # Check for differences between next and prod projects 
    print("Checking differences between next and prod projects...")
    changes_dict = get_all_diff(next_project_dict, prod_project_dict, workarea_path)

    # Print the results
    print("Differences found in the following projects:")
    for name, data in changes_dict.items():    
        print(name, len(data))