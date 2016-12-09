# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources
from UM.Scene.SceneNode import SceneNode
from UM.Scene.ToolHandle import ToolHandle
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry

from UM.View.RenderPass import RenderPass
from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL

from cura.Settings.ExtruderManager import ExtruderManager

import os.path

## RenderPass used to display g-code paths.
class LayerPass(RenderPass):
    def __init__(self, width, height):
        super().__init__("layerview", width, height)

        self._layer_shader = None
        self._tool_handle_shader = None
        self._gl = OpenGL.getInstance().getBindingsObject()
        self._scene = Application.getInstance().getController().getScene()
        self._extruder_manager = ExtruderManager.getInstance()

        self._layer_view = None

    def setLayerView(self, layerview):
        self._layerview = layerview

    def render(self):
        if not self._layer_shader:
            self._layer_shader = OpenGL.getInstance().createShaderProgram(os.path.join(PluginRegistry.getInstance().getPluginPath("LayerView"), "layers.shader"))
        # Use extruder 0 if the extruder manager reports extruder index -1 (for single extrusion printers)
        self._layer_shader.setUniformValue("u_active_extruder", float(max(0, self._extruder_manager.activeExtruderIndex)))
        if not self._tool_handle_shader:
            self._tool_handle_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "toolhandle.shader"))

        self.bind()

        tool_handle_batch = RenderBatch(self._tool_handle_shader, type = RenderBatch.RenderType.Overlay)

        for node in DepthFirstIterator(self._scene.getRoot()):
            if isinstance(node, ToolHandle):
                tool_handle_batch.addItem(node.getWorldTransformation(), mesh = node.getSolidMesh())

            elif isinstance(node, SceneNode) and node.getMeshData() and node.isVisible():
                layer_data = node.callDecoration("getLayerData")
                if not layer_data:
                    continue

                # Render all layers below a certain number as line mesh instead of vertices.
                if self._layerview._current_layer_num - self._layerview._solid_layers > -1 and not self._layerview._only_show_top_layers:
                    start = 0
                    end = 0
                    element_counts = layer_data.getElementCounts()
                    for layer, counts in element_counts.items():
                        if layer + self._layerview._solid_layers > self._layerview._current_layer_num:
                            break
                        end += counts

                    # This uses glDrawRangeElements internally to only draw a certain range of lines.
                    batch = RenderBatch(self._layer_shader, type = RenderBatch.RenderType.Solid, mode = RenderBatch.RenderMode.Lines, range = (start, end))
                    batch.addItem(node.getWorldTransformation(), layer_data)
                    batch.render(self._scene.getActiveCamera())

                # Create a new batch that is not range-limited
                batch = RenderBatch(self._layer_shader, type = RenderBatch.RenderType.Solid)

                if self._layerview._current_layer_mesh:
                    batch.addItem(node.getWorldTransformation(), self._layerview._current_layer_mesh)

                if self._layerview._current_layer_jumps:
                    batch.addItem(node.getWorldTransformation(), self._layerview._current_layer_jumps)

                if len(batch.items) > 0:
                    batch.render(self._scene.getActiveCamera())

        # Render toolhandles on top of the layerview
        if len(tool_handle_batch.items) > 0:
            tool_handle_batch.render(self._scene.getActiveCamera())

        self.release()
