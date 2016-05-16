
from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from UM.Application import Application
from UM.Preferences import Preferences

import UM.Settings

class MachineManagerModel(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)

        ##  When the global container is changed, active material probably needs to be updated.
        self.globalContainerChanged.connect(self.activeMaterialChanged)
        self.globalContainerChanged.connect(self.activeVariantChanged)

        Preferences.getInstance().addPreference("cura/active_machine", "")

        active_machine_id = Preferences.getInstance().getValue("cura/active_machine")
        if active_machine_id != "":
            # An active machine was saved, so restore it.
            self.setActiveMachine(active_machine_id)
            pass


    globalContainerChanged = pyqtSignal()
    activeMaterialChanged = pyqtSignal()
    activeVariantChanged = pyqtSignal()

    def _onGlobalContainerChanged(self):
        Preferences.getInstance().setValue("cura/active_machine", Application.getInstance().getGlobalContainerStack().getId())
        Application.getInstance().getGlobalContainerStack().containersChanged.connect(self._onInstanceContainersChanged)
        self.globalContainerChanged.emit()

    def _onInstanceContainersChanged(self, container):
        container_type = container.getMetaDataEntry("type")
        if container_type == "material":
            self.activeMaterialChanged.emit()
        elif container_type == "variant":
            self.activeVariantChanged.emit()

    @pyqtSlot(str)
    def setActiveMachine(self, stack_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(id = stack_id)
        if containers:
            Application.getInstance().setGlobalContainerStack(containers[0])

    @pyqtSlot(str, str)
    def addMachine(self,name, definition_id):
        definitions = UM.Settings.ContainerRegistry.getInstance().findDefinitionContainers(id=definition_id)
        if definitions:
            new_global_stack = UM.Settings.ContainerStack(name)
            new_global_stack.addMetaDataEntry("type", "machine")
            UM.Settings.ContainerRegistry.getInstance().addContainer(new_global_stack)

            ## DEBUG CODE
            material_instance_container = UM.Settings.InstanceContainer("test_material")
            material_instance_container.addMetaDataEntry("type", "material")
            material_instance_container.setDefinition(definitions[0])

            variant_instance_container = UM.Settings.InstanceContainer("test_variant")
            variant_instance_container.addMetaDataEntry("type", "variant")
            variant_instance_container.setDefinition(definitions[0])

            quality_instance_container = UM.Settings.InstanceContainer(name + "_quality")
            UM.Settings.ContainerRegistry.getInstance().addContainer(material_instance_container)
            UM.Settings.ContainerRegistry.getInstance().addContainer(variant_instance_container)

            current_settings_instance_container = UM.Settings.InstanceContainer(name + "_current_settings")
            current_settings_instance_container.addMetaDataEntry("machine", name)
            current_settings_instance_container.setDefinition(definitions[0])
            UM.Settings.ContainerRegistry.getInstance().addContainer(current_settings_instance_container)

            # If a definition is found, its a list. Should only have one item.
            new_global_stack.addContainer(definitions[0])
            new_global_stack.addContainer(material_instance_container)
            new_global_stack.addContainer(variant_instance_container)
            new_global_stack.addContainer(current_settings_instance_container)

            Application.getInstance().setGlobalContainerStack(new_global_stack)

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineName(self):
        return Application.getInstance().getGlobalContainerStack().getName()

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineId(self):
        return Application.getInstance().getGlobalContainerStack().getId()

    @pyqtProperty(str, notify = activeMaterialChanged)
    def activeMaterialName(self):
        material = Application.getInstance().getGlobalContainerStack().findContainer({"type":"material"})
        if material:
            return material.getName()

    @pyqtProperty(str, notify=activeMaterialChanged)
    def activeMaterialId(self):
        material = Application.getInstance().getGlobalContainerStack().findContainer({"type": "material"})
        if material:
            return material.getId()

    @pyqtSlot(str)
    def setActiveMaterial(self, material_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id=material_id)
        old_material = Application.getInstance().getGlobalContainerStack().findContainer({"type":"material"})
        if old_material:
            material_index = Application.getInstance().getGlobalContainerStack().getContainerIndex(old_material)
            Application.getInstance().getGlobalContainerStack().replaceContainer(material_index, containers[0])

    @pyqtSlot(str)
    def setActiveVariant(self, variant_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id=variant_id)
        old_variant = Application.getInstance().getGlobalContainerStack().findContainer({"type": "variant"})
        if old_variant:
            variant_index = Application.getInstance().getGlobalContainerStack().getContainerIndex(old_variant)
            Application.getInstance().getGlobalContainerStack().replaceContainer(variant_index, containers[0])

    @pyqtProperty(str, notify = activeVariantChanged)
    def activeVariantName(self):
        variant = Application.getInstance().getGlobalContainerStack().findContainer({"type": "variant"})
        if variant:
            return variant.getName()

    @pyqtProperty(str, notify = activeVariantChanged)
    def activeVariantId(self):
        variant = Application.getInstance().getGlobalContainerStack().findContainer({"type": "variant"})
        if variant:
            return variant.getId()

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeDefinitionId(self):
        return Application.getInstance().getGlobalContainerStack().getBottom().id

    @pyqtSlot(str, str)
    def renameMachine(self, machine_id, new_name):
        containers = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(id = machine_id)
        if containers:
            containers[0].setName(new_name)

    @pyqtProperty(str, notify=globalContainerChanged)
    def activeMachineDefinitionId(self):
        return Application.getInstance().getGlobalContainerStack().getContainers()[-1].getId()

    @pyqtSlot(str)
    def removeMachine(self, machine_id):
        UM.Settings.ContainerRegistry.getInstance().removeContainer(machine_id)

    @pyqtProperty(bool)
    def hasMaterials(self):
        # Todo: Still hardcoded.
        #  We should implement this properly when it's clear how a machine notifies us if it can handle materials
        return True

    @pyqtProperty(bool)
    def hasVariants(self):
        # Todo: Still hardcoded.
        #  We should implement this properly when it's clear how a machine notifies us if it can handle variants
        return True

def createMachineManagerModel(engine, script_engine):
    return MachineManagerModel()