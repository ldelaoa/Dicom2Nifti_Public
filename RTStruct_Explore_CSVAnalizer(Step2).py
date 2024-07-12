import os 
import csv
import pandas as pd
import numpy as np
from tqdm import tqdm

def Labels():
    # ITV Labels
    itv_tot_labels = ["ITV", "IGTV", "IgTV", "ITV1", "ITV2", "ITV3", "ITV totaal def", "2ITV", "ITV_TOT", "ITV_6000", "ITV_5100", "ITV_Totaal", "ITV_LBK", "ITV_LOK", "IGTV_6000"]
    itv_tumor_labels = ["ITVtumor", "ITV_tumor", "ITVtumor def", "2ITV_tumor", "ITV-P", "ITVtumorA1", "ITV_tumor_LBK", "ITVtu", "IGTVp"]
    itv_ln_labels = ["ITVklieren", "ITV_klier", "ITV_Klier", "ITVklieren def", "2ITV_klier", "ITV_n", "ITV_klier_LBK", "IGTVnode"]

    # GTV Labels
    gtv_tot_labels = ["GTV", "GTV1", "GTV2", "GTV3", "GTV totaal def", "2GTV", "GTV_TOT", "GTV_6000", "GTV_5100", "GTV_Totaal", "GTV_LBK", "GTV_LOK", "GTV_5000", "GTV_preop", "GTV_totaal", "GTV_voor OK", "GTVtotaal", "GTVnew", "GTV(op exp)", "GTVop", "GTV_voor OK", "GTV oorspr"]
    gtv_tumor_labels = ["GTVtumor", "GTV_tumor", "GTVtumor def", "2GTV_tumor", "GTV-P", "GTVtumorA1", "GTV_tumor_LBK", "GTV tumor", "GTVp", "GTVtu", "GTVtumor_exp", "GTVtumor_exp_50->0", "GTVtumor_insp", "GTVpatelectasebewaren(1)", "GTVt"]
    gtv_ln_labels = ["GTVklieren", "GTV_klier", "GTV_Klier", "GTVklieren def", "2GTV_klier", "GTV_n", "GTV_klier_LBK", "GTVn", "GTVnode_exp", "GTVnodes_exp", "GTVnodes_exp_50->0", "GTVnodes_insp", "GTVklieren"]
    
    return itv_tot_labels,itv_tumor_labels,itv_ln_labels,gtv_tot_labels,gtv_tumor_labels,gtv_ln_labels

def readFirstColumn(csvFile):
    with open(csvFile,mode='r') as file: 
        csv_reader = csv.reader(file)
        first_col  = [row[0]for row in csv_reader]
    unique  = np.unique(first_col)
    return unique

def FixFormat(currString):
    currString = currString.replace("]","")
    currString = currString.replace("[","")
    currString = currString.replace("'","")
    currString = currString.replace(" ","")
    return currString


def main(csv2save,csv_file_path):
    uniqueIds = readFirstColumn(csv_file_path)
    print(len(uniqueIds))
    df  = pd.read_csv(csv_file_path,index_col=False, names= ["PxIds","Year","Data"])
    itv_tot_labels,itv_tumor_labels,itv_ln_labels,gtv_tot_labels,gtv_tumor_labels,gtv_ln_labels = Labels()
    pxLabels = []

    for currPx in tqdm(uniqueIds):
        currITV_tot,currITV_p,currITV_n,currGTV_tot,currGTV_p,currGTV_n = None,None,None,None,None,None
        filtered_df = df[df["PxIds"]==currPx]
        for listLabels in filtered_df["Data"]:
            if not(isinstance(listLabels,float)):
                for currLabel in listLabels.split(','):
                    currLabel = FixFormat(currLabel)

                    if currLabel in itv_tot_labels: currITV_tot = currLabel
                    if currLabel in itv_tumor_labels: currITV_p = currLabel
                    if currLabel in itv_ln_labels: currITV_n = currLabel

                    if currLabel in gtv_tot_labels: currGTV_tot = currLabel
                    if currLabel in gtv_tumor_labels: currGTV_p = currLabel
                    if currLabel in gtv_ln_labels: currGTV_n = currLabel
        pxLabels.append([currPx,currITV_tot,currITV_p,currITV_n,currGTV_tot,currGTV_p,currGTV_n])
    
    df_RTStruct = pd.DataFrame(pxLabels,columns = ["umcg","ITV_tot","ITV_p","ITV_n","GTV_tot","GTV_p","GTV_n"])
    df_RTStruct.to_csv(csv2save,index=False)


if __name__ == '__main__':
    csv2save = "Z:/IO_TempFiles/BlobsRes/CSV/rtstruct_Dicom_AllPX_Clean(Step2).csv"
    csv_file_path = "Z:/IO_TempFiles/BlobsRes/CSV/rtstruct_Dicom_AllPX.csv"
    main(csv2save,csv_file_path)
