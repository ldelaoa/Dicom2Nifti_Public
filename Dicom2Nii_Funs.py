from os.path import join
from datetime import time, datetime
import os
import glob
import numpy as np
from skimage.draw import polygon
import SimpleITK as sitk
import sys
import pandas as pd
import warnings
from os.path import join
from datetime import time, datetime
import pydicom as pdcm
import re
from pydicom.tag import Tag

def sanitize_filename(filename):
    """
    Replaces invalid characters in a filename with valid equivalents or removes them.
    
    Args:
    - filename (str): Original filename
    
    Returns:
    - str: Sanitized filename
    """
    invalid_chars = {
        '>': '_to_',  # Replace '>' with '_to_'
        '<': '_from_',  # Example for '<' if needed
    }
    pattern = re.compile('|'.join(re.escape(char) for char in invalid_chars.keys()))
    sanitized = pattern.sub(lambda match: invalid_chars[match.group()], filename)
    return sanitized

def convert_dicom_to_nifty(input_filepaths,patientID,
                           output_folder,
                           labels_rtstruct,extension,filename,
                           pixel_spacing = None, image_position_patient=None,axial_positions=None,
                           np_image=None,dtype_image=np.float32,dtype_mask=np.uint8,):
    """Function to convert the dicom files contained in input_filepaths to one
       NIFTI image.

    Args:
        input_filepaths (list): list of the dicom paths
        output_folder (str): path to the output folder where to store the
                             NIFTI file.
        modality (str, optional): The modality of the DICOM, it is used to
                                  obtain the correct physical values
                                  (Hounsfield unit for the CT and SUV for the
                                  PT). Defaults to 'CT'.
        sitk_writer (sitk.WriteImage(), optional): The SimpleITK object used
                                                   to write an array to the
                                                   NIFTI format. Defaults to
                                                   None.
        rtstruct_file (list, optional): Path to the RTSTRUCT file associated
                                       with the current image. Defaults to
                                       None.
        labels_rtstruct (list, optional): List of label to extract from the
                                          RTSTRUCT. Defaults to ['GTVt'].
        patient_weight_from_ct (float, optional): If the patient's weight is
                                                  missing from the PT DICOM
                                                  it can be provided through
                                                  this argument. Defaults to
                                                  None.
        extension (str, optional): The extension in which to save the NIFTI.
                                   Defaults to '.nii'.
        dtype_image (numpy.dtype, optional): The dtype in which to save the
                                             image. Defaults to np.float32.
        dtype_mask (numpy.dtype, optional): The dtype in which to save the
                                            segmentation. Defaults to np.uint8.

    Raises:
        MissingWeightException: Error to alert when the weight is missing from
                                the PT, to compute the SUV.
        RuntimeError: Error to alert when one or more slices are missing
        ValueError: Raised when a modality or a unit (for the PT) is not
                    handled.

    Returns:
        numpy.array: The numpy image, used to compute the bounding boxes
    """

    slices = [pdcm.dcmread(dcm) for dcm in input_filepaths]
    
    modality = slices[0].Modality
    
    if modality != 'RTSTRUCT':
        slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
        if modality == 'PT':
            if float(slices[0][Tag(0x00101030)].value) is None:
                if hasattr(slices[0], 'PatientWeight'):
                    patient_weight = float(slices[0].PatientsWeight)
                #elif patient_weight_from_ct is not None:
                #    patient_weight = patient_weight_from_ct
                else:
                    raise MissingWeightException(
                        'Cannot compute SUV the weight is missing')
            else:
                patient_weight = float(slices[0][Tag(0x00101030)].value)

        # Check if all the slices come from the same serie
        same_serie_uid = True
        serie_uid = slices[0].SeriesInstanceUID
        for s in slices:
            same_serie_uid *= serie_uid == s.SeriesInstanceUID

        if not same_serie_uid:
            print("RuntimeError('A slice comes from another serie")
            return 0, 0, None,None
            

        axial_positions = np.asarray([k.ImagePositionPatient[2] for k in slices])
        # Compute redundant slice positions
        ind2rm = [
            ind for ind in range(len(axial_positions))
            if axial_positions[ind] == axial_positions[ind - 1]
        ]
        # Check if there is redundancy in slice positions and remove them
        if len(ind2rm) > 0:
            slices = [k for i, k in enumerate(slices) if i not in ind2rm]
            axial_positions = np.asarray(
                [k.ImagePositionPatient[2] for k in slices])

        slice_spacing = (slices[1].ImagePositionPatient[2] -
                         slices[0].ImagePositionPatient[2])

        pixel_spacing = np.asarray([
            slices[0].PixelSpacing[0],
            slices[0].PixelSpacing[1],
            slice_spacing,
        ])

        if modality == 'CT':
            np_image = get_physical_values_ct(slices, dtype=dtype_image)
        elif modality == 'PT':
            np_image = get_physical_values_pt_new(slices,
                                              patient_weight,
                                              dtype=dtype_image)
        else:
            raise ValueError('The modality {} is not supported'.format(modality))

        position_final_slice = (
            len(slices) - 1) * slice_spacing + slices[0].ImagePositionPatient[2]
        # Test whether some slices are missing
        if not is_approx_equal(position_final_slice,
                               float(slices[-1].ImagePositionPatient[2])):
            if (position_final_slice - axial_positions[-1]) / slice_spacing < 1.5:
                # If only one slice is missing
                diff = np.asarray([
                    not is_approx_equal(
                        float(axial_positions[ind]) -
                        float(axial_positions[ind - 1]) - slice_spacing, 0)
                    for ind in range(1, len(axial_positions))
                ])
                ind2interp = int(np.where(diff)[0])
                new_slice = (np_image[:, :, ind2interp] +
                             np_image[:, :, ind2interp + 1]) * 0.5
                new_slice = new_slice[..., np.newaxis]
                np_image = np.concatenate(
                    (np_image[..., :ind2interp], new_slice, np_image[...,
                                                                     ind2interp:]),
                    axis=2)
                warnings.warn(
                    "One slice is missing, we replaced it by linear interpolation")
            else:
                # if more than one slice are missing
                raise RuntimeError('Multiple slices are missing')

        image_position_patient = [float(k) for k in slices[0].ImagePositionPatient]

        try:
            sitk_image = get_sitk_volume_from_np(np_image, pixel_spacing,
                                             image_position_patient)
        except:
            print("Axes don't match PET?")
            return 0,0,None,None
        if True:
            #correct_patient_name(str(slices[0].PatientName))
            output_filepath = join(
                    output_folder,
                    patientID , filename + '_' +
                    modality.lower() + extension)
            sitk_writer = sitk.ImageFileWriter()
            sitk_writer.SetImageIO('NiftiImageIO')
            sitk_writer.SetFileName(output_filepath)
            sitk_writer.Execute(sitk_image)
            #print("CT/PET conversion finished ok")
    if modality == 'RTSTRUCT':
        rtstruct_file = input_filepaths
        for rt_file in rtstruct_file:
            masks = get_masks(rt_file,
                            labels=labels_rtstruct,
                            image_position_patient=image_position_patient,
                            axial_positions=axial_positions,
                            pixel_spacing=pixel_spacing,
                            shape=np_image.shape,
                            dtype=dtype_image)
            if len(masks)==0:
                print("No Masks",rtstruct_file)
                exit()
                return None, None, None,None
            for label, np_mask in masks: #label.lower()
                output_filepath = join(output_folder,patientID,modality.lower() + extension)

                #output_filepath = join(output_folder,filename+'_'+modality.lower() + extension)
                sitk_writer = sitk.ImageFileWriter()
                sitk_writer.SetImageIO('NiftiImageIO')                
                output_filepath_mask = output_filepath.split('.')[0] + '_' + label + extension
                output_filepath_mask = sanitize_filename(output_filepath.split('.')[0] + '_' + label + extension)

                #print(output_filepath_mask)

                sitk_mask = get_sitk_volume_from_np(np_mask, pixel_spacing,
                                                    image_position_patient)
                
                sitk_writer.SetFileName(output_filepath_mask)
                sitk_writer.Execute(sitk_mask)

    #return np.transpose(np_image,(1, 0, 2)), pixel_spacing, image_position_patient
    return np.transpose(np_image,(1, 0, 2)), pixel_spacing, image_position_patient,axial_positions


