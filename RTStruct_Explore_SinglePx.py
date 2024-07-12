import pydicom

root = "Z:/inbox/Dicom_Data/0619086/"
#rtstruct_path = root+"RS Approved Structure Set/IM1.DCM"
rtstruct_path = root+"RS Unapproved Structure Set/1.2.752.243.1.1.20190102134746257.2300.71414.DCM"

rtstruct_dicom = pydicom.dcmread(rtstruct_path)

for i, roi_seq in enumerate(rtstruct_dicom.StructureSetROISequence):
    if 'itv' in roi_seq.ROIName.lower() or 'gtv' in roi_seq.ROIName.lower():
        print("Names: ",roi_seq.ROIName)