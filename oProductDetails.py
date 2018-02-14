import os;

from mProductVersionAndLicense import cProductDetails;

sProductFolderPath = os.path.dirname(__file__);
oProductDetails = cProductDetails.foReadFromFolderPath(sProductFolderPath);
