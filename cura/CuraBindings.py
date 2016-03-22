# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from PyQt5.QtQml import qmlRegisterType

from . import MaterialsModel

class CuraBindings:
    @classmethod
    def register(self):
        # Additions after 15.06. Uses API version 1.1 so should be imported with "import UM 1.1"
        qmlRegisterType(MaterialsModel.MaterialsModel, "UM", 1, 1, "MaterialsModel")
