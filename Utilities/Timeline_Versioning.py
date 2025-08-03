#!/usr/bin/env python

"""
This script will duplicate the currently active timeline and store the original timeline in an 'Archive'folder.
It looks for the following naming convention: Name_CreationDate(_VersionSuffix), for example "My Timeline_250803_A"
In the duplicate's name dates will be updated and suffixes added if multiple versions are generated on the same day.
"""
import sys
sys.path.append('/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules')
import DaVinciResolveScript
import os
import re
from datetime import datetime

resolve_utils_path = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Examples"

if resolve_utils_path not in sys.path:
    sys.path.append(resolve_utils_path)

import python_get_resolve

from python_get_resolve import GetResolve

def increment_letter(label):
    letters = list(label)
    i = len(letters) - 1

    while i >= 0:
        if letters[i] != 'Z':
            letters[i] = chr(ord(letters[i]) + 1)
            return ''.join(letters)
        else:
            letters[i] = 'A'
            i -= 1

    # All were Zs, add a new letter at the front
    return 'A' + ''.join(letters)

def generate_unique_timeline_name(base_name):
    suffix = ''
    final_name = base_name
    while get_timeline_by_name(project, final_name):
        suffix = increment_letter(suffix or 'A')  # 'A', 'B', 'C'...
        final_name = f"{base_name}_{suffix}"
    return final_name


def get_timeline_by_name(project, name):
    for i in range(project.GetTimelineCount()):
        tl = project.GetTimelineByIndex(i + 1)
        if tl.GetName() == name:
            return tl
    return None


def find_timeline_parent_folder(folder, target_timeline):

    for item in folder.GetClipList():
        if item.GetName() == target_timeline:
            if item.GetClipProperty("Type") == "Timeline":
                return folder
    for subfolder in folder.GetSubFolderList() or []:
        found = find_timeline_parent_folder(subfolder, target_timeline)
        if found:
            return found
    return None


# Open project and navigate to current project:
resolve = GetResolve()
projectManager = resolve.GetProjectManager()
project = projectManager.GetCurrentProject()
mediapool = project.GetMediaPool()
timeline = project.GetCurrentTimeline()
if not timeline:
    print("🔴 No timeline currently open")

#Get current timeline name
t_name = timeline.GetName()


#Get current compact_date

now = datetime.now()
compact_date = now.strftime("%y%m%d")  # e.g., "250724"

new_timeline = None
existing = None

#Search for current date in timeline name
#if timeline name includes current date:

if compact_date in t_name:
    print("🟢 Current timeline has current date")
    #if date is in last position:
    if re.search(rf"{compact_date}$", t_name):
        #duplicate current timeline and name the duplicate "original timeline name_B"
        new_version = generate_unique_timeline_name(f"{t_name}_B")
        if new_version:
                print(f"🟢 New version name set to be '{new_version}'")
        else:
            print(f"🔴 Generating a new timeline name failed")
        new_timeline = timeline.DuplicateTimeline(f"{new_version}")
        if new_timeline:
            print(f"🟢 Created new timeline '{new_version}'")
        else:
            print(f"🔴 Failed to create a new timeline")
        #rename original timeline to "original timeline name_A"
        rename = timeline.SetName(f"{t_name}_A")
        if rename:
            print(f"🟢 Renamed '{timeline.GetName()}' to '{t_name}_A")
            timeline = get_timeline_by_name(project, f"{t_name}_A")
        else:
            print(f"🔴 Renaming '{timeline.GetName()}' failed")
    #elif name ends with "_suffix" eg. (timelinename_250724_D)
    elif re.search(rf"{compact_date}_([A-Z]+)$", t_name):
        #duplicate current timeline and name the duplicate "original timeline name_(letter+1)" eg. "timelinename_250724_E"
        pattern = re.search(r"(.*_)([A-Z]+)$", t_name)
        base_name = pattern.group(1)  # e.g., "Timeline_250724_"
        current_suffix = pattern.group(2)  # e.g., "D"
        next_suffix = increment_letter(current_suffix)
        new_version = generate_unique_timeline_name(f"{base_name}{next_suffix}")
        if new_version:
            print(f"🟢 New version name set to be '{new_version}'")
        else:
            print(f"🔴 Generating a new timeline name failed")

        new_timeline = timeline.DuplicateTimeline(f"{new_version}")
        if new_timeline:
            print(f"🟢 Created new timeline '{new_version}'")
        else:
            print(f"🔴 Failed to create a new timeline")
    else:
        new_version = generate_unique_timeline_name(f"{t_name}_{compact_date}")
        if new_version:
            print(f"🟢 New version name set to be '{new_version}'")
        else:
            print(f"🔴 Generating a new timeline name failed")

        new_timeline = timeline.DuplicateTimeline(f"{new_version}")
        if new_timeline:
            print(f"🟢 Created new timeline '{new_version}'")
        else:
            print(f"🔴 Failed to create a new timeline")


