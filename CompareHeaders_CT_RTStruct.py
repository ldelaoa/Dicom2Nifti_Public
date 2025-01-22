#This program is intended to fix the header of a CT and a RT struct
#in order to be open in RayStation
#This program can be manually solved in Mirada by uploading it and then re saving it. 
#but this would find the differences between those two CTs and fix the incorrect one

import pydicom
import os
import numpy as np
import pydicom as pd
from pydicom.uid import generate_uid
from pydicom.dataset import Dataset, FileDataset
from pydicom.dataelem import DataElement
from pydicom.sequence import Sequence
from tqdm import tqdm

def compare_dicom_headers(file1, file2):
    # Read the DICOM files
    ds1 = pydicom.dcmread(file1,stop_before_pixels=True)
    ds2 = pydicom.dcmread(file2,stop_before_pixels=True)

    # Compare the headers and store differences
    differences = {}
    count=0
    for elem in ds1:
        count+=1
        tag=elem.tag
        if tag not in ds2:
            differences[tag] = (ds1.get(tag), "No existing info")
        elif ds1[tag] != ds2[tag]:
            differences[tag] = (ds1.get(tag), ds2.get(tag))
    for elem in ds2:
        count+=1
        tag=elem.tag
        if tag not in ds1:
            differences[tag] = ("No existing info" , ds2.get(tag))
    
    for curr in differences:
        print(curr,differences[curr])
    return 0

def deleteTag (file1,tag_info="(0008,2112)"):
     ds1 = pydicom.dcmread(file1,stop_before_pixels=True)
     for elem in ds1:
        tag=elem.tag
        if tag == (0x0008, 0x2112):
          print("Deleting it",tag_info)
          del ds1[(0x0008, 0x2112)]
          ds1.save_as(file1)

def GetSequenceInfo(dcm):
    listOfSequenceUID = []
    for elem in dcm.SourceImageSequence:
        uid =elem.ReferencedSOPInstanceUID
        listOfSequenceUID.append(uid)
    print("SOPClassUID",elem.ReferencedSOPClassUID,listOfSequenceUID[0])
    return 

def CreateSequenceInfo(dcm,prefix,SOPClassUID):
    # Create the Source Image Sequence
    source_image_sequence = Sequence()
    
    for i in range(149):
        item = Dataset()
        item.ReferencedSOPClassUID = SOPClassUID
        item.ReferencedSOPInstanceUID = generate_uid(prefix)
        source_image_sequence.append(item)
    
    seq_element = DataElement((0x0008, 0x2112), 'SQ', source_image_sequence)

    dcm[seq_element.tag] = seq_element
    dcm.SeriesDescription = "1.000000-P4P101S300I00003 Gated 0.0A-78180_EditedCT_v1"

    return dcm

def ReadAndGetInfo(file1):
    ds1 = pydicom.dcmread(file1,stop_before_pixels=True)
    si_uid = ds1.StudyInstanceUID
    si_parts = si_uid.split('.')[:-1]
    si_prefix = '.'.join(si_parts)+ '.'
    SOPClassUID = ds1.SOPClassUID
    return ds1,si_prefix,SOPClassUID
    
def RT_ContourImageSequenceAttribute(dcm_path1):
    dcm1 = pydicom.dcmread(dcm_path1, stop_before_pixels=True)
    list_ReferencedROINumber = []
    list_ReferencedSOPClassUID = []
    list_ReferencedSOPInstanceUID = []

    # Get the ROIContourSequence
    for seq1 in dcm1.ROIContourSequence:
        list_ReferencedROINumber.append(seq1.ReferencedROINumber)
        for seq2 in seq1.ContourSequence:
            for seq3 in seq2.ContourImageSequence:
                list_ReferencedSOPClassUID.append(seq3.ReferencedSOPClassUID)
                list_ReferencedSOPInstanceUID.append(seq3.ReferencedSOPInstanceUID)
    
    return list_ReferencedROINumber, list_ReferencedSOPClassUID, list_ReferencedSOPInstanceUID

def StructureSetROISequenceAttribute(dcm_path1):
    dcm1 = pydicom.dcmread(dcm_path1, stop_before_pixels=True)
    listROINumber = []
    listReferencedFrameOfReferenceUID = []
    listROIName = []
    for seq1 in dcm1.StructureSetROISequence:
        listROINumber.append(seq1.ROINumber)
        listReferencedFrameOfReferenceUID.append(seq1.ReferencedFrameOfReferenceUID)
        listROIName.append(seq1.ROIName)
    return listROINumber, listReferencedFrameOfReferenceUID, listROIName

