# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os
import os.path
import re
from PyQt5.QtWidgets import QMessageBox

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.Platform import Platform
from UM.PluginRegistry import PluginRegistry #For getting the possible profile writers to write with.
from UM.Util import parseBool

from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.ContainerManager import ContainerManager

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class CuraContainerRegistry(ContainerRegistry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ##  Create a name that is not empty and unique
    #   \param container_type \type{string} Type of the container (machine, quality, ...)
    #   \param current_name \type{} Current name of the container, which may be an acceptable option
    #   \param new_name \type{string} Base name, which may not be unique
    #   \param fallback_name \type{string} Name to use when (stripped) new_name is empty
    #   \return \type{string} Name that is unique for the specified type and name/id
    def createUniqueName(self, container_type, current_name, new_name, fallback_name):
        new_name = new_name.strip()
        num_check = re.compile("(.*?)\s*#\d+$").match(new_name)
        if num_check:
            new_name = num_check.group(1)
        if new_name == "":
            new_name = fallback_name

        unique_name = new_name
        i = 1
        # In case we are renaming, the current name of the container is also a valid end-result
        while self._containerExists(container_type, unique_name) and unique_name != current_name:
            i += 1
            unique_name = "%s #%d" % (new_name, i)

        return unique_name

    ##  Check if a container with of a certain type and a certain name or id exists
    #   Both the id and the name are checked, because they may not be the same and it is better if they are both unique
    #   \param container_type \type{string} Type of the container (machine, quality, ...)
    #   \param container_name \type{string} Name to check
    def _containerExists(self, container_type, container_name):
        container_class = ContainerStack if container_type == "machine" else InstanceContainer

        return self.findContainers(container_class, id = container_name, type = container_type, ignore_case = True) or \
                self.findContainers(container_class, name = container_name, type = container_type)

    ##  Exports an profile to a file
    #
    #   \param instance_ids \type{list} the IDs of the profiles to export.
    #   \param file_name \type{str} the full path and filename to export to.
    #   \param file_type \type{str} the file type with the format "<description> (*.<extension>)"
    def exportProfile(self, instance_ids, file_name, file_type):
        # Parse the fileType to deduce what plugin can save the file format.
        # fileType has the format "<description> (*.<extension>)"
        split = file_type.rfind(" (*.")  # Find where the description ends and the extension starts.
        if split < 0:  # Not found. Invalid format.
            Logger.log("e", "Invalid file format identifier %s", file_type)
            return
        description = file_type[:split]
        extension = file_type[split + 4:-1]  # Leave out the " (*." and ")".
        if not file_name.endswith("." + extension):  # Auto-fill the extension if the user did not provide any.
            file_name += "." + extension

        # On Windows, QML FileDialog properly asks for overwrite confirm, but not on other platforms, so handle those ourself.
        if not Platform.isWindows():
            if os.path.exists(file_name):
                result = QMessageBox.question(None, catalog.i18nc("@title:window", "File Already Exists"),
                                              catalog.i18nc("@label", "The file <filename>{0}</filename> already exists. Are you sure you want to overwrite it?").format(file_name))
                if result == QMessageBox.No:
                    return
        found_containers = []
        extruder_positions = []
        for instance_id in instance_ids:
            containers = ContainerRegistry.getInstance().findInstanceContainers(id=instance_id)
            if containers:
                found_containers.append(containers[0])

                # Determine the position of the extruder of this container
                extruder_id = containers[0].getMetaDataEntry("extruder", "")
                if extruder_id == "":
                    # Global stack
                    extruder_positions.append(-1)
                else:
                    extruder_containers = ContainerRegistry.getInstance().findDefinitionContainers(id=extruder_id)
                    if extruder_containers:
                        extruder_positions.append(int(extruder_containers[0].getMetaDataEntry("position", 0)))
                    else:
                        extruder_positions.append(0)
        # Ensure the profiles are always exported in order (global, extruder 0, extruder 1, ...)
        found_containers = [containers for (positions, containers) in sorted(zip(extruder_positions, found_containers))]

        profile_writer = self._findProfileWriter(extension, description)

        try:
            success = profile_writer.write(file_name, found_containers)
        except Exception as e:
            Logger.log("e", "Failed to export profile to %s: %s", file_name, str(e))
            m = Message(catalog.i18nc("@info:status", "Failed to export profile to <filename>{0}</filename>: <message>{1}</message>", file_name, str(e)), lifetime = 0)
            m.show()
            return
        if not success:
            Logger.log("w", "Failed to export profile to %s: Writer plugin reported failure.", file_name)
            m = Message(catalog.i18nc("@info:status", "Failed to export profile to <filename>{0}</filename>: Writer plugin reported failure.", file_name), lifetime = 0)
            m.show()
            return
        m = Message(catalog.i18nc("@info:status", "Exported profile to <filename>{0}</filename>", file_name))
        m.show()

    ##  Gets the plugin object matching the criteria
    #   \param extension
    #   \param description
    #   \return The plugin object matching the given extension and description.
    def _findProfileWriter(self, extension, description):
        plugin_registry = PluginRegistry.getInstance()
        for plugin_id, meta_data in self._getIOPlugins("profile_writer"):
            for supported_type in meta_data["profile_writer"]:  # All file types this plugin can supposedly write.
                supported_extension = supported_type.get("extension", None)
                if supported_extension == extension:  # This plugin supports a file type with the same extension.
                    supported_description = supported_type.get("description", None)
                    if supported_description == description:  # The description is also identical. Assume it's the same file type.
                        return plugin_registry.getPluginObject(plugin_id)
        return None

    ##  Imports a profile from a file
    #
    #   \param file_name \type{str} the full path and filename of the profile to import
    #   \return \type{Dict} dict with a 'status' key containing the string 'ok' or 'error', and a 'message' key
    #       containing a message for the user
    def importProfile(self, file_name):
        Logger.log("d", "Attempting to import profile %s", file_name)
        if not file_name:
            return { "status": "error", "message": catalog.i18nc("@info:status", "Failed to import profile from <filename>{0}</filename>: <message>{1}</message>", file_name, "Invalid path")}

        plugin_registry = PluginRegistry.getInstance()
        extension = file_name.split(".")[-1]

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return

        machine_extruders = list(ExtruderManager.getInstance().getMachineExtruders(global_container_stack.getId()))
        machine_extruders.sort(key = lambda k: k.getMetaDataEntry("position"))

        for plugin_id, meta_data in self._getIOPlugins("profile_reader"):
            if meta_data["profile_reader"][0]["extension"] != extension:
                continue

            profile_reader = plugin_registry.getPluginObject(plugin_id)
            try:
                profile_or_list = profile_reader.read(file_name)  # Try to open the file with the profile reader.
            except Exception as e:
                # Note that this will fail quickly. That is, if any profile reader throws an exception, it will stop reading. It will only continue reading if the reader returned None.
                Logger.log("e", "Failed to import profile from %s: %s while using profile reader. Got exception %s", file_name,profile_reader.getPluginId(), str(e))
                return { "status": "error", "message": catalog.i18nc("@info:status", "Failed to import profile from <filename>{0}</filename>: <message>{1}</message>", file_name, str(e))}
            if profile_or_list: # Success!
                name_seed = os.path.splitext(os.path.basename(file_name))[0]
                new_name = self.uniqueName(name_seed)
                if type(profile_or_list) is not list:
                    profile = profile_or_list
                    self._configureProfile(profile, name_seed, new_name)
                    return { "status": "ok", "message": catalog.i18nc("@info:status", "Successfully imported profile {0}", profile.getName()) }
                else:
                    profile_index = -1
                    global_profile = None

                    for profile in profile_or_list:
                        if profile_index >= 0:
                            if len(machine_extruders) > profile_index:
                                extruder_id = Application.getInstance().getMachineManager().getQualityDefinitionId(machine_extruders[profile_index].getBottom())
                                # Ensure the extruder profiles get non-conflicting names
                                # NB: these are not user-facing
                                if "extruder" in profile.getMetaData():
                                    profile.setMetaDataEntry("extruder", extruder_id)
                                else:
                                    profile.addMetaDataEntry("extruder", extruder_id)
                                profile_id = (extruder_id + "_" + name_seed).lower().replace(" ", "_")
                            elif profile_index == 0:
                                # Importing a multiextrusion profile into a single extrusion machine; merge 1st extruder profile into global profile
                                profile._id = self.uniqueName("temporary_profile")
                                self.addContainer(profile)
                                ContainerManager.getInstance().mergeContainers(global_profile.getId(), profile.getId())
                                self.removeContainer(profile.getId())
                                break
                            else:
                                # The imported composite profile has a profile for an extruder that this machine does not have. Ignore this extruder-profile
                                break
                        else:
                            global_profile = profile
                            profile_id = (global_container_stack.getBottom().getId() + "_" + name_seed).lower().replace(" ", "_")

                        self._configureProfile(profile, profile_id, new_name)

                        profile_index += 1

                    return {"status": "ok", "message": catalog.i18nc("@info:status", "Successfully imported profile {0}", profile_or_list[0].getName())}

        # If it hasn't returned by now, none of the plugins loaded the profile successfully.
        return {"status": "error", "message": catalog.i18nc("@info:status", "Profile {0} has an unknown file type or is corrupted.", file_name)}

    def _configureProfile(self, profile, id_seed, new_name):
        profile.setReadOnly(False)
        profile.setDirty(True)  # Ensure the profiles are correctly saved

        new_id = self.createUniqueName("quality_changes", "", id_seed, catalog.i18nc("@label", "Custom profile"))
        profile._id = new_id
        profile.setName(new_name)

        if "type" in profile.getMetaData():
            profile.setMetaDataEntry("type", "quality_changes")
        else:
            profile.addMetaDataEntry("type", "quality_changes")

        if self._machineHasOwnQualities():
            profile.setDefinition(self._activeQualityDefinition())
            if self._machineHasOwnMaterials():
                profile.addMetaDataEntry("material", self._activeMaterialId())
        else:
            profile.setDefinition(ContainerRegistry.getInstance().findDefinitionContainers(id="fdmprinter")[0])

        ContainerRegistry.getInstance().addContainer(profile)

    ##  Gets a list of profile writer plugins
    #   \return List of tuples of (plugin_id, meta_data).
    def _getIOPlugins(self, io_type):
        plugin_registry = PluginRegistry.getInstance()
        active_plugin_ids = plugin_registry.getActivePlugins()

        result = []
        for plugin_id in active_plugin_ids:
            meta_data = plugin_registry.getMetaData(plugin_id)
            if io_type in meta_data:
                result.append( (plugin_id, meta_data) )
        return result

    ##  Get the definition to use to select quality profiles for the active machine
    #   \return the active quality definition object or None if there is no quality definition
    def _activeQualityDefinition(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            definition_id = Application.getInstance().getMachineManager().getQualityDefinitionId(global_container_stack.getBottom())
            definition = self.findDefinitionContainers(id=definition_id)[0]

            if definition:
                return definition
        return None

    ##  Returns true if the current machine requires its own materials
    #   \return True if the current machine requires its own materials
    def _machineHasOwnMaterials(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getMetaDataEntry("has_materials", False)
        return False

    ##  Gets the ID of the active material
    #   \return the ID of the active material or the empty string
    def _activeMaterialId(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            material = global_container_stack.findContainer({"type": "material"})
            if material:
                return material.getId()
        return ""

    ##  Returns true if the current machien requires its own quality profiles
    #   \return true if the current machien requires its own quality profiles
    def _machineHasOwnQualities(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            return parseBool(global_container_stack.getMetaDataEntry("has_machine_quality", False))
        return False
