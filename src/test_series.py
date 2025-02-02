import subprocess
from read_write_automation import FileModifier
from cluster_handling import check_if_job_is_running
from config.config import SOURCEPATH, OUTPATH, LOGPATH, ARCHIVEPATH

class Simulation():
    """
    A class to run series of EULAG simulations.
    """    
    def __init__(self, name):
        """
        Initializes the Simulation object.

        Args:
            name (str): Either the name of the series or the name of the run.
        """        
        self.mod = FileModifier()
        self.series_name = name
        self.run_name = name #if the run is a run series the name later will be changed for every run
        self.export = True
        self.log = True
        self.modify = True
        
    def general_params(self):
        """
        Sets the general parameters for the EULAG runs.

        Returns:
            str: The name of the series.
        """    
        mod = self.mod

        mod.add_para("NPX", 8)
        mod.add_para("NPY", 2)
        mod.add_para("NPZ", 4)

        mod.add_para("NTIME")
        #number of grid cell in x, y, z direction
        mod.add_para("n", 256)
        mod.add_para("m", 64)
        mod.add_para("l", 128)
        #domain length in x, y, z direction
        mod.add_para("dx00", 600.0)
        mod.add_para("dy00", 150.0)
        mod.add_para("dz00", 300.0)
        #reference for one time step 
        mod.add_para("dt00", 0.3)
        mod.add_para("timeadapt", 1)
        mod.add_para("cour_max_allowed", 0.8)

        mod.add_para("TURBST", 0)

        mod.add_para("u00", 0.0)
        mod.add_para("v00", 0.0)
        mod.add_para("st", 0.0)
        mod.add_para("u0z", 0.016666667)
        mod.add_para("v0z", 0.003333333)

        mod.add_para("nt", '20*200')
        mod.add_para("nplot", '5*200')
        mod.add_para("nstore", '10*200')
        mod.add_para("noutp", '5*200')
        
        mod.add_para("iab", 1)
        mod.add_para("iabth", 1)
        mod.add_para("inoise", 1)

        mod.add_para("iblatt", 0)
        mod.add_para("icorio", 0)

        mod.add_para("hf00", 0.0)
        mod.add_para("zab", 200.0)
        mod.add_para("towz", 3600.0)
        mod.add_para("iwrite0", 1)
        mod.add_para("dt_fil", 0.3)
        mod.add_para("nfil", 7)
        mod.add_para("nfilm", 6)
        mod.add_para("nfilo", 100)
        mod.add_para("nfilom", 99)
        mod.add_para("nfstart", 100)
        mod.add_para("nt_film0", 0)
        mod.add_para("nt_filom0", 100)
        mod.add_para("nanlfl", 1)
        mod.add_para("irst", 1)
    

    def run_name_is_duplicate(self):
        """
        reads all the names of the runs from the log.csv file
        from the column that has "Name" as the header
        if self.run_name is not in the list, it returns True
        It also checks if there is a folder in the outpath that has self.run_name in it.

        Returns:
            bool : If the name is a duplicate or not.
        """    
        
        import csv
        name = self.run_name
        
        with open(LOGPATH, "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)
            for i, line in enumerate(csv_reader):
                #check if the name is in the line
                if name not in line:
                    continue
                
                print(f"ERROR: {name} is already in the log file in the row {i}")
                return True
        
        #check if the name is already in the outpath
        import os
        for folder in os.listdir(OUTPATH):
            if name not in folder:
                continue
            print(f"ERROR: {name} is already in the outpath")
            return True
    
        #if the name is not in the log file or in the outpath  
        return False

    def modify_file_and_run_eulag(self):
        """
        Modifies the file with all parameters that were specified (if self.modifiy != False)
        and the starts a EULAG job with the name self.run_name. It also exports the parameters
        and writes the log file if self.export and self.log are True respectively.
        """
        import re
        run_name = self.run_name
        log_name = self.run_name
        mod = self.mod
        
        #check if the name is a duplicate
        if self.run_name_is_duplicate():
            return
        
        #set the parameters for the run
        if self.modify:
            mod.modify_file()
        
        # get rid of the restart prefix
        run_name = re.sub(fr"RESTAR[^_]+_", "", run_name)
        #run the job
        subprocess.run([SOURCEPATH, run_name])
                
        print("EULAG JOB STARTED:", run_name)
        print("---------------------------------")
        print("")
        print("")
        
        #export the parameters and write the log
        if self.export:
            mod.export_parameters(log_name)
        if self.log:
            mod.write_log(log_name)

    def restart_runs(self, restart_number = None):
        """
        Restarts all runs that start with the beginning_run_name.
        It reads the parameters from the archive and modifies them for the restart.
        
        Args:
            beginning_run_name (str): The beginning of the name of the runs to be restarted.
            restart_number (int, optional): The number of the restart. Defaults to None.
        """    
        import os
        
        #import the parameters from the archive
        mod = self.mod
        beginning_run_name = self.series_name
        full_dir_path = {}
        for folder in os.listdir(OUTPATH):
            if not folder.startswith(beginning_run_name):
                continue    
            full_dir_path[folder] = OUTPATH + folder + "/"
        
        answer = input(f"Do you want to restart {len(full_dir_path)} runs? (y/n)")
        if answer != "y":
            print("Aborted")
            quit()

        for folder, dir in full_dir_path.items():
            #check if run is already running
            if check_if_job_is_running(folder):
                print(f"Run {folder} is already running")
                continue
            
            mod.import_parameters(dir)
            #set parameters for restart
            mod.add_para("nt", '20*200')
            mod.add_para("nplot", '5*200')
            mod.add_para("nstore", '10*200')
            mod.add_para("noutp", '5*200')
            
            mod.add_para("dt00", 0.3)
            mod.add_para("timeadapt", 0) #This should always be zero when writing turbst
            
            mod.add_para("irst", 1)
            mod.add_para("dt_fil", 0.3)
            mod.add_para("nfil", 7)
            mod.add_para("nfilm", 6)
            mod.add_para("nfilo", 100)
            mod.add_para("nfilom", 99)
            mod.add_para("nfstart", 100)
            mod.add_para("nt_film0", 0)
            mod.add_para("nt_filom0", 100)
            mod.add_para("nanlfl", 1)
            mod.add_para("iwrite0", 1)
            mod.add_para("TURBST", 1) #Disable timeadapt if TURBST is 1!

            self.run_name = f"RESTART{restart_number}_{folder}"
            self.modify_file_and_run_eulag()

    def no_mod_just_run(self):
        """
        Runs a single EULAG run with the given name without modifying the parameters.
        """    
        self.modify = False
        self.modify_file_and_run_eulag()
        
    def rerun_with_modified_params(self, old_run_name):
        """
        Reruns a single run with modified parameters.

        Args:
            old_run_name (str): The name of the run to be rerun.
        """
        mod = self.mod
    
        mod.import_parameters(OUTPATH + old_run_name)
        
        # modify the parameters here
        
        # # EXAMPLE:
        # mod.add_para("nt", '1')
        # mod.add_para("nplot", '1')
        # mod.add_para("nstore", '1')
        # mod.add_para("noutp", '1')
        TOWZ = [100, 200]
        ZAB = [150, 200]
        run_name = self.run_name
        for towz in TOWZ:
            for zab in ZAB:
                mod.add_para("towz", towz)
                mod.add_para("zab", zab)
                self.run_name = run_name + f"_towz{towz}_zab{zab}"
                self.modify_file_and_run_eulag()
        
    def test_series_courant_number(self):
        """
        Runs a series of EULAG runs with different courant numbers.
        """    
        
        NAME_OF_SERIES = self.series_name
        #set the general parameters for the run
        self.general_params()
        # list of courant numbers to be tested
        CRN =  [0.65, 0.75]#[0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
        
        mod = self.mod
        mod.add_para("TKE", 0)
        mod.add_para("timeadapt", 1)
        mod.add_para("dt00", 0.5)
        mod.add_para("ideep", 0)
        mod.add_para("nt", '9*60*60')
        mod.add_para("nplot", '30*60')
        mod.add_para("nstore", '10*60*60')
        mod.add_para("noutp", '20*60')
        
        
        for crn in CRN:
            #change the noise amplitude
            mod.add_para("cour_max_allowed", crn)
            #name of the run
            self.run_name = NAME_OF_SERIES + "_crn" + str(crn).replace(".", "dot")
            self.modify_file_and_run_eulag()


    def test_series_different_nois_ampns(self):
        """
        Runs a series of EULAG runs with different noise amplitudes.
        """    
        mod = self.mod        
        NAME_OF_SERIES = self.series_name
    
        
        AMPNS = [0.3, 1.8, 3.0, 4.0]
        rghn = 0.0
        
        mod.import_parameters(OUTPATH + "DIANA_rghn0dot0_ampns1dot4")
        mod.add_para("TKE", 0)
        mod.add_para("SGS", 0)
        mod.add_para("rghn", rghn) 

        for ampns in AMPNS:
            #change the noise amplitude
            mod.add_para("ampns", ampns)

            #name of the run
            self.run_name = NAME_OF_SERIES  + "_rghn" + str(rghn).replace(".", "dot") + "_ampns" + str(ampns).replace(".", "dot")
            self.modify_file_and_run_eulag()

    def test_series_different_rghn(self):
        """
        Runs a series of EULAG runs with different rghn values.
        """    
        mod = self.mod
        NAME_OF_SERIES = self.series_name
        
        RGHN_SERIES = [0.3, 0.0001, 0.00005, 0.7]
        ampns = 0
        
        mod.import_parameters(OUTPATH + "DIANA_rghn0dot0_ampns1dot4")
        mod.add_para("TKE", 1)
        mod.add_para("SGS", 1)
        mod.add_para("ampns", ampns) 
        
        
        for rghn in RGHN_SERIES:
            #change the noise amplitude
            mod.add_para("rghn", rghn)
            #name of the run
            self.run_name = NAME_OF_SERIES + "_ampns" + str(ampns).replace(".", "dot") + "_rghn" + str(rghn).replace(".", "dot")
            self.modify_file_and_run_eulag

    def convergence_test(self, old_run_name, first_iteration = 1):
        """
        Runs a EULAG run that is restarted multiple times to get a different
        turbs file for each restart. Comparing the quantities of interest in the
        different turbs files can give an idea of the convergence of the simulation.

        Args:
            run_name (str): The name of the run.
            old_run_name (str): The name of the file to load the parameters from.
            first_iteration (int, optional): The number of the first iteration. Defaults to 1.
        """    
        import time as t
        from cluster_handling import pause_until_next_job_can_start
        from cluster_handling import rename_turbs_file
        from cluster_handling import copy_tapef_file

        mod = self.mod
        run_name = self.run_name
        # if the test is started from the very beginning the first run is a 'normal' run
        if first_iteration == 1:
            mod.import_parameters(OUTPATH + old_run_name)
            mod.add_para("TURBST", 1)
            mod.add_para("timeadapt", 0)
            mod.add_para("dt00", 0.3)
            mod.add_para("nt", '20*200')
            mod.add_para("nplot", '5*200')
            mod.add_para("nstore", '10*200')
            mod.add_para("noutp", '5*200')
            mod.add_para("irst", 0)
            mod.add_para("iwrite0", 0)
            mod.add_para("nfil", first_iteration)
            mod.add_para("nfilm", first_iteration - 1)
            self.modify_file_and_run_eulag()
            
            # wait for the first run to finish
            pause_until_next_job_can_start(run_name)
            rename_turbs_file(run_name, first_iteration)
            copy_tapef_file(run_name, first_iteration)
        
        # set the following runs as restarts
        mod.add_para("irst", 1)
        
        # disable the export and log for the restarts
        self.export = False
        self.log = False 
        
        # start the loop for the following runs
        for i in range(first_iteration + 1, 36):
            restart_run_name = f"RESTART{i}_{run_name}"
            self.run_name = restart_run_name
            
            mod.add_para("nfil", i)
            mod.add_para("nfilm", i-1)

            # export the parameters of the first restart run
            if i == first_iteration + 1:
                mod.export_parameters(restart_run_name)
            
            # modify the source code an run the sim
            self.modify_file_and_run_eulag(export=False, log=False)

            # wait until the job is finished
            pause_until_next_job_can_start(run_name)
            
            # file managment
            rename_turbs_file(run_name, i)
            copy_tapef_file(run_name, i)


if __name__ == "__main__":
    print("Open the file to set up your run.")
    
    """ 
        Set up the name of your single run or the name of the series when intializing the Simulation object
    """   
    sim = Simulation("BLITZCRANK")
   
    """
    You can then the methods of the class to do different kind of runs or series of runs
    Have a look at the methods and customize them to your needs.
    Use the general_params method to set parameters you will have the same for most runs you will do.
    """
    
    #EXAMPLES:
    #sim.restart_runs(1)
    #sim.no_mod_just_run()
    #sim.rerun_with_modified_params("my_old_run")
    #sim.test_series_courant_number()
    #sim.test_series_different_nois_ampns()
    #sim.test_series_different_rghn()
    #sim.convergence_test("DIANA_rghn0dot0_ampns1dot4", 1)

