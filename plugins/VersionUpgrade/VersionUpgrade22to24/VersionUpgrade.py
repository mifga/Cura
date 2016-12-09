# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import configparser #To get version numbers from config files.
import os
import os.path
import io

from UM import Resources
from UM.VersionUpgrade import VersionUpgrade # Superclass of the plugin.

class VersionUpgrade22to24(VersionUpgrade):

    def upgradeMachineInstance(self, serialised, filename):
        # All of this is needed to upgrade custom variant machines from old Cura to 2.4 where
        # `definition_changes` instance container has been introduced. Variant files which
        # look like the the handy work of the old machine settings plugin are converted directly
        # on disk.

        config = configparser.ConfigParser(interpolation = None)
        config.read_string(serialised) # Read the input string as config file.
        config.set("general", "version", "3")

        container_list = []
        if config.has_section("containers"):
            for index, container_id in config.items("containers"):
                container_list.append(container_id)
        elif config.has_option("general", "containers"):
            containers = config.get("general", "containers")
            container_list = containers.split(",")

        user_variants = self.__getUserVariants()
        name_path_dict = {}
        for variant in user_variants:
            name_path_dict[variant.get("name")] = variant.get("path")

        user_variant_names = set(container_list).intersection(name_path_dict.keys())
        if len(user_variant_names):
            # One of the user defined variants appears in the list of containers in the stack.

            for variant_name in user_variant_names: # really there should just be one variant to convert.
                config_name = self.__convertVariant(name_path_dict.get(variant_name))

                # Change the name of variant and insert empty_variant into the stack.
                new_container_list = []
                for item in container_list:
                    if item == variant_name:
                        new_container_list.append(config_name)
                        new_container_list.append("empty_variant")
                    else:
                        new_container_list.append(item)

                container_list = new_container_list

            if not config.has_section("containers"):
                config.add_section("containers")

            config.remove_option("general", "containers")

            for index in range(len(container_list)):
                config.set("containers", index, container_list[index])

        output = io.StringIO()
        config.write(output)
        return [filename], [output.getvalue()]

    def __convertVariant(self, variant_path):
        # Copy the variant to the machine_instances/*_settings.inst.cfg
        variant_config = configparser.ConfigParser(interpolation=None)
        with open(variant_path, "r") as fhandle:
            variant_config.read_file(fhandle)

        if variant_config.has_section("general") and variant_config.has_option("general", "name"):
            config_name = variant_config.get("general", "name")
            if config_name.endswith("_variant"):
                config_name = config_name[:-len("_variant")] + "_settings"
                variant_config.set("general", "name", config_name)

        if not variant_config.has_section("metadata"):
            variant_config.add_section("metadata")
        variant_config.set("metadata", "type", "definition_changes")

        resource_path = Resources.getDataStoragePath()
        machine_instances_dir = os.path.join(resource_path, "machine_instances")

        if variant_path.endswith("_variant.inst.cfg"):
            variant_path = variant_path[:-len("_variant.inst.cfg")] + "_settings.inst.cfg"

        with open(os.path.join(machine_instances_dir, os.path.basename(variant_path)), "w") as fp:
            variant_config.write(fp)

        return config_name

    def __getUserVariants(self):
        resource_path = Resources.getDataStoragePath()
        variants_dir = os.path.join(resource_path, "variants")

        result = []
        for entry in os.scandir(variants_dir):
            if entry.name.endswith('.inst.cfg') and entry.is_file():
                config = configparser.ConfigParser(interpolation = None)
                with open(entry.path, "r") as fhandle:
                    config.read_file(fhandle)
                if config.has_section("general") and config.has_option("general", "name"):
                    result.append( { "path": entry.path, "name": config.get("general", "name") } )
        return result

    def upgradeExtruderTrain(self, serialised, filename):
        config = configparser.ConfigParser(interpolation = None)
        config.read_string(serialised) # Read the input string as config file.
        config.set("general", "version", "3")   # Just bump the version number. That is all we need for now.

        output = io.StringIO()
        config.write(output)
        return [filename], [output.getvalue()]

    def getCfgVersion(self, serialised):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        return int(parser.get("general", "version")) #Explicitly give an exception when this fails. That means that the file format is not recognised.
