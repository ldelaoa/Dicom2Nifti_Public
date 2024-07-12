"""
A script that looks through a path and creates an overview of all the patients and the scans that were performed on them.
By: Jacob Menzigna
Version 2.1
"""

# standard imports
import os
from os.path import join
import logging
import re

# external imports
from natsort import natsorted
import pandas as pd
import pydicom as pdcm


# Add logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


class ScanCrawler:
    """
    TODO: add docstring
    """

    def __init__(self, base_path, output) -> None:
        self.base_path = base_path
        self.output = output

    def csv_writer(self, line, mode='a'):
        """Writes a line to a csv file.

        Args:
            line (str): a string that needs to be written to the csv file
            mode (str, optional): the mode in which the file is opened.
            Defaults to 'a'.
        """

        with open(self.output, mode) as csv_file:
            csv_file.write(line+'\n')

    def get_patient_list(self):
        """Creates a list of patient IDs from the folder names in the base path.

        Raises:
            ValueError: If the folder names do not match the patient ID format.

        Returns:
            list: a list of patient IDs
        """

        folders = os.listdir(self.base_path)
        if re.match(r'\d{7}', folders[0]):
            patient_list = natsorted(folders)

            return patient_list

        else:
            raise ValueError('''The folder names do not match the patient ID format.
                             Please make sure you're looking in a directory with patient folders.''')

    def get_scans_info(self, patient):
        """collects the following information from a patient folder and writes
        them to a csv file:
        - patient ID
        - scan folder name
        - study date
        - study description
        - modality

        Args:
            patient (str): the patient ID of the patient whose scans you wants
            to collect info on
        """

        logger.info('Collecting scan info for patient %s', patient)

        scan_dirs = []
        no_scan_dirs = []

        for root, _, files in os.walk(join(self.base_path, patient)):

            if files and files[0].endswith('.DCM'):

                scan_dirs.append(root)

                try:
                    slices = files
                    dcm = pdcm.dcmread(join(root, slices[0]))

                    folder_name = root.split('\\')[-1]

                    study_date = dcm.StudyDate
                    study_date = study_date[0:4] + '-' + study_date[4:6] \
                        + '-' + study_date[6:8]

                    study_description = dcm.StudyDescription
                    series_description = dcm.SeriesDescription
                    modality = dcm.Modality

                    csv_line = f'"{patient}","{modality}","{study_date}","{series_description}","{study_description}","{folder_name}"'

                    self.csv_writer(csv_line, mode='a')

                except Exception as exc:
                    logger.error('Error in %s: %s', root, exc)
                    continue

            else:
                no_scan_dirs.append(root.split('\\')[-1])


def create_excel(csv_doc, output_path):
    """Writes all the retrived patient study info to an excel file.

    Args:
        csv_doc (str): path to the csv file
        output_path (str): (location) name of the excel file
    """
    df = pd.read_csv(csv_doc)
    df.set_index('patient_id', inplace=True)
    df.to_excel(output_path, index=True)


if __name__ == '__main__':
    pass
