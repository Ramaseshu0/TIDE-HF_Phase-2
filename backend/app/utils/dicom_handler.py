import pydicom
from pydicom.errors import InvalidDicomError
from typing import Dict, Any, Optional
from io import BytesIO
import numpy as np
from PIL import Image
import base64


class DICOMHandler:
    """Service for handling DICOM medical images"""

    @staticmethod
    def is_dicom_file(file_bytes: bytes) -> bool:
        """Check if a file is a valid DICOM file"""
        try:
            pydicom.dcmread(BytesIO(file_bytes), stop_before_pixels=True)
            return True
        except (InvalidDicomError, Exception):
            return False

    @staticmethod
    def extract_dicom_metadata(file_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Extract metadata from DICOM file"""
        try:
            dicom = pydicom.dcmread(BytesIO(file_bytes))

            metadata = {
                # Patient Information
                'patient_name': str(dicom.get('PatientName', 'Unknown')),
                'patient_id': str(dicom.get('PatientID', 'Unknown')),
                'patient_birth_date': str(dicom.get('PatientBirthDate', 'Unknown')),
                'patient_sex': str(dicom.get('PatientSex', 'Unknown')),
                'patient_age': str(dicom.get('PatientAge', 'Unknown')),

                # Study Information
                'study_date': str(dicom.get('StudyDate', 'Unknown')),
                'study_time': str(dicom.get('StudyTime', 'Unknown')),
                'study_description': str(dicom.get('StudyDescription', 'Unknown')),
                'study_instance_uid': str(dicom.get('StudyInstanceUID', 'Unknown')),

                # Series Information
                'series_description': str(dicom.get('SeriesDescription', 'Unknown')),
                'series_number': str(dicom.get('SeriesNumber', 'Unknown')),
                'series_instance_uid': str(dicom.get('SeriesInstanceUID', 'Unknown')),

                # Image Information
                'modality': str(dicom.get('Modality', 'Unknown')),
                'body_part_examined': str(dicom.get('BodyPartExamined', 'Unknown')),
                'image_type': str(dicom.get('ImageType', 'Unknown')),

                # Technical Information
                'manufacturer': str(dicom.get('Manufacturer', 'Unknown')),
                'manufacturer_model_name': str(dicom.get('ManufacturerModelName', 'Unknown')),
                'rows': int(dicom.get('Rows', 0)),
                'columns': int(dicom.get('Columns', 0)),
                'pixel_spacing': str(dicom.get('PixelSpacing', 'Unknown')),
                'slice_thickness': str(dicom.get('SliceThickness', 'Unknown')),

                # Institution Information
                'institution_name': str(dicom.get('InstitutionName', 'Unknown')),
                'referring_physician_name': str(dicom.get('ReferringPhysicianName', 'Unknown')),
            }

            return metadata

        except Exception as e:
            print(f"Error extracting DICOM metadata: {e}")
            return None

    @staticmethod
    def convert_dicom_to_image(file_bytes: bytes) -> Optional[bytes]:
        """Convert DICOM file to PNG image"""
        try:
            dicom = pydicom.dcmread(BytesIO(file_bytes))

            # Get pixel array
            pixel_array = dicom.pixel_array

            # Normalize to 0-255 range
            pixel_array = pixel_array - np.min(pixel_array)
            pixel_array = pixel_array / np.max(pixel_array)
            pixel_array = (pixel_array * 255).astype(np.uint8)

            # Convert to PIL Image
            image = Image.fromarray(pixel_array)

            # Convert to bytes
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            return img_byte_arr.getvalue()

        except Exception as e:
            print(f"Error converting DICOM to image: {e}")
            return None

    @staticmethod
    def get_dicom_thumbnail(file_bytes: bytes, size: tuple = (256, 256)) -> Optional[str]:
        """Generate a thumbnail from DICOM file and return as base64"""
        try:
            image_bytes = DICOMHandler.convert_dicom_to_image(file_bytes)
            if not image_bytes:
                return None

            # Create thumbnail
            image = Image.open(BytesIO(image_bytes))
            image.thumbnail(size, Image.Resampling.LANCZOS)

            # Convert to base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"

        except Exception as e:
            print(f"Error generating DICOM thumbnail: {e}")
            return None

    @staticmethod
    def validate_dicom_series(file_bytes_list: list) -> Dict[str, Any]:
        """Validate if multiple DICOM files belong to the same series"""
        try:
            series_uids = set()
            study_uids = set()

            for file_bytes in file_bytes_list:
                dicom = pydicom.dcmread(BytesIO(file_bytes), stop_before_pixels=True)
                series_uids.add(str(dicom.get('SeriesInstanceUID', '')))
                study_uids.add(str(dicom.get('StudyInstanceUID', '')))

            return {
                'is_valid_series': len(series_uids) == 1,
                'same_study': len(study_uids) == 1,
                'series_count': len(series_uids),
                'study_count': len(study_uids)
            }

        except Exception as e:
            print(f"Error validating DICOM series: {e}")
            return {
                'is_valid_series': False,
                'error': str(e)
            }
