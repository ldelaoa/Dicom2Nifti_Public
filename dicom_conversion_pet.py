import os
from os.path import join
import warnings
import logging
import glob

import click
import SimpleITK as sitk
import yaml
import os
from functions import (convert_dicom_to_nifty,
                                       MissingWeightException)

os.chdir('//zkh/appdata/RTDicom/HANARTHproject/scrips_converting/')
with open('settings.yalm') as file:
    settings = yaml.full_load(file)

path_dicom = settings['path']['dicom']
path_nii = settings['path']['nii']
path_bb = settings['path']['bb_file']
label_rtstruct = settings['voi']

@click.command()
@click.argument('input_filepath',
                type=click.Path(exists=True),
                default=path_dicom)
@click.argument('output_filepath', type=click.Path(), default=path_nii)
@click.argument('bb_filepath', type=click.Path(), default=path_bb)
@click.option('--extension', type=click.STRING, default='.nii.gz')
@click.option('--subfolders', is_flag=True)

def main(input_filepath, output_filepath, bb_filepath, extension, subfolders):

    logger = logging.getLogger(__name__)
    logger.info('Converting Dicom to Nifty')

    sitk_writer = sitk.ImageFileWriter()
    sitk_writer.SetImageIO('NiftiImageIO')
    
    patients=glob.glob(input_filepath+'/*')
    
    already_transformed = [i.split('\\')[-1].split('_')[0] for i in glob.glob(path_nii+'/*_pt.nii.gz')]

    print(already_transformed)

    patients = [str(j.split("\\")[-1]) for j in patients if str(j.split("\\")[-1]) not in list(set(already_transformed))]
    print(patients)

    for dirname in patients:

        files_list_pt = glob.glob(input_filepath+'/'+dirname+'/PET/*.dcm')

        patientID = dirname.split("\\")
        
        patientID = str(patientID[-1])
        
        print(patientID)
        
        if bool(files_list_pt):

            patient_name = patientID 
            
            if subfolders:
                path_output_folder = join(output_filepath, patient_name)
            else:
                path_output_folder = output_filepath
                
            if not os.path.exists(path_output_folder):
                os.mkdir(path_output_folder)

                logger.info('Creating folder {}'.format(output_filepath))

            logger.info('Converting the PT for patient {}'.format(patient_name))
            try:
                (np_pt, px_spacing_pt,
                 im_pos_patient_pt) = convert_dicom_to_nifty(
                     files_list_pt,
                     patient_name,
                     path_output_folder,
                     modality='PT',
                     sitk_writer=sitk_writer,
                     rtstruct_file=None,
                     extension=extension)
            except MissingWeightException:
                    warnings.warn(
                        "Cannot find the weight of the patient, hence it "
                        "is approximated to be 75.0 kg")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logging.captureWarnings(True)

    main()
