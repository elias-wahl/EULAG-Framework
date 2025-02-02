"""
This is a wrapper to run EULAG. It allows to read and set parameters for EULAG and to save them as a config. 
It also saves the configs of a run in a log file and reload configs of previous runs.
With the help of cluster_handling one can also start a test series that restarts the simulation when needed.
"""
import re
import csv
from config.config import SOURCEPATH, OUTPATH, LOGPATH, ARCHIVEPATH, \
                        TESTCASE, CONFIGPATH, CLUSTER, DEFAULT_HELPER_LINE, \
                        DEFAULT_HELPER_PARA_NAME, DEFAULT_HELPER_VALUE

class Line2Read:
    """
    An object that stores the information of a line that is supposed to be read from a file.
    """    
    def __init__(self,
                 line,
                 para_name,
                 helper_para_name: str,
                 helper_value: str, 
                 helper_line: str,
                 pos_of_appearance: int,
                 whole_line: bool,
                 is_float: bool,
                 key_name: str
    ):
        """
        The constructor of the Line2Read class.

        Args:
            line (str): The beginning of the line that the parameter is in. Spaces can be omitted.
            para_name (str): The name of the parameter.
            helper_para_name (str): The name of the helper parameter that is found in the helper line and
            its value has to be equal to the helper value.
            helper_value (str): The value of the helper_para.
            helper_line (str): The line that is searched in the lines before the actual line to verify that the
            line is located in the right section of the code.
            pos_of_appearance (int): If the given description is not unique, the pos_of_appearance can be used to
            specify which appearance of the parameter is meant.
        """        
        self.line = line
        self.line_number = None
        self.para_name = para_name
        self.value = None  # the value that is read from the file
        self.helper_line = helper_line
        self.helper_para_name = helper_para_name
        self.helper_value = helper_value
        self.pos_of_appearance = pos_of_appearance #the position of the right list of matched parameter lines
        self.pos_counter = pos_of_appearance #will be changed during the search
        self.found = False
        self.whole_line = whole_line
        self.is_float = is_float
        self.key_name = key_name

class Line2Modify:
    """
    An object that stores the information of a line that is supposed to be modified in a file.
    """    
    def __init__(self,
                 line,
                 para_name,
                 value, #the new value that should be written in the file
                 helper_para_name: str,
                 helper_value: str,
                 helper_line: str,
                 pos_of_appearance: int,
                 whole_line: bool,
                 is_float: bool,
                 key_name: str
    ):
        """
        The constructor of the Line2Modify class.

        Args:
            line (str): The beginning of the line that the parameter is in. Spaces can be omitted.
            para_name (str): The name of the parameter.
            value (str): The new value that should be written in the file.
            helper_para_name (str): The name of the helper parameter that is found in the helper line and
            its value has to be equal to the helper value.
            helper_value (str): The value of the helper_para.
            helper_line (str): The line that is searched in the lines before the actual line to verify that the
            line is located in the right section of the code.
            pos_of_appearance (int): If the given description is not unique, the pos_of_appearance can be used to
            specify which appearance of the parameter is meant.
            whole_line (bool): If the whole line is the value of the parameter.
            is_float (bool): If the value of the parameter is a float.
            key_name (str): The name of the key in the dictionary and the unique identifier of the parameter.
        """        
        self.line = line
        self.line_number = None
        self.para_name = para_name
        self.value = str(value) #the new value that should be written in the file
        self.helper_line = helper_line
        self.helper_para_name = helper_para_name
        self.helper_value = helper_value
        self.pos_of_appearance = pos_of_appearance #the position of the right list of matched parameter lines
        self.pos_counter = pos_of_appearance
        self.found = False
        self.whole_line = whole_line
        self.is_float = is_float
        self.key_name = key_name
        
        if self.is_float and "." not in self.value and "e" not in self.value:
            self.value = self.value + "."

