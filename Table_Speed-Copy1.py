from Dicom2Nii_Funs import convert_dicom_to_nifty
import numpy as np
import re
import pandas as pd
import csv
import os
import yaml
import nibabel as nib
from rt_utils import RTStructBuilder
import pydicom as pdcm

def saveOnCSV(data):
    file_path = "C:/Users/delaOArevaLR/OneDrive - UMCG/Code/Code_From_Umcg/UMCG_ImageFormattingCode/Dicom2Nifti_Public/Logs/TableSpeed.csv"
    print(data)
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)

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
        #source_csv_path = "//zkh/appdata/RTDicom/Projectline_modelling_lung_cancer/Users/Luis/ListsOfPatients/Dicom2Nii_LastRound.csv"
        source_csv_path = "//zkh/appdata/RTDicom/Projectline_modelling_lung_cancer/Users/Luis/CSVs/FinalDicomTable2.csv"
        
        save_path = config['save_path']
    
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
        if "ave" in f.lower() or "mip" in f.lower() or "thorax" in f.lower():
            missingCT_bool= False
        if "gtv" in f.lower() and not "igtv" in f.lower():
            missingGTV_bool = False
        if "itv" in f.lower() or "igtv" in f.lower():
            missingITV_bool = False    
        if "BPCT" in f:
            missingBPCT_bool = False
            
    return missingCT_bool,missingITV_bool,missingGTV_bool,missingBPCT_bool

def convertPlanCT(df,id_column,patientID,save_path,filename):
    pattern = re.compile(r'(?![2]),(?![0-9])')
    PlanCT_path = df[id_column==patientID]['CT'].iloc[0]
    PlanCT_path_list = pattern.split(PlanCT_path)
    PlanCT_path_clean = [element.strip() for element in PlanCT_path_list]
    PlanCT_path_unique = list(set(PlanCT_path_clean))
    
    for singPlanCT_path in PlanCT_path_unique:
        if len(singPlanCT_path)>0:
            ct_name = singPlanCT_path.split("/")[-2].split(".nii")[0]
            #print("CT:",ct_name)
            #dicom2nifti.convert_directory(singPlanCT_path, save_px_path, compression=True, reorient=False)
            Filename=filename+ct_name
            input_filepaths = []
    
            for currSlide in os.listdir(singPlanCT_path):
                input_filepaths.append(os.path.join(singPlanCT_path,currSlide))
                sslice = pdcm.read_file(input_filepaths[-1])
                if 'TableSpeed' in sslice: 
                    speed  = sslice.TableSpeed   
                    string2File = [patientID,"Plan CT:",ct_name,"Speed",speed]
                    saveOnCSV(string2File)
                    return speed
                elif (0x0019, 0x10b0) in sslice:
                    rotation = sslice.get((0x0019, 0x10b0))
                    string2File = [patientID,"Plan CT:",ct_name,"Rotation",rotation.value]
                    saveOnCSV(string2File)
                    return rotation.value
                elif (0x0019, 0x1023) in sslice: # [Table Speed [mm/rotation]]
                    rotation = sslice.get((0x0019, 0x1023))
                    string2File = [patientID,"Plan CT:",ct_name,"[mm/rotation]",rotation.value]
                    saveOnCSV(string2File)
                    return rotation.value
                else:
                    string2File = [patientID,"Plan CT:",ct_name,"Attribute Not found",None]
                    saveOnCSV(string2File)
                    return 0
                
            #image, pixel_spacing, image_position_patient,axial_positions = convert_dicom_to_nifty(input_filepaths,str(patientID),
            #                        save_path,[],extension='.nii.gz',filename="CT_"+Filename,
            #                        pixel_spacing = None, image_position_patient=None,axial_positions=None,
            #                        np_image=None,dtype_image=np.float32,dtype_mask=np.uint8,)
            
    
    return  image, pixel_spacing, image_position_patient,axial_positions,singPlanCT_path

def convertBPCT(df,patientID,save_path,filename):
    listCTs_path = df[df['pxID'] == patientID].iloc[:,8:20].values.tolist()
    listCTs_path_split = [str(item).replace('\\\\','/') for sublist in listCTs_path for item in sublist]
    for singleCT_path in listCTs_path_split:
        if not(str(singleCT_path)=="nan"):
            listofCTs = singleCT_path.split(", ")
            for singPlanCT_path in listofCTs:
                if len(singPlanCT_path)>2:
                    ct_name = singPlanCT_path.split("/")[-2].split(".nii")[0]
                    #dicom2nifti.convert_directory(singPlanCT_path, save_px_path, compression=True, reorient=False)
                    Filename=filename+ct_name
                    input_filepaths = []
            
                    for currSlide in os.listdir(singPlanCT_path):
                        input_filepaths.append(os.path.join(singPlanCT_path,currSlide))
                        sslice = pdcm.read_file(input_filepaths[-1])
                        if 'TableSpeed' in sslice: 
                            speed  = sslice.TableSpeed   
                            string2File = [patientID,"BP CT:",ct_name,"Speed",speed]
                            saveOnCSV(string2File)
                            return speed
                        elif (0x0019, 0x10b0) in sslice: #[Feed per Rotation]
                            rotation = sslice.get((0x0019, 0x10b0))
                            string2File = [patientID,"BP CT:",ct_name,"Rotation",rotation.value]
                            saveOnCSV(string2File)
                            return rotation.value
                        elif (0x0019, 0x1023) in sslice: # [Table Speed [mm/rotation]]
                            rotation = sslice.get((0x0019, 0x1023))
                            string2File = [patientID,"BP CT:",ct_name,"[mm/rotation]",rotation.value]
                            saveOnCSV(string2File)
                            return rotation.value
                        else:
                            string2File = [patientID,"BP CT:",ct_name,"Attribute Not found",None]
                            saveOnCSV(string2File)
                            return 0
                            
            
                    #image, pixel_spacing, image_position_patient,axial_positions = convert_dicom_to_nifty(input_filepaths,str(patientID),
                    #                        save_path,[],extension='.nii.gz',filename="CT_"+Filename,
                    #                        pixel_spacing = None, image_position_patient=None,axial_positions=None,
                    #                        np_image=None,dtype_image=np.float32,dtype_mask=np.uint8,)
    
    return 0
    
