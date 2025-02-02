"""A simple script that copies folders from the permanent storage to the working directory.
    This is neccessary if the user wants to use the data from a previous run in a new run.
"""
import sys
from config.config import OUTPATH, ARCHIVEPATH


# Reads the string that the folder names start with from the command line
try:
    starts_with = sys.argv[1]
except IndexError:
    print("Please provide a string that the folder names start with")
    quit()

# Checks if the user provided a new name for the folders
new_name = None
try:
    new_name = sys.argv[2]
except:
    pass

def copy_to_perm(starts_with: str):
    """Copies folders from the permanent storage to the working directory.

    Args:
        statrs_with (str): The string that the folder names start with.
    """    
    import os
    import shutil
    #count the number of folder that start with the string "starts_with"
    count = 0
    for folder in os.listdir(ARCHIVEPATH):
        if folder.startswith(starts_with):
            count += 1
    print(f"Do you want to copy {count} folders that start with {starts_with} from the permanent storage to the OUTDIR? (y/n)")
    answer = input()
    if answer == "y":
        print("#"*40)
        #copy all folders that start with the string "starts_with" to the permanent storage
        for folder in os.listdir(ARCHIVEPATH):
            if folder.startswith(starts_with):
                print(f"Copying {folder}...")
                new_folder = folder
                if new_name is not None:
                    old_name = folder.split("_")[0]
                    new_folder = folder.replace(old_name, new_name)
                #if the folder already exists in the permanent storage do not copy and print a message
                if os.path.exists(OUTPATH+ new_folder):
                    print(f"{folder} already exists in the permanent storage and thus was not copied.")
                else:
                    shutil.copytree(ARCHIVEPATH + folder, OUTPATH + new_folder, symlinks=True)
                    print("Done.")
                print("-"*40)
        print("#"*40)
        print("All folders were copied")
    else:
        print("Nothing was copied")

if __name__ == "__main__":
    copy_to_perm(starts_with)