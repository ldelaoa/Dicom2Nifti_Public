#Create a csv file with the following structure pxID,CSV,RT
#gets a folder root
#loops to finds pxid folders
#insde px folder is the timepoint of the 4dctscan study
#inside pxid folders, finds CTs and RT in separate folder
#in this example each ct has a rt file in separate folders with almost the same name

#v2 - link between CT and RT is added

import os
import re
import shutil
import pydicom as pdcm
import pandas as pd
from tqdm import tqdm

def sanitize_pathFun(path):
    invalid_chars = r'[<>:]'
    sanitized_path = re.sub(invalid_chars, '_', path)
    return sanitized_path

def CreateFolderStructure(root,currPx):
    temp_SeriesName = []
    temp_slides = {} 
    pathWithStructure = "C:/Users/delaOArevaLR/OneDrive - UMCG/Scans/REACT/Selected_REACT_Dicom/REACT_Dicom_Selected/REACT_Dicom_Selected_Structured/"
    if not(os.path.exists(os.path.join(pathWithStructure,currPx))):
        os.mkdir(os.path.join(pathWithStructure,currPx))
    for root,dir,files in os.walk(os.path.join(root,currPx)):
        for f in files: 
            modality,temp_uid,SeriesName = GetModalityandUIDandSeries(os.path.join(root,f))
            SeriesName = sanitize_pathFun(SeriesName)
            if SeriesName in temp_SeriesName:
                value = temp_slides[SeriesName]
                temp_slides[SeriesName] = value+1
                source =os.path.join(root,f)
                destination = os.path.join(pathWithStructure,currPx,SeriesName)
                shutil.move(source, destination)
            else:
                temp_SeriesName.append(SeriesName)
                folder_name  = os.path.join(pathWithStructure,currPx,SeriesName)
                if not(os.path.exists(folder_name)):
                    os.mkdir(folder_name)
                temp_slides[SeriesName] = 1
                source =os.path.join(root,f)
                destination = os.path.join(pathWithStructure,currPx,SeriesName)
                shutil.move(source, destination)
    
    for key, value in temp_slides.items():
        print(currPx)
        print(f"Folder: {key} Slides: {value}")
                    
    return 0

def extract_numbers_before_A(text):
    # Use regex to find all occurrences of numbers before 'A'
    pattern = r'Gated (\d+\.?\d*)A'
    matches = re.findall(pattern, text)
    return matches

def GetModalityandUIDandSeries(path):
    # Read the DICOM files
    ds = pdcm.dcmread(path, stop_before_pixels=True)
    modality = ds.Modality
    temp_uid = None
    description = ds.SeriesDescription
    if modality == 'CT':
        temp_uid = ds.SeriesInstanceUID
    if modality == 'RTSTRUCT':
        temp_uid = ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].SeriesInstanceUID
    return modality,temp_uid,description

def SaveinCSV(currPx,CT_path,RT_path):
    # Create a csv file with the following structure pxID,CSV,RT
    savecsvpath = 'C:/Users/delaOArevaLR/OneDrive - UMCG/Scans/NBIA_4d/'
    csvpath = os.path.join(savecsvpath,'REACT_DicomSelectedPaths.csv')
    if not os.path.exists(csvpath):
        df = pd.DataFrame(columns=['pxID','CT','RT'])
        df.to_csv(csvpath, index=False)
    df = pd.read_csv(csvpath)
    new_row = {'pxID': currPx, 'CT': CT_path, 'RT': RT_path}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(csvpath, index=False)
    return 1


if __name__ == '__main__':
    #root = 'C:/Users/delaOArevaLR/OneDrive - UMCG/Scans/NBIA_4d/Dicom_Selected/'
    root = "C:/Users/delaOArevaLR/OneDrive - UMCG/Scans/REACT/Selected_REACT_Dicom/REACT_Dicom_Selected/REACT_Dicom_Selected_Structured/"
    PxList = os.listdir(root)
    createStructureBool = False
    if createStructureBool:
        for currPx in tqdm(PxList):
            CreateFolderStructure(root,currPx)
    for currPx in tqdm(PxList):
        timepoints = os.listdir(root+currPx)
        for currtimepoint in timepoints:
            allfolders = os.listdir(root+currPx+'/'+currtimepoint)
            allfolders = sorted(allfolders)
            rt_uid,ct_uid = [],[]
            rt_list ,ct_list = [],[]
            for currFolder in allfolders:
                if os.path.isdir(os.path.join(root,currPx,currtimepoint,currFolder)):
                    files = os.listdir(os.path.join(root,currPx,currtimepoint,currFolder))
                for file in files: 
                    modality,temp_uid,_ = GetModalityandUIDandSeries(os.path.join(root,currPx,currtimepoint,currFolder,file))
                    if modality == 'CT':
                        ct_list.append(os.path.join(root,currPx,currtimepoint,currFolder))
                        ct_uid.append(temp_uid)
                        break
                    if modality == 'RTSTRUCT':
                        rt_list.append(os.path.join(root,currPx,currtimepoint,currFolder,file))
                        rt_uid.append(temp_uid)
            count=0
            for i in range(len(ct_list)):
                for j in range(len(rt_list)):
                    if ct_uid[i] == rt_uid[j]:
                        count+=1
                        SaveinCSV(currPx,ct_list[i],rt_list[j])
                        #print('match path!:',count,":",currPx,ct_list[i],rt_list[j])