from config.config import OUTPATH, LOGPATH

class Thumbnails():
    """Thumbnail class that creates preview pictures of the simulation results.
    """    
    def __init__(self, 
                filepath: str = "/", 
                outpath: str = OUTPATH,
                slice_of = "u",
                specific_coord_name: str = "y",
                specific_time: int = 1,
                specific_coord: int = 0,
                show_plot: bool = False):
        """Initializes the Thumbnail class with the given parameters.

        Args:
            filepath (str, optional): Filepath to the tape file. Defaults to "/".
            outpath (str, optional): Path to the output folder. Defaults to OUTPATH.
            slice_of (str, optional): Field to plot. Defaults to "u".
            specific_coord_name (str, optional): Name of the coordinate to slice. Defaults to "y".
            specific_time (int, optional): Time of the slice. Defaults to 1.
            specific_coord (int, optional): Value of the specific coordinate at the slice. Defaults to 0.
            show_plot (bool, optional): Show the plot. Defaults to False.
        """        
        self.filepath = filepath
        self.outpath = outpath
        self.slice_of = slice_of
        self.specific_coord_name = specific_coord_name
        self.specific_time = specific_time
        self.specific_coord = specific_coord
        self.show_plot = show_plot  
        self.make_new_folder = False
        self.field = None
        self.slice = None
        self.domain_sizes = None
        self.total_timesteps = None
        self.args = None
        self.parameters = {}
    
    def _open_netcdf(self):
        """Opens the netcdf file and reads the parameters.
        """        
        self.parameters = {}
        self.domain_sizes = None
        try:
            self._read_parameters()
            if not self._is_finished():
                print("-"*50)
                print(f"WARNING: The simulation of run {self.outpath} is not finished yet. Skipping. ")
                print("-"*50)
                return
        except(FileNotFoundError, TypeError) as e:
            print("-"*50)
            print(f"WARNING: Could not check if run {self.outpath} is finished. Plot anyway? (y/n)")
            if input() != "y":
                print("Skipping...")
                print("-"*50)    
                return
        
        for file_letter in ['s', 'f']:
            self.filepath = self.outpath + fr"tape{file_letter}.nc" 
            print(f"Opening {self.filepath}")   
            try:
                self._read_netcdf()
                break
            except ImportError:
                print("-"*50)
                print("WARNING: Could not import xarray")
                print("-"*50)
                quit()
            except FileNotFoundError:
                print("-"*50)
                print(f"WARNIN: Could not find {self.filepath}")
                print("-"*50)
                return None
        
        if self.domain_sizes is None:
            print("-"*50)
            print(f"WARNING: Could not find a tape in {self.outpath}")
            print("Skipping...")
            print("-"*50)
            return None
        
        return self.domain_sizes

    def _read_netcdf(self):
        """Reads the netcdf file and gets the field and the slice.
        """        
        import xarray as xr
        dataset = xr.open_dataset(self.filepath)
        self.field = dataset[self.slice_of]
        self._get_slice()
        self.domain_sizes = {'t': self.field.sizes['t'] ,
                            'x': self.field.sizes['x'] ,
                            'y': self.field.sizes['y'] ,
                            'z': self.field.sizes['z']}
    
    def _get_slice(self):
        """Gets the slice of the field at the specific time and coordinate.
        """        
        try:
            self.slice = self.field.sel(t=self.specific_time, **{self.specific_coord_name: self.specific_coord})

        except:
            print(f"Could not find a slice with {self.specific_coord_name}={self.specific_coord} and t={self.specific_time}")
            print("Skipping...")
            print("-"*50)
        return self.slice
    
    def _read_run_names(self):
        """Reads the run names from the log file.
        """        
        import csv
        run_names = []
        with open(LOGPATH, "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)
            for line in csv_reader:
                run_names.append(line[1])
        return run_names

    #a function that checks if there is any png file in the folder
    def _check_for_png(self, run_name: str = None):
        """Checks if there are any png files in the folder.

        Args:
            run_name (str, optional): Name of the run. Defaults to None.

        Returns:
            bool: True if there are png files in the folder, False otherwise.
        """        
        import os
        if run_name is not None:
            folder_path = self.outpath + run_name + "/"
        else:
            folder_path = self.outpath
        try:
            for file in os.listdir(folder_path):
                if file.endswith(".png"):
                    return True
        except: 
            print(f"Could not find any files in {self.outpath}, which is in the log file.")
            return True
        return False
    
    def _plot(self):
        """Plots the slice of the field.
        """        
        from matplotlib import pyplot as plt
        from numpy import linspace

        axis = ['x','y','z']
        axis_dict = {'x': "dx00", 'y': "dy00", 'z': "dz00"}
        axis.remove(self.specific_coord_name)

        d100 = self.para_read(axis_dict[axis[0]])
        d200 = self.para_read(axis_dict[axis[1]])
        d300 = self.para_read(axis_dict[self.specific_coord_name])
        n1_grid_points = self.domain_sizes[axis[0]]
        n2_grid_points = self.domain_sizes[axis[1]]
        n3_grid_points = self.domain_sizes[self.specific_coord_name]
        
        #get coordinates for rescalled grid
        x1 = linspace(0, d100, n1_grid_points)
        x2 = linspace(0, d200, n2_grid_points)
        coords = {axis[0]: x1, axis[1]: x2}
        slice_remap = self.slice.assign_coords(coords)
        
        #get coordinates for interpolated grid
        x1_interp = linspace(0, d100, 2 * n1_grid_points)
        x2_interp = linspace(0, d200, 2 * n2_grid_points)
        coords_interp = {axis[0]: x1_interp, axis[1]: x2_interp}
        interp_field = slice_remap.interp(coords=coords_interp, method='linear')
        max_val = interp_field.max().values
        min_val = interp_field.min().values
  
        filename = f'{self.slice_of}_{self.specific_coord_name}{self.specific_coord}_t{self.specific_time}'
        current_nt = self.specific_time*min(self.para_read("nplot"), self.para_read("nstore"))
        title = f"{self.slice_of} - field at {self.specific_coord_name}={self.specific_coord} ({self.specific_coord*d300/n3_grid_points:.2f} m)"\
              + f" at nt={current_nt}, i.e. approx. ({current_nt*self.para_read('dt00')/3600:.2f} h)"\
              + f" with min={min_val:.2f} and max={max_val:.2f}\n"\
              + self.outpath.split("/")[-2]
        fig, ax = plt.subplots()#figsize=(10, round(d200/d100 * 10)))
        #plt.figure(figsize=(10, round(d200/d100 * 10)))#x1_size, x2_size))  # Adjust figure size as needed
        
        fig.suptitle(title)
        #set the colorbar
        ax.set_xlabel(axis[0])
        ax.set_ylabel(axis[1])

        interp_field.plot(ax=ax, cmap = 'viridis', add_colorbar=True)
        # Set equal aspect ratio
        ax.set_aspect('equal')
        
        if self.show_plot:
            plt.show()
        else:   
            # Save the plot to a file
            plt.savefig(self.outpath + str(filename))   # Replace with your output path
            if self.make_new_folder == True:
                #create new folder if it does not exist
                import os
                run_name = self.outpath.split("/")[-2]
                run_series_name = run_name.split("_")[0]
                print("Creating folder: ", OUTPATH + run_series_name + "/")
                os.makedirs(OUTPATH + run_series_name + "/", exist_ok=True)
                plt.savefig(OUTPATH + run_series_name + "/" + "_[" + self.slice_of + "]_" + self.specific_coord_name\
                             + str(self.specific_coord) + "_t" + str(self.specific_time) + "_" + run_name + ".png")

            plt.close()
    
    def _plot_slice_of_specific(self):
        """Reads the netcdf file and plots the slice of the field for one specific time and coordinate.
        """        
        self._read_netcdf()
        self._plot()
    
    #TODO these should be methods of a new class parameters 
    def _read_parameters(self):
        """Reads the parameters from the csv file.
        """        
        import csv
        with open(self.outpath + "parameters.csv") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) < 4:
                    continue
                elif row[2] == "" or row[3] == "":
                    continue
                elif row[2] == "para_name":
                    continue
                self.parameters[row[2]] = row[3]

        self.total_timesteps = (self.para_read('nt') // min((self.para_read('nplot')), self.para_read('nstore')))+1
        self.domain_sizes = {'t': self.total_timesteps,
                            'x': self.para_read('n'),
                            'y': self.para_read('m'),
                            'z': self.para_read('l')}

    def para_read(self, para_name: str):
        """Reads the parameter from the parameters dictionary.
        """        
        try:
            return eval(self.parameters[para_name])
        except:
            return float(self.parameters[para_name])

    def _is_finished(self):
        """Checks if the simulation is finished.
        """        
        current_timesteps = self.domain_sizes['t']
        if self.total_timesteps == current_timesteps:
            return True
        return False
    
    def create_thumbnails(self):
        """Creates thumbnails for the simulation results.
        """        
        if self._open_netcdf() == None:
            return
            
        t_tenth = (self.domain_sizes['t']-1) / 10
        t_series = [int(round(t_tenth * 2.5 * i)) for i in range(5)]

        for t in t_series:
            self.specific_time = t
            self.specific_coord = 0
            #xz-plane
            self.slice_of = "u"
            self.specific_coord_name = "y"
            self._plot_slice_of_specific()

            #yz-plane
            self.slice_of = "v"
            self.specific_coord_name = "x"
            self._plot_slice_of_specific()
        
        z_tenth = (self.domain_sizes['z'] - 1) / 10
        z_series =  [int(round(z_tenth * 2.5 * i)) for i in range(5)]
        for z in z_series: 
            #xy-plane
            self.slice_of = "w"
            self.specific_coord_name = "z"
            self.specific_coord = z
            self.specific_time = t_series[3]
            self._plot_slice_of_specific()
        
    def thumbnails_for_all(self, beginning_run_name: str = None):
        """Creates thumbnails for all the simulation results that start with the given name.
        """
        self.show_plot = False
        if beginning_run_name is not None:
            import os
            full_dir_path = list()
            for folder in os.listdir(self.outpath):
                if folder.startswith(beginning_run_name):
                    full_dir_path.append(OUTPATH + folder + "/")
        else:
            full_dir_path = [OUTPATH + run_name + "/" for run_name in self._read_run_names()]
        for dir in full_dir_path:
            self.outpath = dir
            if not self._check_for_png():
                try:
                    self.create_thumbnails()
                except IndexError:
                    print(f"Tape of run {self.outpath} is not ready yet.") 
                    continue
            else:
                if self.args.name != "":
                    print(f"Skipping {dir} because it already has png files in it.")

    def thumbnail_for_specific(self, beginning_run_name: str):
        """Creates a specific thumbnail for a specific run that starts with the given name.
        """
        import os
        full_dir_path = list()
        for folder in os.listdir(self.outpath):
            if folder.startswith(beginning_run_name):
                full_dir_path.append(OUTPATH + folder + "/")
        for dir in full_dir_path:
            self.outpath = dir
            if self._open_netcdf() == None:
                continue
            self._read_netcdf()
            self._plot_slice_of_specific()

    def delete_thumbnails(self, beginning_run_name):
        """Deletes the thumbnails for the simulation results that start with the given name.
        """        
        import os
        count = 0
        for folder in os.listdir(self.outpath):
            if folder.startswith(beginning_run_name):
                if self._check_for_png(folder):
                    count += 1
        print(f"Found {count} folders with the name {beginning_run_name} that have png files in them.")
        if (count==0) or (input("Do you want to delete the pictures in them? (y/n)") == "y"):
            for folder in os.listdir(self.outpath):
                if folder.startswith(beginning_run_name):
                    folder_path = self.outpath + folder + "/"
                    for file in os.listdir(folder_path):
                        if file.endswith(".png"):
                            os.remove(folder_path + file)
                    print(f"Deleted all the png files in {folder_path}")
        else:
            print("Did not delete anything")
            quit()

def flag_parser():
    """Parses the flags from the command line.
    """    
    import argparse
    parser = argparse.ArgumentParser()
    #Add the arguments
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--delete", default=False, action="store_true",\
                    help="Delete all the png files in the folders that start with the given name")
    group.add_argument("-r", "--reload", default=False, action="store_true",\
                    help="Reload the thumbnails for the folders that start with the given name")
    group.add_argument("-s", "--specific", default=False, action="store_true",\
                    help="Create a specific thumbnail for a specific runs starting with the given name")
    parser.add_argument("-nf", "--new_folder", default=False, action="store_true", help="Create a new folder for the thumbnails.")
    #Parse the arguments
    parser.add_argument("-n", "--name", default="", help="Set the beginning of the run name you want to modify.")
    parser.add_argument("-f", "--field", default="u", help="Set the field you want to plot.")
    parser.add_argument("-t", "--time", default=1, help="Set the time of the slice you want to plot.")
    parser.add_argument("-cn", "--coord_name", default="y", help="Set the coordinate name of the slice you want to plot.")
    parser.add_argument("-c", "--coord", default=1, help="Set the coordinate of the slice you want to plot.")
    return parser.parse_args()

if __name__ == "__main__":
    #Read in the arguments.
    args = flag_parser()
    
    #Create an instance of the Thumbnails class
    tn = Thumbnails()
    tn.args = args
    
    if args.delete:
        if args.name == "":
            print("Please provide a name with the -n argument")
            quit()
        print(f"Deleting thumbnails for runs in the outpath that start with {args.name}")    
        tn.delete_thumbnails(args.name)
    
    elif args.reload:
        if args.name == "":
            print("Please provide a name with the -n argument")
            quit()
        print(f"Reloading thumbnails for runs in the outpath that start with {args.name}")
        tn.delete_thumbnails(args.name)
        tn.thumbnails_for_all(args.name)

    elif args.specific:
        if args.name == "":
            print("Please provide a name with the -n argument")
            quit()
        print(f"Creating a specific thumbnail for the run in the outpath that starts with {args.name}")
        tn.slice_of = args.field
        tn.specific_time = int(args.time)
        tn.specific_coord_name = args.coord_name
        tn.specific_coord = int(args.coord)
        tn.make_new_folder = args.new_folder
        tn.thumbnail_for_specific(args.name)    

    else:
        if args.name == "":
            print("Creating thumbnails for all runs in the outpath")
        if args.name != "":
            print(f"Creating thumbnails for runs in the outpath that start with {args.name}")
        tn.thumbnails_for_all(args.name)




