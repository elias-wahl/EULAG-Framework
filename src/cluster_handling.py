import subprocess

def get_output_folders_of_running_slurm_jobs():
    """
    Retrieves the output folder names for the user's running Slurm jobs.
    """

    command = "squeue -u $(whoami) -o '%j %Z'"  # Get job ID and working directory
    process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if process.returncode == 0:
        output = process.stdout
        output_folders = []

        for line in output.splitlines()[1:]:  # Skip header line
            job_id, working_dir = line.split()
            output_folders.append(working_dir.split(sep='/')[-1])    # Append output folder

        return output_folders
    else:
        print(f"Error executing squeue: {process.stderr}")
        return []  # Return an empty list if there's an error


def check_if_job_is_running(job_name):
    """
    Checks if the user's job is running.
    """

    output_folders = get_output_folders_of_running_slurm_jobs()
    return job_name in output_folders

def check_how_many_jobs_are_running():
    """
    Checks how many jobs the user has running.
    """

    output_folders = get_output_folders_of_running_slurm_jobs()
    return len(output_folders)

def pause_until_next_job_can_start(job_name):
    """
    Pauses the script until the user's next job can start.
    """
    import time as t
    
    t_iter = 0
    while True:
        job_number = check_how_many_jobs_are_running()
        if not check_if_job_is_running(job_name):
            if job_number < 4:
                print(f"Job {job_name} is no longer running. Starting next job...")
                return
        else:  
            t_iter += 1  
            print(f"Job {job_name} is still running or too many jobs are running. Waiting for it to finish...")
            t.sleep(30)  # Sleep for 30 seconds
        if t_iter > 120:
            print("Job is taking too long to finish. Exiting...")
            quit()

def rename_turbs_file(job_name, time_step):
    """
    Renames the turb file to include the time step.
    """
    from config import OUTPATH
    import os
    # Get the output folder
    output_folder = os.path.join(OUTPATH, job_name)

    #rename the TurbSt file
    os.rename(os.path.join(output_folder, "turbs.nc"), os.path.join(output_folder, f"turbs{time_step}.nc"))
    os.rename(os.path.join(output_folder, "turbf.nc"), os.path.join(output_folder, f"turbf{time_step}.nc"))


def copy_tapef_file(job_name, time_step):
    """
    Copies the tape file to a new file with the time step.
    """
    from config import OUTPATH
    import os
    import time as t
    # Get the output folder
    output_folder = os.path.join(OUTPATH, job_name)

    #copy the tape file
    os.system(f"cp {os.path.join(output_folder, 'tapef.nc')} {os.path.join(output_folder, f'tapef{time_step}.nc')}")
    t.sleep(15)  # Sleep for 15 seconds

if __name__ == "__main__":
    import sys
    print("-" * 40)
    # get a job name from the command line
    if len(sys.argv) > 1:
        job_name = sys.argv[1]
        print(f"Job name: {job_name}")
    else:
        job_name = None
        print("No job name provided.")
    print("-" * 40)
    output_folders = get_output_folders_of_running_slurm_jobs()
    if output_folders:
        print("Output folders of your running Slurm jobs:")
        for folder in output_folders:
            if job_name == folder:
                print(f"- {folder} <-- This is the job you are looking for.")
            else:
                print(f"- {folder}")
    else:
        print("You have no running Slurm jobs.")
    print("-" * 40)
    print("Number of running jobs: ", check_how_many_jobs_are_running())
    print("Is the job you specified running? ", check_if_job_is_running(job_name))