def get_sitk_volume_from_np(np_image, pixel_spacing, image_position_patient):
    trans = (2, 0, 1)
    sitk_image = sitk.GetImageFromArray(np.transpose(np_image, trans))
    sitk_image.SetSpacing(pixel_spacing)
    sitk_image.SetOrigin(image_position_patient)
    return sitk_image


def is_approx_equal(x, y, tolerance=0.05):
    return abs(x - y) <= tolerance


class MissingWeightException(RuntimeError):
    pass


def correct_patient_name(patient_name):
    output = patient_name.replace("HN-CHUS-", "CHUS")
    output = output.replace("HN-CHUM-", "CHUM")
    output = output.replace("HN-HGJ-", "CHGJ")
    output = output.replace("HN-HMR-", "CHMR")
    output = output.replace("HN-CHUV-", "CHUV")
    return output


def get_masks(rtstruct_file,
              labels, 
              image_position_patient=None,
              axial_positions=None,
              pixel_spacing=None,
              shape=None,
              dtype=np.int8):
    contours = read_structure(rtstruct_file, labels=labels)
    return get_mask_from_contour_robust(contours,
                                 image_position_patient,
                                 axial_positions,
                                 pixel_spacing,
                                 shape,
                                 dtype=dtype)

#labels=['GTV tumor','GTV-PT', 'GTV  primaire tumor', 'gtv goed',  'GTV_CT+PET',  'GTVTumor',  'GTVtumor', 'GTV70',  'GTV_tumor','GTV PET+CT',  'gtv', 'gtv PT', 'GTV PT', 'gtv tumor', 'GTV',  'GTVpt']

