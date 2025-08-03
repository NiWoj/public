#!/usr/bin/env python


import sys
sys.path.append('/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules')
import DaVinciResolveScript
import os

resolve_utils_path = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Examples"

if resolve_utils_path not in sys.path:
    sys.path.append(resolve_utils_path)

import python_get_resolve

from python_get_resolve import GetResolve

# Create project and set parameters:
resolve = GetResolve()
projectManager = resolve.GetProjectManager()
project = projectManager.GetCurrentProject()
mediapool = project.GetMediaPool()

FolderList = mediapool.GetRootFolder().GetSubFolderList()

Footage = None
found = False

OriginalFolder = mediapool.GetCurrentFolder()

for folder in FolderList:
    if folder.GetName() == 'Footage':
        Footage = folder 
        CurrentFolder = mediapool.SetCurrentFolder(Footage)
        found = True
        break
    elif folder.GetSubFolderList() != None:
        for subfolder in folder.GetSubFolderList():
            if subfolder.GetName() == 'Footage':
                Footage = subfolder 
                CurrentFolder = mediapool.SetCurrentFolder(Footage)
                found = True
                break
    if found == True:
        break

if Footage == None:
    print("🔴 No bin 'Footage' found")
    sys.exit()

def format_meta(prefix, value):
    return f"{prefix}{value}" if value else ""

def rename_clip(clip, folder):

    Name = clip.GetName()
    if Name:
        print(f"🟢 Found {Name}")

    name_part, ext = os.path.splitext(Name)


    MetaScene =  format_meta("_", clip.GetMetadata("Scene"))
    if not MetaScene:
        print(f"🟡 No Scene Metadata found for {Name}")
    MetaCam =  format_meta("_", clip.GetMetadata("Camera #"))
    if not MetaCam:
        print(f"🟡 No Camera Metadata found for {Name}")
    MetaTake =  format_meta("_", clip.GetMetadata("Take"))
    if not MetaTake:
        print(f"🟡 No Take Metadata found for {Name}")
    MetaKey =  format_meta("_", clip.GetMetadata("Description"))
    if not MetaKey:
        print(f"🟡 No Description found for {Name}")


    NewName = f"{name_part}{MetaCam}{MetaScene}{MetaTake}{MetaKey}{ext}"

    if Name == NewName:
        print (f"🟡 {Name} skipped")
        return

    source_path = clip.GetClipProperty("File Path")
    

    new_path = source_path.replace(f"{Name}", f"{NewName}")  
    clip.SetClipProperty("Clip Name", NewName)
    clip.SetClipProperty("File Name", NewName) 
    os.rename(source_path, new_path)  
    print(f"🟢 Renamed {Name} to {NewName}")    

    Relink = mediapool.ImportMedia([new_path])   
    mediapool.DeleteClips([clip]) 
    if Relink:
        print(f"🟢 Relinking {NewName} was succesful")
    else:
        print(f"🔴 Relinking {NewName} failed")
    
    

def rename_clips_in_folder(folder):
    for clip in folder.GetClipList():
        rename_clip(clip, folder) 

    for subfolder in folder.GetSubFolderList():
        mediapool.SetCurrentFolder(subfolder)
        rename_clips_in_folder(subfolder)

rename_clips_in_folder(Footage)

mediapool.SetCurrentFolder(OriginalFolder)
    

projectManager.SaveProject()
sys.exit()
