#Create a csv file with the following structure pxID,CSV,RT
#gets a folder root
#loops to finds pxid folders
#insde px folder is the timepoint of the 4dctscan study
#inside pxid folders, finds CTs and RT in separate folder
#in this example each ct has a rt file in separate folders with almost the same name


import os
import re
import pydicom as pdcm
import pandas as pd
from tqdm import tqdm

def extract_numbers_before_A(text):
    # Use regex to find all occurrences of numbers before 'A'
    pattern = r'Gated (\d+\.?\d*)A'
    matches = re.findall(pattern, text)
    return matches

def GetModality(path):
    # Read the DICOM files
    file = os.listdir(path)[0]
    ds = pdcm.dcmread(os.path.join(path,file), stop_before_pixels=True)
    modality = ds.Modality
    return modality

def SaveinCSV(currPx,CT_path,RT_path):
    # Create a csv file with the following structure pxID,CSV,RT
    savecsvpath = 'C:/Users/delaOArevaLR/OneDrive - UMCG/Scans/NBIA_4d/'
    csvpath = os.path.join(savecsvpath,'NBIA4d.csv')
    if not os.path.exists(csvpath):
        df = pd.DataFrame(columns=['pxID','CT','RT'])
        df.to_csv(csvpath, index=False)
    df = pd.read_csv(csvpath)
    new_row = {'pxID': currPx, 'CT': CT_path, 'RT': RT_path}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(csvpath, index=False)
    return 1


if __name__ == '__main__':
    root = 'C:/Users/delaOArevaLR/OneDrive - UMCG/Scans/NBIA_4d/Dicom_Selected/'
    PxList = os.listdir(root)
    for currPx in tqdm(PxList):
        timepoints = os.listdir(root+currPx)
        for currtimepoint in timepoints:
            allfolders = os.listdir(root+currPx+'/'+currtimepoint)
            allfolders = sorted(allfolders)
            gate_CT,gate_RT = None,None
            for currFolder in allfolders:
                if not("BP" in currFolder):
                    modality = GetModality(os.path.join(root,currPx,currtimepoint,currFolder))
                    if modality == 'CT':
                        CT_path = os.path.join(root,currPx,currtimepoint,currFolder)
                        gate_CT = extract_numbers_before_A(currFolder)
                    if modality == 'RTSTRUCT':
                        RT_Path = os.path.join(root,currPx,currtimepoint,currFolder)
                        gate_RT = extract_numbers_before_A(currFolder)
                    if gate_CT == gate_RT and gate_CT != None:
                        SaveinCSV(currPx,CT_path,RT_Path)
                        gate_CT,gate_RT = None,None
                    

                

