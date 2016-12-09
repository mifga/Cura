# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from UM.Application import Application

from cura.QualityManager import QualityManager
from cura.Settings.ProfilesModel import ProfilesModel
from cura.Settings.ExtruderManager import ExtruderManager

##  QML Model for listing the current list of valid quality changes profiles.
#
class UserProfilesModel(ProfilesModel):
    def __init__(self, parent = None):
        super().__init__(parent)

    ##  Fetch the list of containers to display.
    #
    #   See UM.Settings.Models.InstanceContainersModel._fetchInstanceContainers().
    def _fetchInstanceContainers(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return []

        # Fetch the list of quality changes.
        quality_manager = QualityManager.getInstance()
        machine_definition = quality_manager.getParentMachineDefinition(global_container_stack.getBottom())
        quality_changes_list = quality_manager.findAllQualityChangesForMachine(machine_definition)

        # Fetch the list of qualities
        quality_list =  QualityManager.getInstance().findAllUsableQualitiesForMachineAndExtruders(global_container_stack,
                                                              ExtruderManager.getInstance().getActiveExtruderStacks())

        # Filter the quality_change by the list of available quality_types
        quality_type_set = set([x.getMetaDataEntry("quality_type") for x in quality_list])
        filtered_quality_changes = [qc for qc in quality_changes_list if qc.getMetaDataEntry("quality_type") in quality_type_set]

        return filtered_quality_changes