def read_structure(rtstruct_file, labels):#=['gtvp', 'gtv tumor', 'gtv_pt','gtv-tumor','gtv-pt','gtvprim_tumor','gtv','gtvpt','gtv pt','gtv_tumor','gtvprimairetumor','gtv primaire tumor','gtv  primaire tumor','gtvtumor','gtv_p','gtv pet+ct','gtv pet-ct']):
    structure = pdcm.dcmread(rtstruct_file)
    contours = []

    try:
        for i, roi_seq in enumerate(structure.StructureSetROISequence):
            contour = {}
            #print("Names: ",roi_seq.ROIName)
            for label in labels:            
                if label.lower() in roi_seq.ROIName.lower():
                    contour['color'] = structure.ROIContourSequence[i].ROIDisplayColor
                    contour['number'] = structure.ROIContourSequence[i].ReferencedROINumber
                    contour['name'] = roi_seq.ROIName
                    assert contour['number'] == roi_seq.ROINumber
                    try:
                        contour['contours'] = [s.ContourData for s in structure.ROIContourSequence[i].ContourSequence]
                        contours.append(contour)
                    except AttributeError:
                        print("AttributeError in the Contour, not in the RT file")
                        continue
    except AttributeError:
        print("AttributeError, no StructureROISequence in RT")
        return contours
    return contours

def read_headers(rtstruct_file, labels=['GTV tumor','GTV-PT', 'GTV  primaire tumor', 'gtv goed',  'GTV_CT+PET',  'GTVTumor',  'GTVtumor', 'GTV70',  'GTV_tumor','GTV PET+CT',  'gtv', 'gtv PT', 'GTV PT', 'gtv tumor', 'GTV',  'GTVpt',  'GTVp']):
    structure = pdcm.dcmread(rtstruct_file)
    gtv_names = []
    try:
        for i, roi_seq in enumerate(structure.StructureSetROISequence):
            
            if  'gtv' in roi_seq.ROIName.lower() or 'primaire' in roi_seq.ROIName.lower() or 'lk' in roi_seq.ROIName.lower() or 'klie' in roi_seq.ROIName.lower() or 'ln' in roi_seq.ROIName.lower() or 'ctv' in roi_seq.ROIName.lower():

                gtv_names.append(roi_seq.ROIName)
            #gtv_names = gtv_names + [j for j in list(roi_seq.ROIName) if 'GTV' in j or 'gtv' in j]

        return list(set(gtv_names))
    except:
        return list()

def choose_rtstruct(rtstruct_file):

    for name in rtstruct_file:

        #print(name)

        structure = pdcm.dcmread(name)

        try:
            for i, roi_seq in enumerate(structure.StructureSetROISequence):
                print(roi_seq.ROIName)
                if  'gtv' in roi_seq.ROIName.lower():
                #if  ('gtvpt' in roi_seq.ROIName.lower()) or ('gtv pt' in roi_seq.ROIName.lower()) or ('gtv-pt' in roi_seq.ROIName.lower()) or ('gtv  primaire tumor' in roi_seq.ROIName.lower()):
                    print('Found name ' + roi_seq.ROIName)
                    return [name]

            for i, roi_seq in enumerate(structure.StructureSetROISequence):
                print(roi_seq.ROIName)
                if  'primaire' in roi_seq.ROIName.lower():
                #if  ('gtvpt' in roi_seq.ROIName.lower()) or ('gtv pt' in roi_seq.ROIName.lower()) or ('gtv-pt' in roi_seq.ROIName.lower()) or ('gtv  primaire tumor' in roi_seq.ROIName.lower()):
                    print('Found name ' + roi_seq.ROIName)
                    return [name]
        except:
            print('Problem with RTSTRUCT')
            continue
            
    return list()

        #print(roi_seq.ROIName)
        #for label in labels:
            
            #print(roi_seq.ROIName)