#else:
else:
    #if name ends in other date:
    if re.search(r"(.*?)[_\-]([0-9]{6})$", t_name):
        print("🟢 Current timeline ends with older date")
        pattern = re.search(r"(.*?)[_\-]([0-9]{6})$", t_name)
    
        # Replace old date with today’s compact date
        base_version = f"{pattern.group(1)}_{compact_date}"

        # Check if a timeline with that name already exists
        existing = get_timeline_by_name(project, base_version)
        if existing:
            print("🟡 Timeline with current date already exists")
            # Rename the existing one to "_A"
            new_existName = generate_unique_timeline_name(f"{base_version}_A")
            rename = existing.SetName(new_existName)
            if rename:
                print(f"🟢 Renamed '{timeline.GetName()}' to '{new_existName}' ")
            else:
                print(f"🔴 Renaming '{timeline.GetName()}' failed")
            existing = get_timeline_by_name(project, new_existName)


            # Generate a safe new version name like "_B", "_C", etc.
            new_version = generate_unique_timeline_name(base_version)
            if new_version:
                print(f"🟢 New version name set to be '{new_version}'")
            else:
                print(f"🔴 Generating a new timeline name failed")


        else:
            new_version = generate_unique_timeline_name(base_version) 
            if new_version:
                print(f"🟢 New version name set to be '{new_version}' ")
            else:
                print(f"🔴 Generating a new timeline name failed")
        
        # Duplicate timeline under that new name
        new_timeline = timeline.DuplicateTimeline(new_version)
        if new_timeline:
            print(f"🟢 Created new timeline '{new_version}'")
        else:
            print(f"🔴 Failed to create a new timeline")

    #elif name ends in ..._date_suffix
    elif re.search(r"([0-9]{6})_([A-Z]+)$", t_name):
        pattern = r"([0-9]{6})_([A-Z]+)$"
        #duplicate timeline and name name_currentdate
        new_version = generate_unique_timeline_name(f"{t_name.replace(pattern, compact_date)}")
        if new_version:
            print(f"🟢 New version name set to be '{new_version}'")
        else:
            print(f"🔴 Generating a new timeline name failed")
        new_timeline = timeline.DuplicateTimeline(f"{new_version}")
        if new_timeline:
            print(f"🟢 Created new timeline '{new_version}'")
        else:
            print(f"🔴 Failed to create a new timeline")
    #else:
    else:
        #duplicate current timeline and name the duplicate "original timeline name_currentdate"
        print(f"🟡 No date convention 'YY/MM/DD'  found in '{timeline.GetName()}'")
        new_version = generate_unique_timeline_name(f"{t_name}_{compact_date}")
        if new_version:
            print(f"🟢 New version name set to be '{new_version}'")
        else:
            print(f"🔴 Generating a new timeline name failed")
        new_timeline = timeline.DuplicateTimeline(f"{new_version}")
        if new_timeline:
            print(f"🟢 Created new timeline '{new_version}'")
        else:
            print(f"🔴 Failed to create a new timeline")


#check if current timeline mediapool folder contains sub-folder "Archive"
root = mediapool.GetRootFolder()
t_folder = find_timeline_parent_folder(root, timeline.GetName())
if not t_folder:
    print("🔴 Could not find parent folder for this timeline.")
    sys.exit()
mediapool.SetCurrentFolder(t_folder)
archive = None
subfolders = t_folder.GetSubFolderList()
for folder in subfolders:
    if "archive" in folder.GetName().lower():
        archive = folder
        break
#if not
if archive is None:
    print("🟡 No folder 'Archive' (or similar) found")
    #create subfolder "Archive"
    archive = mediapool.AddSubFolder(t_folder, "Archive")
    print("🟡 Created new folder 'Archive' at original timeline location")
else:
    print(f"🟢 'Archive' folder located at original timeline location")

#Set duplicate to be the current timeline
jump = project.SetCurrentTimeline(new_timeline)
if jump:
    print(f"🟢 Succesfully opened new timeline'{new_version}'")
else:
    print(f"🔴 Failed to jump to new timeline")

#Move original timeline into "Archive" folder
timeline_original = timeline.GetMediaPoolItem()
if timeline_original:
    print(f"🟡 Moving {timeline_original.GetName()} to folder 'Archive' ")
move = mediapool.MoveClips([timeline_original], archive)
if move:
    if find_timeline_parent_folder(archive, timeline_original.GetName()) is not None:
        print(f"🟢 Migration of {timeline_original.GetName()} successful")
else: 
    print(f"🔴 Migration of {timeline_original.GetName()} to 'Archive' failed")

if existing is not None:
    if find_timeline_parent_folder(archive, existing.GetName()) is None:
        mediapool.MoveClips([existing.GetMediaPoolItem()], archive)
        

if jump:
    print(f"🟢 Succesfully opened new timeline'{new_version}'")
else:
    print(f"🔴 Failed to jump to new timeline")


#Save project
projectManager.SaveProject()
sys.exit()


