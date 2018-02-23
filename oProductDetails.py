import os;
from mProductDetails import cProductDetails;

sProductFolderPath = os.path.dirname(__file__);
oProductDetails = cProductDetails.foReadFromFolderPath(sProductFolderPath);
