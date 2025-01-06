import pydicom
import os
import csv
from tqdm import tqdm
#from multiprocessing import Pool
import logging

def getLabels(rtstruct_path,px):
    #rtstruct_path,px = args
    try:
        rtstruct_dicom = pydicom.dcmread(rtstruct_path,stop_before_pixels=True)
        if rtstruct_dicom.Modality =="RTSTRUCT" and hasattr(rtstruct_dicom, 'StructureSetROISequence'):
            names_struct = []
            for i, roi_seq in enumerate(rtstruct_dicom.StructureSetROISequence):
                if 'lung' not in roi_seq.ROIName.lower() and ('itv' in roi_seq.ROIName.lower() or 'gtv' in roi_seq.ROIName.lower()):
                    if "ContourSequence" in rtstruct_dicom.ROIContourSequence[i]:
                        contour = [s.ContourData for s in rtstruct_dicom.ROIContourSequence[i].ContourSequence]
                        if len(contour)>1:
                            names_struct.append(roi_seq.ROIName)
            date = rtstruct_dicom.StudyDate
            return [px,date[:4],names_struct]
        return [px,None,None]
    except Exception as e:
        print(px,e)
        return [px,None,None]
    
def main(root,csv_file_path,logger):
    #p = Pool()  # number of processes = number of CPUs
    #tasks = []
    results = []
    pxList = os.listdir(root)
    for currPx in tqdm(pxList):
        logger.info("Px "+str(currPx))
        for subroot,dirs,files in os.walk(os.path.join(root,currPx)):
            for d in dirs:
                if "RTSTRUCT" in d or "pproved" in d or 'PinnPlan' in d:
                    rtstructFile_list = os.listdir(os.path.join(subroot,d))
                    for currRTfile in rtstructFile_list:
                        [Px,StudyDate,Names_struct] = getLabels(os.path.join(subroot,d,currRTfile),currPx)
                        if Names_struct is not None:
                            results.append([Px,StudyDate,Names_struct])
                        #tasks.append(()
    #results = p.map(getLabels, tasks)
    with open (csv_file_path,'w',newline='') as file:
        writer = csv.writer(file)
        for result in results:
            writer.writerow(result)
            
if __name__ == '__main__':
    #root = "//zkh/appdata/RTDicom/Projectline_modelling_lung_cancer/DICOM_data/DATA_VOLLEDIG_unstructured/"
    #csv_file_path = "//zkh/appdata/RTDicom/Projectline_modelling_lung_cancer/Users/Luis/CSVs/rtstruct_Dicom_AllPX.csv"
    root = "Z:/inbox/Dicom_Data/ToFix/ToFix"
    csv_file_path = "Z:/inbox/Dicom_Data/ToFix/rtstruct_Dicom_AllPX_indre.csv"
    logging.basicConfig(level=logging.INFO,format='%(message)s',filename = 'Logs/RTStruct_Explore_FullFolder_Step1.log',filemode='a')
    logger = logging.getLogger('my_logger')
    logger.info("----------------new run------------------")
    main(root,csv_file_path,logger)