def get_mask_from_contour_robust(contours, image_position_patient, axial_positions, pixel_spacing, shape, dtype=np.uint8):
    z = np.asarray(axial_positions)
    pos_r = image_position_patient[1]
    spacing_r = pixel_spacing[1]
    pos_c = image_position_patient[0]
    spacing_c = pixel_spacing[0]

    output = []
    previous_nodes = None

    for con in contours:
        try:
            mask = np.zeros(shape, dtype=dtype)
            for current in con['contours']:
                nodes = np.array(current).reshape((-1, 3))
                if nodes.shape[0] == 1:
                    if previous_nodes is not None:
                        nodes = previous_nodes
                        print("Curr mask",con['name']," OK Interpolate node")
                    else:
                        print("Curr mask",con['name'],"Skip if no previous nodes to interpolate from")
                        continue  
                else: 
                    previous_nodes = nodes
                assert np.amax(np.abs(np.diff(nodes[:, 2]))) == 0
                z_indices = np.where((nodes[0, 2] - 0.001 < z) & (z < nodes[0, 2] + 0.001))[0]
                if z_indices.size == 0:
                    z_index = np.interp(nodes[0, 2], z, np.arange(len(z)))
                else:
                    z_index = z_indices[0]
                r = (nodes[:, 1] - pos_r) / spacing_r
                c = (nodes[:, 0] - pos_c) / spacing_c
                rr, cc = polygon(r, c)
                if len(rr) > 0 and len(cc) > 0:
                    if np.max(rr) > 512 or np.max(cc) > 512:
                        raise Exception("The RTSTRUCT file is compromised")
                mask[rr, cc, int(z_index)] = 1
            output.append((con['name'], mask))
        except Exception as e:
            print("ERROR on Dicom funs robust",e)
            continue
    return output


def get_mask_from_contour(contours,image_position_patient,axial_positions,pixel_spacing,shape,dtype=np.uint8):
    z = np.asarray(axial_positions)
    pos_r = image_position_patient[1]
    spacing_r = pixel_spacing[1]
    pos_c = image_position_patient[0]
    spacing_c = pixel_spacing[0]
    output = []
    for con in contours:
        try:
            mask = np.zeros(shape, dtype=dtype)
            for current in con['contours']:
                nodes = np.array(current).reshape((-1, 3))
                assert np.amax(np.abs(np.diff(nodes[:, 2]))) == 0
                z_index = np.where((nodes[0, 2] - 0.001 < z) & (z < nodes[0, 2] + 0.001))[0][0]
                r = (nodes[:, 1] - pos_r) / spacing_r
                c = (nodes[:, 0] - pos_c) / spacing_c
                rr, cc = polygon(r, c)
                if len(rr) > 0 and len(cc) > 0:
                    if np.max(rr) > 512 or np.max(cc) > 512:
                        raise Exception("The RTSTRUCT file is compromised")
                mask[rr, cc, z_index] = 1
            output.append((con['name'], mask))
        except Exception as e:
            print("ERROR on Dicom funs",e)
            print("")
        
    return output


def get_physical_values_ct(slices, dtype=np.float32):
    image = list()
    for s in slices:
        image.append(float(s.RescaleSlope) * s.pixel_array + float(s.RescaleIntercept))
        #image.append(s.RescaleSlope * s.pixel_array + s.RescaleIntercept)
    return np.stack(image, axis=-1).astype(dtype)


def get_physical_values_pt_old(slices):
    units = slices[0].Units
    s = slices[0]
    if units == 'BQML':
        datetime_acquisition = datetime.strptime(
            s[Tag(0x00080022)].value + s[Tag(0x00080032)].value.split('.')[0],
            "%Y%m%d%H%M%S")
        datetime_serie = datetime.strptime(
            s[Tag(0x00080021)].value + s[Tag(0x00080031)].value.split('.')[0],
            "%Y%m%d%H%M%S")
        if datetime_serie < datetime_acquisition and datetime_serie > datetime(
                1950, 1, 1):
            pass
        else:
            pass
        return get_suv_from_bqml(slices)
    elif units == 'CNTS':
        return get_suv_philips(slices)
    else:
        raise ValueError('The {} units is not handled'.format(units))

