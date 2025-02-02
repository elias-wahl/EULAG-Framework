"""A simple script that copies folders from the working directory to the permanent storage.
    This is neccessary if the user wants to save the data from a run for later use.
"""
import sys
import imp
imp.load_source("path_config", "../config/path_config.py")
from path_config import OUTPATH, ARCHIVEPATH

starts_with = sys.argv[1]
new_name = None

try:
    new_name = sys.argv[2]
except:
    pass

def copy_to_perm(starts_with: str):
    """Copies folders from the working directory to the permanent
    """    
    import os
    import shutil
    #count the number of folder that start with the string "starts_with"
    count = 0
    for folder in os.listdir(OUTPATH):
        if folder.startswith(starts_with):
            count += 1
    print(f"Do you want to copy {count} folders that start with {starts_with} to the permanent storage? (y/n)")
    answer = input()
    if answer == "y":
        print("#"*40)
        #copy all folders that start with the string "starts_with" to the permanent storage
        for folder in os.listdir(OUTPATH):
            if folder.startswith(starts_with):
                print(f"Copying {folder}...")
                new_folder = folder
                if new_name is not None:
                    old_name = folder.split("_")[0]
                    new_folder = folder.replace(old_name, new_name)
                #if the folder already exists in the permanent storage do not copy and print a message
                if os.path.exists(ARCHIVEPATH + new_folder):
                    print(f"{folder} already exists in the permanent storage and thus was not copied.")
                else:
                    shutil.copytree(OUTPATH + folder, ARCHIVEPATH + new_folder, symlinks=True)
                    print("Done.")
                print("-"*40)
        print("#"*40)
        print("All folders were copied")
    else:
        print("Nothing was copied")

copy_to_perm(starts_with)