class FileModifier():
    """
    A class that is used to read and modify a file. It has two dictionaries "lines_to_read" and "lines_to_modify"
    that store the Line2Read and Line2Modify objects. The class has a method "modify_file" that reads the file, processes
    the lines to modify and the lines to read and writes the changes back to the file. The class also has a method
    "export_parameters" that exports the parameters that have been read and modified to a "parameters.csv" file.
    The class has a method "import_parameters" that imports the parameters that should be read and modified from a csv file.
    The class has a method "write_log" that writes the parameters that have been read and modified to a log file.
    """    
    def __init__(self, safe=True):
        """Initializes the FileModifier object with the dictionaries "lines_to_read", "lines_to_modify" and "line_archive".

        Args:
            safe (bool, optional): If safe is True, the program stops if a parameter found twice. Defaults to True.
        """        
        self.lines_to_read = {}
        self.lines_to_modify = {}
        self.line_archive = {}
        self.safe = safe
        self._add_all_parameters_to_archive()
        self.import_all_para_from_archive()
    
    def _properties_of_line(self, line):
        # Using a loop
        properties = {}
        for key, value in vars(line).items():
            properties[key] = value

        # Using a dictionary comprehension (more concise)
        properties = {key: value for key, value in vars(line).items()}
        return properties
    
    def _add_line_to_archive(self,
                             para_name,
                             line,
                             helper_para_name = DEFAULT_HELPER_PARA_NAME,
                             helper_value = DEFAULT_HELPER_VALUE,
                             helper_line = DEFAULT_HELPER_LINE,
                             pos_of_appearance = None,
                             whole_line = False,
                             is_float = False,
                             key_name = None):
        """
        Adds a new Line2Read object to the dictionary "line_archive" with all the parameters that are needed
        to find the parameter in the file "sunCAR30506.csh". If the parameter is to be modified, also a value
        has to be specified.

        Args:
            para_name (str): The name of the parameter in the file.
            line (str): The beginning of the line that the parameter is in. Spaces can be omitted.
            helper_para_name (str, optional): The name of the helper parameter that is found in the helper line and
            its value has to be equal to the helper value. Defaults to DEFAULT_HELPER_PARA_NAME.
            helper_value (str, optional): The value of the helper_para. Defaults to DEFAULT_HELPER_VALUE.
            helper_line (str, optional): The line that is searched in the lines before the actual line to verify that the
            line is located in the right section of the code. Defaults to DEFAULT_HELPER_LINE.
            pos_of_appearance (int, optional): If the given description is not unique, the pos_of_appearance can be used to
            specify which appearance of the parameter is meant. Defaults to None.
            whole_line (bool, optional): If the whole line is the value of the parameter. Defaults to False.
            is_float (bool, optional): If the value of the parameter is a float. Defaults to False.
            key_name (str, optional): The name of the key in the dictionary and the unique identifier of the parameter.
            Defaults to None, but is set to para_name if not specified.
        """            
        
        if key_name == None:
            key_name = para_name
        
        if helper_line != DEFAULT_HELPER_LINE:
            if helper_para_name == DEFAULT_HELPER_PARA_NAME and helper_value == DEFAULT_HELPER_VALUE:
                helper_para_name = None
                helper_value = None
        
        self.line_archive[key_name] = Line2Read(line, para_name, helper_para_name, helper_value, 
                                                 helper_line, pos_of_appearance, whole_line, is_float, key_name)
   
    def add_para(self, key_name, value = None):
        """
        Adds a parameter to the dictionary "lines_to_read" or "lines_to_modify" with the help of the line_archive.
        If now value is specified, the value of the parameter is read from the file. If a value is specified, the
        parameter is set to this value.
        
        Args:
            para_name (str): The name of the parameter that is supposed to be added.
            value (str, optional): The value of the parameter. Defaults to None.
        """        
        try:
            line = self.line_archive[key_name]
            line.value = value
            properties = self._properties_of_line(line)
            self.add_line(**properties)

        except KeyError:
            print(f"Warning: {key_name} not found in the archive.")
            quit()
 
    def add_line(self, 
                 key_name,
                 para_name,
                 line,
                 value,
                 helper_para_name = DEFAULT_HELPER_PARA_NAME,
                 helper_value = DEFAULT_HELPER_VALUE,
                 helper_line = DEFAULT_HELPER_LINE,
                 pos_of_appearance = None,
                 whole_line = False,
                 is_float = False,
                 **kwarg
    ):
        """Add a new Line2Modify object to the dictionary "lines_to_modify" or
        a new Line2Read object to the dictionary "lines_to_read".

        Args:
            key_name (str): The name of the key in the dictionary and the unique identifier of the parameter.
            para_name (str): The name of the parameter.
            line (str): The beginning of the line that the parameter is in. Spaces can be omitted.
            helper_para_name (str, optional): The name of the helper parameter that is found in the helper line and
            its value has to be equal to the helper value. Defaults to "TESTCASE".
            helper_value (str, optional): The value of the helper_para. Defaults to TESTCASE.
            helper_line (str, optional): The line that is searched in the lines before the actual line to verify that the
            line is located in the right section of the code. Defaults to '[^ ]+\s*\(\s*TESTCASE \s*==.*'.
            pos_of_appearance (_type_, optional): If the given description is not unique, the pos_of_appearance can be used to
            specify which appearance of the parameter is meant. Defaults to None.
            pos_of_appearance (_type_, optional): If the given description is not unique, the pos_of_appearance can be used to
            specify which appearance of the parameter is meant. Defaults to None.
            whole_line (bool, optional): If the whole line is the value of the parameter. Defaults to False.
            is_float (bool, optional): If the value of the parameter is a float. Defaults to False.
        """    
        if value == None:
            self.lines_to_read[key_name] = Line2Read(line, para_name, helper_para_name,
                                                        helper_value, helper_line, pos_of_appearance,
                                                        whole_line, is_float, key_name)
        else:
            self.lines_to_modify[key_name] = Line2Modify(line, para_name, str(value), helper_para_name,
                                                           helper_value, helper_line, pos_of_appearance,
                                                           whole_line, is_float, key_name)
            
    
    def check_for_right_section(self, line_obj, lines, i) -> bool:
        """
        This function searches for the first instance of the line_obj.helper_line before the line lines[i]
        and returns True if in this line the line_obj.helper_para_name is equal to the line_obj.helper_value.

        Args:
            line_obj (Line2Modify or Line2Read): The object that is checked.
            lines (list): The list of lines of the file.
            i (int): The index of the line that is checked.
        Returns:
            bool: True if the helper line is found and either the helper_para_name is equal to the helper_value or
            they are not given.
        """        
        for j in range(i, i-30, -1):
        # check if line_obj.helper_line is part of the current line
            if not re.search(line_obj.helper_line, lines[j]):
                continue
            
            # check if either the helper_para_name and helper_value are given
            if line_obj.helper_para_name or line_obj.helper_value:
                match = re.search(fr"{line_obj.helper_para_name}\s*==\s*{line_obj.helper_value}", lines[j])
                if match:
                    if line_obj.pos_counter != None:
                        line_obj.pos_counter -= 1
                    if line_obj.pos_counter == 0 or line_obj.pos_counter == None:
                        return True
                else:
                    return False
            #if no helper values are given, the function returns True if the helper line is found
            else: 
                if line_obj.pos_counter != None:
                        line_obj.pos_counter -= 1    
                if line_obj.pos_counter == 0 or line_obj.pos_counter == None:
                        return True
        return False

    def modify_file(self, filepath=SOURCEPATH):
        """
        Opens the file and reads the lines. Then it processes the lines to modify and the lines to read.
        The lines to modify are modified and the lines to read are read. The changes are written back to the file.

        Args:
            filepath (str, optional): The path to the file that should be modified. Defaults to SOURCEPATH.

        Returns:
            int: The number of lines that have been changed.
        """        
        for line_obj in self.lines_to_read.values():
            line_obj.found = False
        for line_obj in self.lines_to_modify.values():
            line_obj.found = False
        lines_changed = 0

        # Read the file and store lines
        with open(filepath, "r") as file:
            lines = file.readlines()

        # Process Lines to Modify and write changes (Modified)
    
        for key_name, line_obj in self.lines_to_modify.items():
            line_obj.pos_counter = line_obj.pos_of_appearance  
            # escape the line_obj.line and the para name to be used in the regex
            line_begin = re.escape(line_obj.line)
            para_name = re.escape(line_obj.para_name)  
            for i, line in enumerate(lines):
                # check if the line start with the line_begin
                if not re.match(fr"\s*{line_begin}", line):
                    continue
                
                # get the value of the parameter if it is found, else match is None
                match = re.search(fr"(^|[ ,\()])({para_name}\s*[=/ ]\s*)([^ /,\)\n]+)", line)  # Modified regex
                
                # checks if the parameter is found and if the 'right' paramter after the helper line is found
                if not (match and self.check_for_right_section(line_obj, lines, i)):
                    continue
                
                #warn and quit if the parameter is found multiple times
                if line_obj.found == True:
                    print(f"Warning: The parameter {key_name}/{line_obj.para_name} was found multiple times fitting the search criteria in in {SOURCEPATH}\
                            in line {line_obj.line_number} and {i + 1}.")
                    quit()
                
                value_with_operator = match.group(2)
                old_line = lines[i]
                if line_obj.whole_line:
                    lines[i] = re.sub(fr"{para_name}(.*)", f"{line_obj.para_name}{line_obj.value}", line, count=1)
                else:
                    lines[i] = re.sub(fr"{para_name}\s*[=/ ]\s*[^ /,\)\n]+", f"{value_with_operator}{line_obj.value}", line, count=1) 
                    
                line_obj.line_number = i + 1
                
                if lines[i] != old_line:
                    lines_changed += 1
                    print(f"{'Modified':>18}| {line_obj.line_number:>6} | -> {key_name:<17} = {line_obj.value:>15} | {line_obj.para_name:<5}")# | {lines[i]}")
                else:
                    print(f"{'Already Set':>18}| {line_obj.line_number:>6} | -> {key_name:<17} = {line_obj.value:>15} | {line_obj.para_name:<5}")# | {lines[i]}")
                
                line_obj.found = True
                if self.safe == False: break
            if line_obj.found == False:
                print(f"Warning: The parameter {key_name}/{line_obj.para_name} not found in {SOURCEPATH} with the search pattern {line_obj.helper_line},\
                        {line_obj.helper_para_name} = {line_obj.helper_value} and thus not written to the file.")
                quit()

        with open(filepath, "w") as file:    
            file.writelines(lines)

         # Process Lines to Read
       
        for key_name, line_obj in self.lines_to_read.items():
            line_obj.pos_counter = line_obj.pos_of_appearance
            
            # check if the parameter is not already in the lines_to_modify dictionary
            if key_name in self.lines_to_modify:
                continue
            
            # escape the line_obj.line and the para name to be used in the regex
            line_begin = re.escape(line_obj.line)
            para_name = re.escape(line_obj.para_name)  
            
            # go through all lines in the file
            for i, line in enumerate(lines):
                # check if the line start with the line_begin
                if not re.match(fr"\s*{line_begin}", line):
                    continue
            
                # if the parameter has the whole line attribute, the whole line after the parameter name
                # is counted as the parameter value
                if line_obj.whole_line:
                    match = re.search(fr"(^|[ ,\()])({para_name})(.*)", line)
                # get the value of the parameter if it is found, else match is None
                else:
                    match = re.search(fr"(^|[ ,\()]){para_name}\s*(=|/| )\s*([^ /,\)]+)", line)  # Modified regex
                # checks if the parameter is found and if the 'right' paramter afte the helper line is found 
                
                if not (match and self.check_for_right_section(line_obj, lines, i)):
                    continue
                
                #warn and quit if the parameter is found multiple times
                if line_obj.found == True:
                    print(f"Warning: Parameter {key_name}/{line_obj.para_name} found multiple times fitting the search criteria in in {SOURCEPATH}\
                            in line {line_obj.line_number} and {i + 1}.")
                    quit()

                if line_obj.whole_line:
                    line_obj.value = str(match.group(3))
                else:
                    line_obj.value = str(match.group(3).strip())
                
                line_obj.line_number = i + 1
                
                print(f"{'Read':>18} | {line_obj.line_number:>6} | -> {key_name:<17} = {line_obj.value:>15} | {line_obj.para_name:<5}")# | {line}")
                line_obj.found = True
                
                #break if the parameter is found: does not find duplicates, but runs faster
                if self.safe == False: break
                        
            if (line_obj.found == False):
                print(f"Warning:  Parameter {key_name}/{line_obj.para_name} not found in {SOURCEPATH} with the search pattern {line_obj.helper_line},\
                    {line_obj.helper_para_name} = {line_obj.helper_value} and pos_of_appearance = {line_obj.pos_of_appearance}.")

        print(f"\nTotal lines changed: {lines_changed}")
        return lines_changed
    
    def export_parameters(self, name_of_run = "", outpath=OUTPATH, file_name="parameters"):
        """
        Exports the parameters that have been read and modified to a "parameters.csv" file. The format is as follows:
        The first block contains the changed parameters and the second block contains the read parameters.
        The columns are "line_number", "line", "para_name", "value", "helper_para_name", "helper_value", "helper_line".

        Args:
            name_of_run (str, optional): The name of the run that is used in the outpath. If the name contains "RESTART",
            the name is shortened to the part after "RESTART" and the part before the first "_" is removed. In this case
            the parameters are saved to a "restart_parameters.csv" file. Defaults to "".
            outpath (str, optional): The path where the folder with the name_of_run is saved. Defaults to OUTPATH.
            file_name (str, optional): The name of the csv file. Defaults to "parameters".
        """        
        import re
        import os
        #get rid of the .csv ending if it is there
        file_name = re.sub(".csv", "", file_name)

        # if outpath is OUTPATH:
        if "RESTART" in name_of_run:
            outpath = outpath + re.sub(fr"RESTAR[^_]+_", "", name_of_run) + "/" + "restart_" + file_name + ".csv"
        else:
            outpath = outpath + name_of_run + "/" + file_name + ".csv"
        
        properties = self._properties_of_line(Line2Modify("", "", "", "", "", "", "", "","",""))
        del properties["pos_counter"]
        del properties["found"]

        #check if there is already a file with the same name
        if os.path.exists(outpath):
            print("-"*100)
            print(f"Warning: The file {outpath} already exists and will be overwritten.")
            print("Do you want to continue? (y/n)")
            if input() != "y":
                quit()
            
        with open(outpath, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            
            writer.writerow(["Changed parameters"])
            writer.writerow(properties)
            for line_obj in self.lines_to_modify.values():
                line_obj_properties = self._properties_of_line(line_obj)
                del line_obj_properties["pos_counter"]
                del line_obj_properties["found"]
                writer.writerow(line_obj_properties.values())

            writer.writerow([])
            writer.writerow(["Read parameters"])
            writer.writerow(properties)
            for line_obj in self.lines_to_read.values():
                if line_obj.value == None:
                    continue
                line_obj_properties = self._properties_of_line(line_obj)
                del line_obj_properties["pos_counter"]
                del line_obj_properties["found"]
                writer.writerow(line_obj_properties.values())

    def import_parameters(self, inpath="/"):
        """
        Imports the parameters that should be read and modified from a csv file. The format is the same as in the
        export_parameters method. The method reads the csv file and creates a new Line2Read or Line2Modify object for each
        row in the csv file. The object is then added to the dictionary "lines_to_read" or "lines_to_modify".

        Args:
            inpath (str, optional): The path to the csv file. Defaults to "/".
        """        
        #check if the inpath end with .csv

        if inpath[-4:] != ".csv":
            full_file_path = inpath + "/parameters.csv"
        else:
            full_file_path = inpath
        with open(full_file_path, "r") as csvfile:
            reader = csv.reader(csvfile)
            # Skip the first row
            _ = next(reader)  
            # Read the second row as header
            header = next(reader)
            
            # get the column indices of the parameters "key_name" and "value"
            try:
                key_name_index = header.index("key_name")
            except:
                print("No key_name column found in the csv file. Using para_name insted")
                key_name_index = header.index("para_name")
                
            value_index = header.index("value")
            # Read the rest of the rows
            for i, row in enumerate(reader, start=1):
                if row == []: 
                    continue # Skip empty rows
                elif row[0] in ["line", "line_number", "Changed parameters", "Read parameters"]:
                    continue # Skip header row
                elif row[3] == "":
                    print(f"Warning: {row[2]} has no value in the csv file in line number {i}.")
                    continue # Skip rows without a value
                    
                # extract the key_name and the value from the row
                key_name, value = row[key_name_index], row[value_index]

                # check if the parameter is known if the line archive
                if key_name not in self.line_archive:
                    print(f"Warning: {key_name} not found in the archive.")
                    continue
                
                # make sure the float values have a dot
                if self.line_archive[key_name].is_float and "." not in value and "e" not in value:
                    value = value + "."
                    
                # print out the imported parameters
                print(f"{'Imported':>18} | {key_name:<17} = {value:>15} | {row[2]:<5}")
                # add the parameter to the dictionary
                self.add_para(key_name, value)
    
    def write_log(self, run_name, logpath=LOGPATH):
        """
        Writes the parameters that have been read and modified to a log file. The format is as follows:
        It appends the parameters to the log file, where also older runs are stored. The first two columns are
        "name_of_run" and "date_time". The self.para_name are the rest of the header. If a self.para_name is not yet in the header,
        it is added to the header.

        Args:
            run_name (str): The name of the run that is used in the log file.
            logpath (str, optional): The path to the log file. Defaults to LOGPATH.

        """        
        
        INIT_HEADER = ['Started', 'Name', 'Notes']
        
        class Parameter:
            def __init__(self, para_name, value):
                self.para_name = para_name
                self.value = value

        def _read_first_line(logpath):
            try:
                with open(logpath, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    return next(reader)  # Get the first row as a list

            except: return []

        from datetime import datetime
        now = datetime.now()
        start_time = now.strftime("%d.%m.%y %H:%M")
        header = _read_first_line(logpath)
        name = Parameter("Name", run_name)
        time = Parameter("Started", start_time)
        notes = Parameter("Notes", "")
        
        init_dict = {}
        init_dict['Name'] = name
        init_dict['Started'] = time
        init_dict['Notes'] = notes

        all_params = {**init_dict, **self.lines_to_read, **self.lines_to_modify}
        for para_name, line_obj in all_params.items():
            if para_name not in header:
                header.append(para_name)

        # Read all lines except the first
        try:
            with open(logpath, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                # Skip the first line
                next(reader)
                remaining_lines = list(reader)
        except: remaining_lines = []
        
        
        new_line = []
        for para in header:
            if para in all_params:
                new_line.append(all_params[para].value)
            else:
                new_line.append("")
        
        # Write the new first line and the rest of the lines back to the file
        with open(logpath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            writer.writerows(remaining_lines)
            writer.writerow(new_line)

    def import_all_para_from_archive(self):
        """
        This method is enacted in the constructor of the class and adds all parameters that are in the archive.
        """        
        for key_name in self.line_archive.keys():
            self.add_para(key_name)
    
    def _add_all_parameters_to_archive(self): 
        """
        This method is enacted in the constructor of the class and adds the information below on how to find
        the parameters in the file "sunCAR30506.csh" such that they can be added easily by the method "add_para"
        without further information.
        """

        # For bgc
        self._add_line_to_archive("NNP", "set    NNP", key_name = "bgc_NNP",
                                  helper_line="#HELPER LINE", pos_of_appearance=1)
        
        self._add_line_to_archive("QUEUE", "setenv QUEUE", key_name = "bgc_QUEUE",
                                  helper_line="#HELPER LINE", pos_of_appearance=1)
    
        self._add_line_to_archive("DIR", "setenv DIR /Net", key_name= "bgc_DIR",
                                    whole_line=True, helper_line="#HELPER LINE",
                                    pos_of_appearance=1)
        self._add_line_to_archive("mpiifort", "mpiifort", helper_line="#HELPER LINE")
        
        
        # For levante
        self._add_line_to_archive("NNP", "set    NNP", key_name="levante_NNP",
                                  helper_line="#HELPER LINE", pos_of_appearance=2)
        
        self._add_line_to_archive("QUEUE", "setenv QUEUE", key_name="levante_QUEUE",
                                  helper_line="#HELPER LINE", pos_of_appearance=2)    
        
        self._add_line_to_archive("PROJECT", "setenv PROJECT", key_name="levante_PROJECT",
                                  helper_line="#HELPER LINE")

        self._add_line_to_archive("DIR", "setenv DIR /work", key_name= "levante_DIR",
                                    whole_line=True, helper_line="#HELPER LINE",
                                    pos_of_appearance=1)
                                
        self._add_line_to_archive("OUTPUTDIR", "#setenv OUTPUTDIR", whole_line=True,
                                helper_line="#HELPER LINE")
        
        self._add_line_to_archive("mpif90", "mpif90", helper_line="#HELPER LINE")        
         
        
        self._add_line_to_archive("TESTCASE", "#define TESTCASE", helper_line="!HELPER LINE")
        match TESTCASE:
            case "19":    
                self._add_line_to_archive("NPX", "setenv NPX", helper_line="#HELPER LINE")
                self._add_line_to_archive("NPY", "setenv NPY", helper_line="#HELPER LINE")
                self._add_line_to_archive("NPZ", "setenv NPZ", helper_line="#HELPER LINE")
                                       
                self._add_line_to_archive("NTIME", "setenv NTIME", helper_line="#HELPER LINE")
                self._add_line_to_archive("m", "parameter ")
                self._add_line_to_archive("n", "parameter ")
                self._add_line_to_archive("l", "parameter ")

                self._add_line_to_archive("dx00", "parameter ", is_float=True)
                self._add_line_to_archive("dy00", "parameter ", is_float=True)
                self._add_line_to_archive("dz00", "parameter ", is_float=True)
                self._add_line_to_archive("dt00", "parameter ", is_float=True)
                self._add_line_to_archive("dtmax", "parameter ", is_float=True)
                self._add_line_to_archive("lxyz", "parameter ")
            
                self._add_line_to_archive("nt", "parameter ")
                self._add_line_to_archive("noutp", "parameter ")
                self._add_line_to_archive("nplot", "&")
                self._add_line_to_archive("nstore", "&")

                self._add_line_to_archive("ibcx", "parameter ", pos_of_appearance=2) #Careful with the pos_of_appearance
                self._add_line_to_archive("ibcy", "parameter ", pos_of_appearance=2) #Depends on PARAMETER POLES
                self._add_line_to_archive("ibcz", "parameter ", pos_of_appearance=2)

                self._add_line_to_archive("isflx", "parameter ")
                self._add_line_to_archive("inoise","parameter ")
                self._add_line_to_archive("iblatt", "parameter ")
                self._add_line_to_archive("nspc", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("istr", "parameter ", pos_of_appearance=1)
                self._add_line_to_archive("zhz", "parameter ", is_float=True, pos_of_appearance=1)

                self._add_line_to_archive("imetryc", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("ivctype", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("ihorizdef", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("ivertdef", "parameter ", helper_line="!HELPER LINE")
            
                self._add_line_to_archive("isphere", "parameter ")
                self._add_line_to_archive("icylind", "parameter ")
                self._add_line_to_archive("icorio", "parameter ")
                self._add_line_to_archive("ideep", "parameter ")

                self._add_line_to_archive("TURBST", "#define")
                self._add_line_to_archive("TKE", "#define")
                self._add_line_to_archive("SGS", "#define")
                self._add_line_to_archive("CHEMIS", "#define")
                self._add_line_to_archive("IMRSB", "#define")
                self._add_line_to_archive("J3DIM", "#define")
                self._add_line_to_archive("MOISTMOD", "#define")
                self._add_line_to_archive("POLES", "#define")             

                self._add_line_to_archive("initi", "data")
                self._add_line_to_archive("lipps", "data")

                self._add_line_to_archive("iab", "data")
                self._add_line_to_archive("iabth", "data")
                self._add_line_to_archive("iabqw", "data")

                self._add_line_to_archive("dxabL", "data", is_float=True)
                self._add_line_to_archive("towxL", "data", is_float=True)  
                self._add_line_to_archive("dxabR", "data", is_float=True)
                self._add_line_to_archive("towxR", "data", is_float=True)
                self._add_line_to_archive("dyab", "data", is_float=True)
                self._add_line_to_archive("towy", "data", is_float=True)
                self._add_line_to_archive("zab", "data", is_float=True)
                self._add_line_to_archive("towz", "data", is_float=True)

                self._add_line_to_archive("g", "data", is_float=True)
                self._add_line_to_archive("rg", "data", is_float=True)
                self._add_line_to_archive("tt00", "data", is_float=True)
                self._add_line_to_archive("th00", "&  th00", is_float=True)
                self._add_line_to_archive("pr00", "&  th00", is_float=True)
                self._add_line_to_archive("rh00", "&  th00", is_float=True) 
            
                self._add_line_to_archive("u00", "data", is_float=True)
                self._add_line_to_archive("v00", "data", is_float=True)
                self._add_line_to_archive("st", "data", is_float=True)
                self._add_line_to_archive("u0z", "data", is_float=True)
                self._add_line_to_archive("v0z", "data", is_float=True)

                self._add_line_to_archive("fcr0", "data", pos_of_appearance=1, is_float=True)
                self._add_line_to_archive("ang", "data", pos_of_appearance=1, is_float=True)
                self._add_line_to_archive("initprs", "data", pos_of_appearance=1, is_float=True)

                self._add_line_to_archive("ceps", "data", pos_of_appearance=1, is_float=True)
                self._add_line_to_archive("cL", "data", pos_of_appearance=1, is_float=True)
                self._add_line_to_archive("cm", "data", pos_of_appearance=1, is_float=True)
                self._add_line_to_archive("css", "data", pos_of_appearance=1, is_float=True)
                self._add_line_to_archive("prndt", "data", pos_of_appearance=1, is_float=True)

                self._add_line_to_archive("hf00", "data", is_float=True)
                self._add_line_to_archive("qf00", "data", is_float=True)
                self._add_line_to_archive("cdrg", "data", is_float=True)
                self._add_line_to_archive("rghn", "data", is_float=True)

                self._add_line_to_archive("rv", "data", is_float=True)
                self._add_line_to_archive("t00", "data", is_float=True)
                self._add_line_to_archive("ee0", "data", is_float=True)
                self._add_line_to_archive("hlat", "data", is_float=True)
                self._add_line_to_archive("rl00", "data", is_float=True)
                self._add_line_to_archive("dtm", "data", is_float=True)

                self._add_line_to_archive("cour_max_allowed", "data cour_max_allowed", helper_line="!HELPER LINE", 
                                         is_float=True)
                self._add_line_to_archive("timeadapt", "data timeadapt", helper_line="!HELPER LINE")
                self._add_line_to_archive("ampns", "ampns", helper_line="!HELPER LINE",  is_float=True)
                
                #Restart Parameters
                self._add_line_to_archive("iwrite", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("iwrite0", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("irst", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("iomode", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("ismode", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("iopar", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("nfil", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("nfilm", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("nfilo", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("nfilom", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("dt_fil", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("nt_fil0", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("nt_film0", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("dt_filo", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("nt_filo0", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("nt_filom0", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("nfstart", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("nanlfl", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("idia", "parameter ", helper_line="!HELPER LINE")
                self._add_line_to_archive("nplo", "parameter ", helper_line="!HELPER LINE")
            
                self._add_line_to_archive("chmsrc", "chmsrc", helper_line="!HELPER LINE",  is_float=True)
                self._add_line_to_archive("chmflx", "chmflx", helper_line="!HELPER LINE",  is_float=True)
                
                # Landcover Class 1
                self._add_line_to_archive("zo(i,j)", "zo(i,j)", key_name="LC1_zo", helper_line="!HELPER LINE",  is_float=True, pos_of_appearance=1)
                self._add_line_to_archive("hfxp(i,j,:)", "hfxp(i,j,:)", key_name="LC1_hfxp", helper_line="!HELPER LINE", pos_of_appearance=1, whole_line=True)
                self._add_line_to_archive("qfxp(i,j,:)", "qfxp(i,j,:)", key_name="LC1_qfxp", helper_line="!HELPER LINE", pos_of_appearance=1, whole_line=True)
                self._add_line_to_archive("chmsrc(i,j,1)", "chmsrc(i,j,1)", key_name="LC1_chmsrc1", helper_line="!HELPER LINE",  is_float=True, pos_of_appearance=1)
                self._add_line_to_archive("chmsrc(i,j,2)", "chmsrc(i,j,2)", key_name="LC1_chmsrc2", helper_line="!HELPER LINE",  is_float=True, pos_of_appearance=1)
                self._add_line_to_archive("chmflx(i,j,1)", "chmflx(i,j,1)", key_name="LC1_chmflx1", helper_line="!HELPER LINE",  is_float=True, pos_of_appearance=1)
                
                # Landcover Class 0
                self._add_line_to_archive("zo(i,j)", "zo(i,j)", key_name="LC0_zo", helper_line="!HELPER LINE",  is_float=True, pos_of_appearance=2)
                self._add_line_to_archive("hfxp(i,j,:)", "hfxp(i,j,:)", key_name="LC0_hfxp", helper_line="!HELPER LINE", pos_of_appearance=2, whole_line=True)
                self._add_line_to_archive("qfxp(i,j,:)", "qfxp(i,j,:)", key_name="LC0_qfxp", helper_line="!HELPER LINE", pos_of_appearance=2, whole_line=True)
                self._add_line_to_archive("chmsrc(i,j,1)", "chmsrc(i,j,1)", key_name="LC0_chmsrc1", helper_line="!HELPER LINE",  is_float=True, pos_of_appearance=2)
                self._add_line_to_archive("chmsrc(i,j,2)", "chmsrc(i,j,2)", key_name="LC0_chmsrc2", helper_line="!HELPER LINE",  is_float=True, pos_of_appearance=2)
                self._add_line_to_archive("chmflx(i,j,1)", "chmflx(i,j,1)", key_name="LC0_chmflx1", helper_line="!HELPER LINE",  is_float=True, pos_of_appearance=2)

def flag_parser():
    #check for flags when running the script
    parser = argparse.ArgumentParser()
    #Add the arguments
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--default", default=False, action="store_true",\
                        help="Restore the sunCAR30506.csh file to its default state from the src/default.csv file")
    group.add_argument("-l", "--load", default=False, action="store_true",\
                        help="Load a specific configuration from the config (-c), the archive (-a) or the output (-o) folder.")
    group.add_argument("-s", "--save", default="",\
                        help="Save the current configuration as a configuration in the config folder with the name you set.")
    
    parser.add_argument("-c", "--config", default="", help="Set the name of the configuration you want to load from the config folder. Input the full name.")
    parser.add_argument("-a", "--archive", default="", help="Set the name of the archive folder you want to laod the parameter configuration from.")
    parser.add_argument("-o", "--output", default="", help="Set the name of the output folder you want to load the parameter configuration from.")
    return parser.parse_args()

if __name__ == "__main__":
    import argparse
    mod = FileModifier(safe=True)

    args = flag_parser()
    print("-"*100)
    # If '-c', '-a' or '-o'  is set but -l is not or if -l is set but no argument is given, print an error message.
    if args.default:
        try:
            mod.import_parameters("./src/default.csv")
        except FileNotFoundError:
            print("The file could not be found at ./src/default.csv.")
            quit()
        print("Do you really want to restore the sunCAR30506.csh file to its default state? (y/n)")
        answer = input()
        if answer != "y":
            print("No changes have been made.")
            quit()    
        mod.modify_file()

    elif args.load:
        if args.config == "" and args.archive == "" and args.output == "":
            print("Please specify the name of the configuration you want to load.")
            quit()
        else:
            path = ""
            try: 
                if args.config != "":
                    #get rid of the .csv ending if there
                    re.sub(r".csv", "", args.config)
                    path = f"{CONFIGPATH}/{args.config}.csv"
                elif args.archive != "":
                    path = ARCHIVEPATH + f"{args.archive}"
                elif args.output != "":
                    path = OUTPATH + f"{args.output}"
                
                mod.import_parameters(path)
                print("-"*100)
                print(f"Do you really want to load the configuration {args.config}? (y/n)")
                answer = input()
                
            except FileNotFoundError:
                print(f"The file could not be found in the directory {path}.")
                quit()        
            
            if answer != "y":
                print("No changes have been made.")
                quit()
            mod.modify_file()

    elif args.save != "":
        if args.config != "" or args.archive != "" or args.output != "":
            print("This will always save to the config folder. No need to specify the folder.")
            print("Do you you want to the save the current configuration in the config folder? (y/n)")
            answer = input()
            if answer != "y":
                print("No changes have been made.")
                quit()
        
        mod.modify_file()
        #get rid of the .csv ending if it is there
        file_name = re.sub(".csv", "", args.save)
        mod.export_parameters(outpath=CONFIGPATH, file_name=file_name)

        print(f"The configuration has been saved as {file_name}.csv in the config folder.")
    
    # if not option are specified
    else:
        mod.modify_file()


