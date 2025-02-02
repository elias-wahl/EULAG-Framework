global SOURCEPATH, OUTPATH, LOGPATH, ARCHIVEPATH, TESTCASE, CLUSTER, CONFIGPATH, \
        DEFAULT_HELPER_LINE, DEFAULT_HELPER_PARA_NAME, DEFAULT_HELPER_VALUE

"""
SOURCEPATH: The path to the EULAG source code.
OUTPATH: The path to the output folder where the run directories will be saved.
LOGPATH: The path to the log file.
ARCHIVEPATH: The path to the archive folder, whre run directories are moved to for long-term storage.
CONFIGPATH: The path to the config folder.
TESTCASE: The testcase you will be running.
CLUSTER: The cluster you are running on ∈{"bgc", "levante"}

The following only change, if you know what you are doing. The default values for the corresponding names.
Documentation for these parameters can be found in read_write_automation.py.

DEFAULT_HELPER_LINE: The default for the helper line in read_write_automation.py.
DEFAULT_HELPER_PARA_NAME: The default for the helper parameter name in read_write_automation.py.
DEFAULT_HELPER_VALUE: The default for the helper value in read_write_automation.py.
"""


RUN_INSTANCE = "bgc_elias"

if RUN_INSTANCE == "LOCAL":
    SOURCEPATH = "/home/ewahl/Documents/EULAG/src/sunCAR30506.csh"
    OUTPATH = "/home/ewahl/Documents/EULAG/src/"
    LOGPATH = "/home/ewahl/Documents/EULAG/src/log.csv",
    ARCHIVEPATH = "/home/ewahl/Documents/EULAG/src/"
    TESTCASE = "19"

if RUN_INSTANCE == "bgc_elias":
    
    #PATHS
    SOURCEPATH = "/Net/Groups/BSI/people/ewahl/EULAG_dev/src/sunCAR30506.csh" #t
    OUTPATH = "/Net/Groups/BSI/scratch/ewahl/EULAG_out/"
    LOGPATH = "/Net/Groups/BSI/people/ewahl/EULAG_dev/config/log.csv"
    ARCHIVEPATH = "/Net/Groups/BSI/work/EULAG/better_EULAG_archive/"
    CONFIGPATH = "/Net/Groups/BSI/people/ewahl/EULAG_dev/config/"
    
    #OTHER
    TESTCASE = "19"
    CLUSTER = "bgc"
    
    #Only change, if you know what you are doing
    DEFAULT_HELPER_LINE = "[^ ]+\s*\(\s*TESTCASE \s*==.*" 
    DEFAULT_HELPER_PARA_NAME = "TESTCASE"
    DEFAULT_HELPER_VALUE = TESTCASE



