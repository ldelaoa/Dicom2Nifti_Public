import os
import shutil
from tqdm import tqdm

# Specify the path where the folders are located
path = "//zkh/appdata/RTDicom/Projectline_modelling_lung_cancer/DICOM_data/DATA_VOLLEDIG_unstructured"

# Specify the path to the text file containing the IDs
id_file_path = "C:/Users/delaOArevaLR/OneDrive - UMCG/Ch2/CheckCT_Dicom2NiiAgain.txt"

# Specify the path to the new folder where you want to copy the files
#new_folder_path = "//zkh/appdata/RTDicom/Projectline_modelling_lung_cancer/DICOM_data/DATA_VOLLEDIG_unstructured/"
new_folder_path = "//zkh/appdata/RTDicom/Projectline_modelling_lung_cancer/Users/Luis/DataToDRE/"

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

with open(id_file_path, 'r') as id_file:
    ids = id_file.read().splitlines()

# Loop over the folders in the specified path
for folder_name in tqdm(os.listdir(path)):
    # If the folder name is in the list of IDs
    if folder_name in ids:
        # Construct the full path to the folder
        folder_path = os.path.join(path, folder_name)
        # If the path is a directory
        if os.path.isdir(folder_path):
            # Copy the directory to the new folder
            copytree(folder_path, os.path.join(new_folder_path, folder_name))
