# EULAG-Framework
The work I do around the EULAG simulation. Included are scripts that facilitate handling the code and postprocessing, as well as a script that generates a landcover map for the lower boundary of the simulation. The EULAG code is unfortunately not included, please contact Piotr Smolarkiewicz for that.

**src/**
- normally includes the EULAG source code
- also included are the following wrapper scripts that facilitate working with the code:
  - read_write_automation: parameter input/output, presets, log file and run series automation
  - test_series: basic building blocks and examples to use read_write_automation for actual runs and test series
  - cluster_handling: an auxiliary module that helps to communicate and check with the cluster

**surface_model/**
- this is used to generate land cover maps for the simulation's lower boundary
- lake_statistics: this is the script that generates the land covers
- fields/: the generated landcover are saved in here
- variograms/: if the landscapes should be generated with the statistics of a given variogram, the variogram data is read from here

**post_proc/**
- this directory is dedicated to post-processing
- create_thumbnail: allows the creation of pictures for runs to have a brief overview without needing to load big chunks of data
- parameter: reads the parameters of a run from the parameter snapshot generated from read_write_automation and allows for easy access through a dictionary
- save_perm: save run folders from the working directory to an archive
- load_again: loads run folders from the archive to the work directory so they can be used as starting points for reruns

**config/**
- config: includes all paths that are custom for each user and system
