import subprocess

from constants import AppConstants
AppConstants = AppConstants()


# Check if the current processing XML file has a diff with the wanted processing file. When true, change the files
def compare_processing_file(procFile):
    diffPath = "bash " + str(AppConstants.HANDLER_PATH) + str(AppConstants.LOCAL_PROCESS_DIR) + \
               "diffProcessing.sh " + str(AppConstants.HANDLER_PATH) + str(AppConstants.LOCAL_PROCESS_DIR) + procFile
    diff = subprocess.check_output(diffPath, shell=True)
    if len(diff) > 0:
        change_processing_file(procFile)
        return
    return


# Change the processing XML with help of a bash script
def change_processing_file(procFile):
    changePath = "bash " + str(AppConstants.HANDLER_PATH) + str(AppConstants.LOCAL_PROCESS_DIR) + \
               "changeProcessing.sh " + str(AppConstants.HANDLER_PATH) + str(AppConstants.LOCAL_PROCESS_DIR) + procFile
    subprocess.check_output(changePath, shell=True)
    return