def main_ct_edit(ct_slide_raw_list,ct_oldpath,ct_newpath):
    for currSlide in tqdm(ct_slide_raw_list):
        currSlide_Fullpath = os.path.join(ct_oldpath,currSlide)
        newSlide_Fullpath = os.path.join(ct_newpath,currSlide)
    #deleteTag (ct_slide_raw,tag_info="(0008,2112)")
    ds1,si_prefix,SOPClassUID = ReadAndGetInfo(currSlide_Fullpath)
    dcm = CreateSequenceInfo(ds1,si_prefix,SOPClassUID)
    dcm.save_as(newSlide_Fullpath)
    return 0

def main_ct(root,ct_slide_fixed,rtstruct_fixed,ct_slide_raw,rtstruct_raw):

    ct_differences = compare_dicom_headers(ct_slide_fixed,ct_slide_raw)
    print("Differences in CT slides headers:")
    for key, value in ct_differences.items():
        print(f"{key}: {value[0]} and {value[1]}")

def main_rt_detailedcheck(rt_working,rt_broken):
    list_ReferencedROINumber1, list_ReferencedSOPClassUID1, list_ReferencedSOPInstanceUID1 = RT_ContourImageSequenceAttribute(rt_working)
    list_ReferencedROINumber2, list_ReferencedSOPClassUID2, list_ReferencedSOPInstanceUID2 = RT_ContourImageSequenceAttribute(rt_broken)

    listROINumber1, listReferencedFrameOfReferenceUID1, listROIName1 = StructureSetROISequenceAttribute(rt_working)
    listROINumber2, listReferencedFrameOfReferenceUID2, listROIName2 = StructureSetROISequenceAttribute(rt_broken)

    print("Differences in RT Struct headers:")
    print(len(listROINumber1),len(listROINumber2))    
    print(len(listReferencedFrameOfReferenceUID1),len(listReferencedFrameOfReferenceUID2))
    print(len(listROIName1),len(listROIName2))
    
    for j in range(len(listROINumber1)):
        for i in range(len(list_ReferencedROINumber1)):
            if list_ReferencedROINumber1[i] == listROINumber1[j]:
                print(listROINumber1[j],listROIName1[j],listReferencedFrameOfReferenceUID1[j])
                print(list_ReferencedROINumber1[i],"-",list_ReferencedSOPClassUID1[i],"-",list_ReferencedSOPInstanceUID1[i])
                print("")
    print("----------------------------------------------------")    
    for j in range(len(listROINumber2)):
        for i in range(len(list_ReferencedROINumber2)):
            if list_ReferencedROINumber2[i] == listROINumber2[j]:
                print(listROINumber2[j],listROIName2[j],listReferencedFrameOfReferenceUID2[j])
                print(list_ReferencedROINumber2[i],"-",list_ReferencedSOPClassUID2[i],"-",list_ReferencedSOPInstanceUID2[i])
                print("")

    return

def ChangeSeriesInstance(dcm_path):
    dcm = pydicom.dcmread(dcm_path, stop_before_pixels=True)
    
    print("Series",dcm.SeriesInstanceUID,"to",dcm.SOPInstanceUID)
    new_series_instance = "1.3.6.1.4.1.14519.5.2.1.6834.5010.758699498834696705727292429103"
    dcm.SeriesInstanceUID = new_series_instance
    dcm.SeriesDescription = "RT_Edited_"+dcm.SeriesDescription
    dcm.save_as(dcm_path)
    print("Series",dcm.SeriesInstanceUID)
    return

if __name__ == "__main__":
    
    root = "C:/Users/delaOArevaLR/OneDrive - UMCG/Scans/NBIA_4d/Dicom_Selected/101_HM10395/10-21-1997-NA-p4-86157/"
    rt_working = root+"BP0%/101_HM10395/iug/rtstruct_ok/IM1.DCM"
    rt_broken =  root+"1.000000-P4P101S300I00003 Gated 0.0A-843.1/1-1 - Edited.dcm"

    #ChangeSeriesInstance(rt_broken)
    #compare_dicom_headers(rt_working,rt_broken)
    main_rt_detailedcheck(rt_working,rt_broken)
