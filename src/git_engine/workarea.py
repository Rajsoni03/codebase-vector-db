from git import Repo
import xml.etree.ElementTree as ET
from pprint import pprint
import os 
import subprocess
import requests
import json
import multiprocessing


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
def check_repo_diff(args, workarea_path):
    project_name, next_dict, prod_dict = args
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

        next_repo.git.fetch(remote, next_branch)
        prod_repo.git.fetch(remote, prod_branch)

        # Check if the revision is a tag or branch
        if prod_branch.startswith("refs/tags/"):
            diff_with_prod = next_repo.git.diff(prod_branch)
        else:
            diff_with_prod = next_repo.git.diff(f"{remote}/{prod_branch}")
        print(f"Adding diff for {project_name}:")
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