def get_physical_values_pt_new(slices, patient_weight, dtype=np.float32):
    s = slices[0]
    units = s.Units

    if units == 'BQML':

        start_time_str = s.RadiopharmaceuticalInformationSequence[0].RadiopharmaceuticalStartTime
        start_time = time(int(start_time_str[0:2]),
                            int(start_time_str[2:4]),
                            int(start_time_str[4:6]))
        
        scan_time = datetime.strptime(
                    s[Tag(0x00080021)].value + s[Tag(0x00080031)].value.split('.')[0],
                    "%Y%m%d%H%M%S")
        start_datetime = datetime.combine(scan_time.date(), start_time)
        
        decay_time = (scan_time-start_datetime).total_seconds()

        return get_suv_from_bqml_new(slices,
                                 decay_time,
                                 patient_weight,
                                 dtype=dtype)

def get_suv_from_bqml_new(slices, decay_time, patient_weight, dtype=np.float32):
    # Get SUV from raw PET
    image = list()
    for s in slices:
        pet = float(s.RescaleSlope) * s._pixel_array + float(s.RescaleIntercept)
        half_life = float(
            s.RadiopharmaceuticalInformationSequence[0].RadionuclideHalfLife)
        total_dose = float(
            s.RadiopharmaceuticalInformationSequence[0].RadionuclideTotalDose)
        decay = 2**(-decay_time / half_life)
        actual_activity = total_dose * decay

        im = pet * patient_weight * 1000 / actual_activity
        image.append(im)
    return np.stack(image, axis=-1).astype(dtype)


def get_physical_values_pt(slices, patient_weight, dtype=np.float32):
    s = slices[0]
    units = s.Units
    if units == 'BQML':

        acquisition_datetime = datetime.strptime(
            s[Tag(0x00080022)].value + s[Tag(0x00080032)].value.split('.')[0],
            "%Y%m%d%H%M%S")
        serie_datetime = datetime.strptime(
            s[Tag(0x00080021)].value + s[Tag(0x00080031)].value.split('.')[0],
            "%Y%m%d%H%M%S")

        try:
            if (serie_datetime <= acquisition_datetime) and (
                    serie_datetime > datetime(1950, 1, 1)):
                scan_datetime = serie_datetime
            else:
                scan_datetime_value = s[Tag(0x0009100d)].value
                if isinstance(scan_datetime_value, bytes):
                    scan_datetime_str = scan_datetime_value.decode(
                        "utf-8").split('.')[0]
                elif isinstance(scan_datetime_value, str):
                    scan_datetime_str = scan_datetime_value.split('.')[0]
                else:
                    raise ValueError(
                        "The value of scandatetime is not handled")
                scan_datetime = datetime.strptime(scan_datetime_str,
                                                  "%Y%m%d%H%M%S")

            start_time_str = s.RadiopharmaceuticalInformationSequence[
                0].RadiopharmaceuticalStartTime
            start_time = time(int(start_time_str[0:2]),
                              int(start_time_str[2:4]),
                              int(start_time_str[4:6]))
            start_datetime = datetime.combine(scan_datetime.date(), start_time)
            decay_time = (scan_datetime - start_datetime).total_seconds()
        except KeyError:
            warnings.warn("Estimation of time decay for SUV"
                          " computation from average parameters")
            decay_time = 1.75 * 3600  # From Martin's code
        return get_suv_from_bqml(slices,
                                 decay_time,
                                 patient_weight,
                                 dtype=dtype)

    elif units == 'CNTS':
        return get_suv_philips(slices, dtype=dtype)
    else:
        raise ValueError('The {} units is not handled'.format(units))



def get_suv_philips(slices, dtype=np.float32):
    image = list()
    suv_scale_factor_tag = Tag(0x70531000)
    for s in slices:
        im = (float(s.RescaleSlope) * s._pixel_array +
              float(s.RescaleIntercept)) * float(s[suv_scale_factor_tag].value)
        image.append(im)
    return np.stack(image, axis=-1).astype(dtype)


def get_suv_from_bqml(slices, decay_time, patient_weight, dtype=np.float32):
    # Get SUV from raw PET
    image = list()
    for s in slices:
        pet = float(s.RescaleSlope) * s._pixel_array + float(s.RescaleIntercept)
        half_life = float(
            s.RadiopharmaceuticalInformationSequence[0].RadionuclideHalfLife)
        total_dose = float(
            s.RadiopharmaceuticalInformationSequence[0].RadionuclideTotalDose)
        decay = 2**(-decay_time / half_life)
        actual_activity = total_dose * decay

        im = pet * patient_weight * 1000 / actual_activity
        image.append(im)
    return np.stack(image, axis=-1).astype(dtype)
