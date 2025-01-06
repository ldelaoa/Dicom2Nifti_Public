import numpy as np
import pydicom
import os
import csv
import pandas as pd
import yaml

def FindCT_UID(path):
    files = os.listdir(path)
    ct_dicom_dataset = pydicom.dcmread(os.path.join(path,files[0]))
    series_instance_uid = ct_dicom_dataset[(0x0020, 0x0052)].value
    return series_instance_uid

def FindRT_UID_perContour(path,roi_name_to_find):
    files = os.listdir(path)
    rtstruct_dataset = pydicom.dcmread(path+files[0])
    if rtstruct_dataset.Modality == "RTSTRUCT":
        roi_sequence = rtstruct_dataset.StructureSetROISequence
        for roi_item in roi_sequence:
            roi_number = roi_item.ROINumber
            roi_name = roi_item.ROIName
            if roi_name == roi_name_to_find:
                # Print information for the found ROI
                #print(f"ROI Name: {roi_name}")
                #print(f"ROI NameTo find: {roi_name_to_find}")
                #print(f"ROI Number: {roi_number}")
                referenced_frame_of_reference_uid = roi_item.ReferencedFrameOfReferenceUID
                #print(f"Referenced Frame of Reference UID: {referenced_frame_of_reference_uid}")
                return referenced_frame_of_reference_uid

        else:
            return None


def FindUIDMatch(RtPaths,CTPaths,label):
    numcontours=0
    for currRTpath in RtPaths:
        for currCTpath in CTPaths:
            #for label in labels:
            ctUID = FindCT_UID(currCTpath)
            rtUID = FindRT_UID_perContour(currRTpath,label)
            if rtUID == ctUID and ctUID is not None and rtUID is not None:
                numcontours+=1                    
                print("Yes Match",label)
                break
                break
    return numcontours

def GetTheContourRTMatch(ctfolder,rtfolder,tot_labels,tumor_labels,ln_labels):
    singlematch = False
    ct_Match = []
    tot_Match, tumor_Match, ln_Match = ([],[],[])
    if len(ctfolder)==0:
        print("No CT")
    for k in range(len(ctfolder)):
        for j in range(len(rtfolder)):
            rtfiles = os.listdir(rtfolder[j])
            for i in range(len(rtfiles)):
                if not singlematch:
                    try:
                        print("check",i,j,k)
                        #rtstruct = RTStructBuilder.create_from(dicom_series_path=ctfolder[k],rt_struct_path=str(rtfolder[j]+rtfiles[i]))
                        for labeltot in tot_labels:
                            numITVs = FindUIDMatch(RTStruct_fpaths,AvgCt_fpaths,labeltot)
                            if numITVs>0:
                                tot_Match.append(str(rtfolder[j]+rtfiles[i]))
                                singlematch = True
                                break
                        for labeltum in tumor_labels:
                            numITVs = FindUIDMatch(RTStruct_fpaths,AvgCt_fpaths,labeltum)
                            if numITVs>0:
                                tumor_Match.append(str(rtfolder[j]+rtfiles[i]))
                                singlematch = True
                                break
                        for labelln in ln_labels:
                            numITVs = FindUIDMatch(RTStruct_fpaths,AvgCt_fpaths,labelln)
                            if numITVs>0:
                                ln_Match.append(str(rtfolder[j]+rtfiles[i]))

                        if len(tot_Match)+len(tumor_Match)+len(ln_Match) == 0:
                            print("No labels Matched: ")
                        else:
                            ct_Match.append(ctfolder[k])
                            if len(tot_Match) == 0: tot_Match.append(0)
                            if len(tumor_Match) == 0: tumor_Match.append(0)
                            if len(ln_Match) == 0: ln_Match.append(0)
                    except Exception as e: pass

        #mask_3d = rtstruct.get_roi_mask_by_name(label)
    return ct_Match,tot_Match,tumor_Match,ln_Match

def TargetLabelsYaml():
    with open('config_Dicom2Nii.yaml', 'r') as stream:
        config = yaml.safe_load(stream)
        
        itvtot = config['itv_tot_labels']
        itvtum = config['itv_tumor_labels']
        itvnod = config['itv_ln_labels']
        
        gtvtot = config['gtv_tot_labels']
        gtvtum = config['gtv_tumor_labels']
        gtvnod = config['gtv_ln_labels']
    
    target_labels = itvtot + itvtum+itvnod+gtvtot+gtvtum+gtvnod

    return target_labels


def main(csv_file_path,PxList,targetlabels,fieldnames): 
    with open(csv_file_path, 'w', newline='') as csvfile:
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if csvfile.tell() == 0:
            writer.writeheader()

        for Px in PxList:
            AvgCt_fpaths = []
            RTStruct_fpaths = []

            for root, dirs, files in os.walk(root_path+Px, topdown=True):
                for d in dirs:
                    if "2mm" in d or "3mm" in d or  "%" in d or "2,5mm" in d or "Ave" in d or "MIP" in d or ("CT" in d and not "RTSTRUCT" in d):
                        AvgCt_fpaths.append(root+'/'+d+'/')
                    if ('RTSTRUCT' in d or "pproved" in d) or ("PinnPlan" in d and not("RTDOSE" in d)):
                        #for f in os.listdir(root+'/'+d+'/'):
                        RTStruct_fpaths.append(root+'/'+d+'/')


            print("Px",Px,"Num CTs",len(AvgCt_fpaths),"Num RTs",len(RTStruct_fpaths))

                #ctMatch,rtMatch_tot,rtMatch_tumor,rtMatch_ln = GetTheContourRTMatch(AvgCt_fpaths,RTStruct_fpaths,gtv_tot_labels,gtv_tumor_labels,gtv_ln_labels)

                #if ctMatch ==None:
                #    print("No Match")
                #else: 
                #    print("Yes Match")
            writer.writerow({'pxID':Px,'CT':AvgCt_fpaths[0],'RT':RTStruct_fpaths[0]})

if __name__ == "__main__":
     #GET PATHS AND LABELS
    targetlabels = TargetLabelsYaml()
    root_path  = "Z:/inbox/Dicom_Data/ToFix/ToFix/"
    PxList = np.sort(os.listdir(root_path))
    csv_file_path = "Z:/DRE_Code/Dicom2Nifti_Public/DicomTable_DRE.csv"
    fieldnames = ['pxID', 'CT', 'RT']

    #LOOK for patients already been analized
    if os.path.exists(csv_file_path):
        df = pd.read_csv(csv_file_path)
        checked_list = df['pxID'].tolist()
        print(len(checked_list),"Px already checked,out of",len(PxList))
   

    main(csv_file_path,PxList,targetlabels,fieldnames)





