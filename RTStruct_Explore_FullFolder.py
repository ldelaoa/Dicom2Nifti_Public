import pydicom
import os
import csv

def getLabels(rtstruct_path,px):
    rtstruct_dicom = pydicom.dcmread(rtstruct_path)
    names_struct = []
    for i, roi_seq in enumerate(rtstruct_dicom.StructureSetROISequence):
        if 'lung' not in roi_seq.ROIName.lower() and ('itv' in roi_seq.ROIName.lower() or 'gtv' in roi_seq.ROIName.lower()):
            names_struct.append(roi_seq.ROIName)
    date = rtstruct_dicom.StudyDate
    return [px,date[:4],names_struct]

def main(root,csv_file_path):
    csv_list = []
    pxList = os.listdir(root)
    for currPx in pxList:
        for subroot,dirs,files in os.walk(os.path.join(root,currPx)):
            for d in dirs:
                if "rtstruct" in d or "pproved" in d:
                    rtstructFile_list = os.listdir(os.path.join(subroot,d))
                    for currRTfile in rtstructFile_list:
                        csv_list.append(getLabels(os.path.join(subroot,d,currRTfile),currPx))
        
    with open (csv_file_path,'w',newline='') as file:
        writer = csv.writer(file)
        for i in range(len(csv_list)):
            writer.writerow(csv_list[i])

if __name__ == '__main__':
    root = "Z:/inbox/Dicom_Data/"
    csv_file_path = "Z:/IO_TempFiles/BlobsRes/CSV/rtstruct_prueba.csv"
    main(root,csv_file_path)
