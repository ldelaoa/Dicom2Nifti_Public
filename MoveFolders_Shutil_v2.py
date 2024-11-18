# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 15:39:01 2024

@author: delaOArevaLR
"""

IDS = ["1174472","1396853","1397990","1426704","1430520","1499147","2000368","2090413","2096249","2168777","2174844","2183919","2196013","2226259","2271692","2323531","2327063","2370962","2374240","2659861","2851836","3330761","3932820","4241082","4962318","5468590","6300771","6629816","7391514","759818","7759459","7867220","8034617","8248305","8812408","9235768","9236751","9375818","9854449","986614"]

import os
import shutil
from tqdm import tqdm 

def copy_folders_by_id(source_dir, dest_dir, listofID2copy):
    
    # Ensure destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    for currID in tqdm(listofID2copy):
        
        source_folder = os.path.join(source_dir, currID)
        
        if os.path.exists(source_folder) and os.path.isdir(source_folder):
    
            dest_folder = os.path.join(dest_dir, currID)
            
            try:
                shutil.copytree(source_folder, dest_folder)
            except Exception as e:
                print(f"Failed to copy {currID}: {e}")
        else:
            print(f"Folder {currID} does not exist in the source directory")

# Example usage
source_directory = '//zkh/appdata/RTDicom/Projectline_modelling_lung_cancer/Users/Luis/CT_ITV_GTV_XBP_NII_(170)'
destination_directory = '//zkh/appdata/RTDicom/Projectline_modelling_lung_cancer/Users/Luis/CT_ITV_GTV_XBP_NII_(170)_2transfer'
listofID2copy = ["1174472","1396853","1397990","1426704","1430520","1499147","2000368","2090413","2096249","2168777","2174844","2183919","2196013","2226259","2271692","2323531","2327063","2370962","2374240","2659861","2851836","3330761","3932820","4241082","4962318","5468590","6300771","6629816","7391514","759818","7759459","7867220","8034617","8248305","8812408","9235768","9236751","9375818","9854449","986614"]

copy_folders_by_id(source_directory, destination_directory, listofID2copy)
