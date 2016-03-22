# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Qt.ListModel import ListModel
from UM.Application import Application
from UM.Signal import Signal, SignalEmitter
from UM.Settings import SettingsError
from UM.Resources import Resources
from UM.Logger import Logger

from PyQt5.QtCore import Qt, pyqtSlot

import os
import configparser
import io #For serialising the profile to strings.

class MaterialsModel(ListModel):
    NameRole = Qt.UserRole + 1
    GroupRole = Qt.UserRole + 2
    VariantRole = Qt.UserRole + 3
    SupplierRole = Qt.UserRole + 4


    def __init__(self, parent = None):
        super().__init__(parent)

        self._material_profiles = []

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.GroupRole, "group")
        self.addRoleName(self.VariantRole, "variant")
        self.addRoleName(self.SupplierRole, "supplier")

        self.loadMaterials()

        for material_profile in self._material_profiles:
            general_data = material_profile.getGeneralData()
            self.appendItem({
                "name": general_data["name"],
                "group": general_data["type"],
                "variant": general_data["color"],
                "supplier": general_data["supplier"]
            })

    def loadMaterials(self):
        dirs = Resources.getAllPathsForType(Application.getInstance().ResourceTypes.Materials)
        for dir in dirs:
            if not os.path.isdir(dir):
                continue

            for root, dirs, files in os.walk(dir):
                for file_name in files:
                    path = os.path.join(root, file_name)

                    if os.path.isdir(path):
                        continue

                    # Bit of a hack, but we should only use cfg or curaprofile files in the profile folder.
                    try:
                        extension = path.split(".")[-1]
                        if  extension != "cfg" and extension != "curaprofile":
                            continue
                    except:
                        continue # profile has no extension

                    material_profile = MaterialProfile()
                    try:
                        material_profile.loadFromFile(path)
                    except Exception as e:
                        Logger.log("e", "An exception occurred loading Profile %s: %s", path, str(e))
                        continue

                    self._material_profiles.append(material_profile)


class MaterialProfile(SignalEmitter):
    ProfileVersion = 1

    ##  Constructor.
    def __init__(self):
        super().__init__()

        self._general = {}
        self._metadata = {}
        self._settings = {}

    def getGeneralData(self):
        return self._general

    def getMetaData(self):
        return self._metadata

    def getSettingsData(self):
        return self._settings

    ##  Load a serialised profile from a file.
    #
    #   The read is currently not atomic, only the write is. So this method
    #   assumes that there are no other processes than this Cura instance
    #   writing to the file. If there are, the ConfigParser will likely fail
    #   (but the file doesn't get corrupt).
    #   \param path The path to the file to load from.
    def loadFromFile(self, path):
        f = open(path) #Open file for reading.
        serialised = f.read()
        self.unserialise(serialised, path) #Unserialise the serialised contents that we found in that file.

    ##  Load a serialized profile from a string.
    #
    #   The unserialised profile is saved in this instance.
    #   \param serialised A string containing the serialised form of the
    #   profile.
    #   \param origin A string representing the origin of this serialised
    #   string. This is only used when an error occurs.
    def unserialise(self, serialised, origin = "(unknown)"):
        stream = io.StringIO(serialised) #ConfigParser needs to read from a stream.
        parser = configparser.ConfigParser(interpolation = None)
        parser.readfp(stream)

        if not parser.has_section("general"):
            raise SettingsError.InvalidFileError(origin)

        if not parser.has_option("general", "version") or int(parser.get("general", "version")) != self.ProfileVersion:
            raise SettingsError.InvalidVersionError(origin)

        for key, value in parser["general"].items():
            self._general[key] = value

        if parser.has_section("metadata"):
            for key, value in parser["metadata"].items():
                self._metadata[key] = value

        if parser.has_section("settings"):
            for key, value in parser["settings"].items():
                self._settings[key] = value
