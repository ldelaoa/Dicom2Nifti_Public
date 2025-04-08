from Dicom2Nii_Funs import convert_dicom_to_nifty
import numpy as np
import re
import pandas as pd
import os
import yaml
import logging
import pydicom as pdcm
from tqdm import tqdm

def openYaml():
    with open('config_Dicom2Nii.yaml', 'r') as stream:
        config = yaml.safe_load(stream)
        
        itvtot = config['itv_tot_labels']
        itvtum = config['itv_tumor_labels']
        itvnod = config['itv_ln_labels']
        
        gtvtot = config['gtv_tot_labels']
        gtvtum = config['gtv_tumor_labels']
        gtvnod = config['gtv_ln_labels']
    
        
        #source_csv_path = config['source_csv']
        source_csv_path = "C:/Users/delaOArevaLR/OneDrive - UMCG/Ch2/XLS/TrainingTestingCohort_WithBPandITV_paths.csv"
        save_path = "//zkh/appdata/RTDicom/Projectline_modelling_lung_cancer/Users/Luis/CT_ITV_GTV_XBP_Nii_v2/"
        #save_path = config['save_path']

        #source_csv_path = "C:/Users/delaOArevaLR/OneDrive - UMCG/Scans/NBIA_4d/NBIA4d_DicomSelectedPaths.csv"
        #save_path = "C:/Users/delaOArevaLR/OneDrive - UMCG/Scans/NBIA_4d/Nifti_Selected/"

        #source_csv_path = "C:/Users/delaOArevaLR/OneDrive - UMCG/Scans/REACT/REACT_DicomSelectedPaths.csv"
        #save_path = "C:/Users/delaOArevaLR/OneDrive - UMCG/Scans/REACT/Selected_REACT_Nifti/"
        
    
    df = pd.read_csv(source_csv_path)
    target_labels = itvtot + itvtum+itvnod+gtvtot+gtvtum+gtvnod

    return df,target_labels,save_path

def FilteredIDs():
    id_file_path = "C:/Users/delaOArevaLR/OneDrive - UMCG/Ch2/CheckCT_Dicom2NiiAgain.txt"
    
    with open(id_file_path, 'r') as id_file:
        ids = id_file.read().splitlines()
    #ids2 = ["659641","986614","9061277","7391514","3740147","7475016","6874374","3930261","9375818","8847536","5468590","9443032","282824","102687","2610935","9646447","7867220","9854449","3853415"]
    return ids

def LookForPlanCT_GTV_ITV_InNii(path_Nii):
    missingCT_bool,missingITV_bool,missingGTV_bool,missingBPCT_bool = (True,True,True,True)
    for f in os.listdir(path_Nii):
        if "ave" in f.lower() or  "2,5mm" in f.lower() or "25mm" in f.lower() or "3mm" in f.lower() :
            missingCT_bool= False
        if "gtv" in f.lower() and not "igtv" in f.lower():
            missingGTV_bool = False
        if "itv" in f.lower() or "igtv" in f.lower():
            missingITV_bool = False    
        if "BPCT" in f:
            missingBPCT_bool = False
            
    return missingCT_bool,missingITV_bool,missingGTV_bool,missingBPCT_bool

def convertPlanCT(CT_path,patientID,save_path,filename):
    ct_name = CT_path.split("\\")[-1]
    
    Filename=filename+ct_name
    input_filepaths = []

    for currSlide in os.listdir(CT_path):
        input_filepaths.append(os.path.join(CT_path,currSlide))
    try:
        image, pixel_spacing, image_position_patient,axial_positions = convert_dicom_to_nifty(input_filepaths,str(patientID),
                                save_path,[],extension='.nii.gz',filename="CT_"+Filename,
                                pixel_spacing = None, image_position_patient=None,axial_positions=None,
                                np_image=None,dtype_image=np.float32,dtype_mask=np.uint8,)
    except:
        print(f"Error in {patientID} CT")
        print(CT_path)
        pass
            
    return  image, pixel_spacing, image_position_patient,axial_positions,ct_name
    
def convertRT(RT_path,patientID,save_path,bp_name,target_labels,image, pixel_spacing, image_position_patient,axial_positions):
    Filename="RTstruct"+bp_name+"_"
    #singleRT_path = os.path.join(RT_path,os.listdir(RT_path)[0])
    singleRT_path = RT_path
    try:

        image, pixel_spacing, image_position_patient,axial_positions = convert_dicom_to_nifty([singleRT_path],str(patientID),
                                save_path,target_labels,extension='.nii.gz',filename="RT_"+Filename,
                                pixel_spacing = pixel_spacing, image_position_patient=image_position_patient,axial_positions=axial_positions,
                                    np_image=image,dtype_image=np.float32,dtype_mask=np.uint8,)
    except:
        print(f"Error in {patientID} RT")
        print(RT_path)
        pass


    return 1

def main():
    df,target_labels,save_path = openYaml()
    df['pxID'] = df['pxID'].astype(str)

    for _, row in tqdm(df.iterrows()):
        patientID = row['pxID']
        CT_path = row['CT']
        RT_path = row['RT']
        save_path_px = os.path.join(save_path,patientID)
        if not(os.path.exists(save_path_px)): 
            os.makedirs(save_path_px)

        image, pixel_spacing, image_position_patient,axial_positions,bp_name = convertPlanCT(CT_path,patientID,save_path,"PlanCT_")

        convertRT(RT_path,patientID,save_path,bp_name,target_labels,image=image, pixel_spacing=pixel_spacing, image_position_patient=image_position_patient,axial_positions=axial_positions)

if __name__ == "__main__":
    main()