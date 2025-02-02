class Parameters():
    """A class to read and store parameters from the parameters.csv file.
    """    
    def __init__(self, outpath: str):
        """Initializes the Parameters class.
        
        Args:
            outpath (str): The path to the run output directory.
        """
        self.outpath = outpath
        self.dict = {}
        self.total_timesteps = 0
        self.domain_sizes = {}
        self._read_parameters()

    def __setitem__(self, key, value):
        self.dict[key] = value
    
    def __getitem__(self, key):
        return self._para_read(key)

    def _para_read(self, para_name: str):
        """Reads the parameter value from the dictionary.
        """        
        try:
            return eval(self.dict[para_name])
        except:
            return float(self.dict[para_name])
    
    def _read_parameters(self):
        """Reads in the parameters from the parameters.csv file and stores them in the dictionary.
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
                self[row[2]] = row[3]
       
        self.total_timesteps = self['nt'] // min((self['nplot']), self['nstore'])
        self.domain_sizes = {'t': self.total_timesteps,
                            'x': self['n'],
                            'y': self['m'],
                            'z': self['l']}