def convertRT(df,patientID,save_path,target_labels,id_column,image, pixel_spacing, image_position_patient,axial_positions):
    print("RTStruct:")
    listRTs_path = df[df['pxID'] == patientID].iloc[:, 2:8].values.tolist()
    listRTs_path_split = [item for sublist in listRTs_path for item in sublist]
    listRTs_path_unique = np.unique(listRTs_path_split)
    
    pattern = re.compile(r'(?![2]),(?![0-9])')
    PlanCT_path = df[id_column==patientID]['CT'].iloc[0]
    PlanCT_path_list = pattern.split(PlanCT_path)
    PlanCT_path_clean = [element.strip() for element in PlanCT_path_list]
    PlanCT_path_unique = list(set(PlanCT_path_clean))
    
    for singleRT_path in listRTs_path_unique:
        if not(str(singleRT_path)=="nan"):
            if False:
                Filename="RTstruct"
                try:
                    image, pixel_spacing, image_position_patient,axial_positions = convert_dicom_to_nifty([singleRT_path],str(patientID),
                                            save_path,target_labels,extension='.nii.gz',filename="RT_"+Filename,
                                            pixel_spacing = pixel_spacing, image_position_patient=image_position_patient,axial_positions=axial_positions,
                                                np_image=image,dtype_image=np.float32,dtype_mask=np.uint8,)
                except Exception as e: 
                    print(e)
                    pass
                            
                
            elif (image is None and pixel_spacing is None and image_position_patient is None and axial_positions is None):
                Filename="RTstructUtils"
                for single_PlanCT_path in PlanCT_path_unique:
                    try:
                        rtstructUTILS = RTStructBuilder.create_from(dicom_series_path=single_PlanCT_path,rt_struct_path=singleRT_path)
                        all_names = rtstructUTILS.get_roi_names()
                        planCT_Nii_path = os.listdir(os.path.join(save_path,str(patientID)))
                        
                        planCT_Nii_path = [file for file in planCT_Nii_path  if 'PlanCT' in file]
                        ct_nifti = nib.load(os.path.join(save_path,str(patientID),planCT_Nii_path[0]))
                        for curr_mask in target_labels: 
                            for curr_name in all_names: 
                                if curr_mask == curr_name:
                                    mask_3d = rtstructUTILS.get_roi_mask_by_name(curr_mask)
                                    mask_nifti = nib.Nifti1Image(mask_3d, affine=ct_nifti.affine, header=ct_nifti.header)
                                    nib.save(mask_nifti, os.path.join(save_path,str(patientID),Filename+curr_mask+'.nii.gz'))
                        return 0
                    except Exception as e: 
                        print(e)
                        pass
            return 1
    return 0

def main():
    df,target_labels,save_path = openYaml()
    df['pxID'] = df['pxID'].astype(int)
    id_column = df.iloc[:, 0]

    filtered_ids = FilteredIDs()
    
    count=0
    listMissingRTs = []
    for patientID in id_column:
        if str(patientID) in filtered_ids:

            #CREATE PATH
            if not os.path.exists(save_path+str(patientID)):
                os.makedirs(save_path+str(patientID)+'/')
                print("NEW Px:",patientID,"Count",count)
        
            #CHECK IF PX has been completed before
            missPlanCTNii,missITVNii,missGTVTNii,missBPCT = LookForPlanCT_GTV_ITV_InNii(save_path+str(patientID))
            if False and not(missPlanCTNii):
                print("Already Complete Px:",patientID,"Count",count)
            else:
                print("Not complete Folder Px:",patientID,"Count",count)
                
                
                #Convert Plan CT
                #image, pixel_spacing, image_position_patient,axial_positions, singPlanCT_path = convertPlanCT(df,id_column,patientID,save_path,"PlanCT_")
                speedPlan = convertPlanCT(df,id_column,patientID,save_path,"PlanCT_")

                # RTSTruct
            
                #convertBool  = convertRT(df,patientID,save_path,target_labels, id_column,image=None, pixel_spacing=None, image_position_patient=None,axial_positions=None)
                #if convertBool == 1:
                #    listMissingRTs.append(patientID)
                #Convert BP CT
                speedBP = convertBPCT(df,patientID,save_path,"BPCT_")
            
                
                            
            count+=1 

    if False:
        with open('listMissingRTs.txt','w') as f:
            for item in listMissingRTs:
                f.write("%s\n" % item)


if __name__ == "__main__":
    main()












