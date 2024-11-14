# -*- coding: utf-8 -*-

import os

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.utils import iface
from qgis.PyQt.QtCore import pyqtSlot, pyqtSignal
from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsFeature, QgsVectorLayer, QgsField, QgsVectorDataProvider, QgsLayerTreeModel
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox
from PyQt5.QtCore import Qt
from qgis.gui import QgsMapTool

# Load the UI form
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'featuretransfer_dockwidget_base.ui'))


class FeatureTransferDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(FeatureTransferDockWidget, self).__init__(parent)
        self.setupUi(self)

        # Initialize variables
        self.selected_Copy_from_Layer = None
        self.selected_Paste_to_Layer = None

        # Set filters for the layer selectors
        self.Copy_from_Layer.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.Paste_to_Layer.setFilters(QgsMapLayerProxyModel.VectorLayer)

        # Connect signals
        self.Copy_from_Layer.layerChanged.connect(self.updateFields)
        self.Copy_from_Layer.layerChanged.connect(self.updatePasteLayer)
        self.Select_Field.currentIndexChanged.connect(self.updateFeatures)
        self.Search_String.featureChanged.connect(self.updateFeaturePicker)
        self.Search_Button.clicked.connect(self.onAccept)
        self.Copy_Feature_to_Layer_Button.clicked.connect(self.copyAndPasteFeature)
        self.Field_Selection.itemSelectionChanged.connect(self.updateCopyFeaturetoLayerButton)
        self.Copy_Checkbox.toggled.connect(self.updateCopyFeaturetoLayerButton)

        # Initially disable the OK button
        self.Copy_Feature_to_Layer_Button.setEnabled(False)

        # Set window to stay on top
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # Clear initial selection
        self.clearLayerSelection()

        # Set default Copy from Layer
        self.setDefaultLayer()

        # Connect to layer visibility changes
        QgsProject.instance().layerWillBeRemoved.connect(self.setDefaultLayer)
        QgsProject.instance().layerWasAdded.connect(self.setDefaultLayer)

        # Update Paste layer based on current selection
        self.updatePasteLayer()

    def clearLayerSelection(self):
        """Clears the selected layers."""
        self.Copy_from_Layer.setLayer(None)
        self.Paste_to_Layer.setLayer(None)

    def setDefaultLayer(self):
        """Sets the default layer to the first visible vector layer."""
        layers = QgsProject.instance().layerTreeRoot().children()
        visible_vector_layers = [layer.layer() for layer in layers if isinstance(layer.layer(), QgsVectorLayer) and layer.isVisible()]

        if not visible_vector_layers:
            self.Copy_from_Layer.setLayer(None)  # No layers are visible
        elif len(visible_vector_layers) == 1:
            self.Copy_from_Layer.setLayer(visible_vector_layers[0])  # Only one visible layer
        else:
            self.Copy_from_Layer.setLayer(visible_vector_layers[0])  # More than one visible layer, set the first one

    def updatePasteLayer(self):
        """Updates the Paste to Layer dropdown based on the selected Copy from Layer."""
        # Get all vector layers from the project
        layers = QgsProject.instance().layerTreeRoot().children()
        vector_layers = [layer.layer() for layer in layers if isinstance(layer.layer(), QgsVectorLayer)]

        # Get the layer selected in "Copy from Layer"
        selected_copy_layer = self.Copy_from_Layer.currentLayer()

        # Filter out the selected copy layer
        visible_vector_layers = [
            layer for layer in vector_layers
            if layer != selected_copy_layer and self.isLayerVisible(layer)
        ]

        # If the selected copy layer is not visible, include it in the list of visible layers
        if selected_copy_layer and not self.isLayerVisible(selected_copy_layer):
            visible_vector_layers.append(selected_copy_layer)

        # Set the first available layer in the "Paste to Layer" dropdown, or None if no layers are available
        if visible_vector_layers:
            self.Paste_to_Layer.setLayer(visible_vector_layers[0])  # Set the first available layer
        else:
            self.Paste_to_Layer.setLayer(None)  # No layers to select from

    def isLayerVisible(self, layer):
        """Check if the given layer is visible in the layer tree. """
        root = QgsProject.instance().layerTreeRoot()
        for node in root.findLayer(layer.id()).parent().children():
            if node.layer() == layer:
                return node.isVisible()
        return False

    @pyqtSlot()
    def updateFields(self):
        """Updates the fields dropdown based on the selected Copy from Layer."""
        self.Field_Selection.clear()
        self.selected_Copy_from_Layer = self.Copy_from_Layer.currentLayer()

        if self.selected_Copy_from_Layer:
            fields = self.selected_Copy_from_Layer.fields().names()
            fields = [field for field in fields if field.lower() != 'fid']
            self.Field_Selection.addItems(fields)
            self.Copy_Field_Box.setVisible(True)  # Show the Copy_Field_Box

        else:
            self.Copy_Field_Box.setVisible(False)  # Hide the Copy_Field_Box

    @pyqtSlot()
    def updateFeatures(self):
        """Updates the features picker based on the selected field."""
        self.selected_Paste_to_Layer = self.Paste_to_Layer.currentLayer()
        self.selected_Copy_from_Layer = self.Copy_from_Layer.currentLayer()
        selected_field = self.Select_Field.currentField()

        if self.selected_Copy_from_Layer:
            field_names = self.selected_Copy_from_Layer.fields().names()
            if selected_field and selected_field in field_names:
                self.Search_String.setLayer(self.selected_Copy_from_Layer)
                self.Search_String.setDisplayExpression(selected_field)

    @pyqtSlot()
    def updateFeaturePicker(self):
        """Placeholder function for updating the feature picker."""
        pass

    def onAccept(self):
        """Handles the Search button click event."""
        selected_field = self.Select_Field.currentField()
        selected_feature = self.Search_String.currentModelIndex()

        if not selected_field or not selected_feature:
            QMessageBox.warning(self, "Error", "Please select layer, field, and feature.")
            return

        if self.selected_Copy_from_Layer and selected_field and selected_feature:
            value = selected_feature.data()
            expression = f'"{selected_field}" = \'{value}\''
            self.selected_Copy_from_Layer.selectByExpression(expression)
            iface.mapCanvas().refresh()
            iface.mapCanvas().zoomToSelected(self.selected_Copy_from_Layer)

    def updateCopyFeaturetoLayerButton(self):
        """Enables or disables the Copy Feature to Layer button based on selections."""
        if self.Field_Selection.selectedItems() or self.Copy_Checkbox.isChecked():
            self.Copy_Feature_to_Layer_Button.setEnabled(True)
        else:
            self.Copy_Feature_to_Layer_Button.setEnabled(False)

    def copyAndPasteFeature(self):
        """Copies the selected feature(s) from the Copy from Layer to the Paste to Layer."""
        Paste_to_Layer = self.Paste_to_Layer.currentLayer()
        Copy_from_Layer = self.Copy_from_Layer.currentLayer()

        if not Paste_to_Layer or not Copy_from_Layer:
            QMessageBox.warning(self, "Error", "Please select both Copy and Paste layers.")
            return

        # Start editing for layers
        Paste_to_Layer.startEditing()

        # Ensure all fields from the source layer are present in the target layer
        copy_fields = Copy_from_Layer.fields()
        paste_fields = Paste_to_Layer.fields()

        # Determine which fields to use for copying
        if self.Copy_Checkbox.isChecked():
            fields_to_copy = [field for field in copy_fields.names() if field.lower() != 'fid']
        elif self.Field_Selection.selectedItems():
            fields_to_copy = [item.text() for item in self.Field_Selection.selectedItems() if item.text().lower() != 'fid']
        else:
            # If neither checkbox nor field selection is used, show a message and return
            QMessageBox.warning(self, "Error", "Please select fields or check the Copy All Fields option.")
            return

        # Add fields to paste layer if they do not exist
        for field_name in fields_to_copy:
            if field_name not in paste_fields.names():
                Paste_to_Layer.dataProvider().addAttributes([QgsField(field_name, copy_fields.field(field_name).type())])
                Paste_to_Layer.updateFields()

        # Copy selected features from source layer to target layer
        features = Copy_from_Layer.getSelectedFeatures()
        new_features = []

        for feature in features:
            new_feature = QgsFeature(Paste_to_Layer.fields())
            new_feature.setGeometry(feature.geometry())

            for field_name in fields_to_copy:
                if field_name in feature.fields().names():
                    new_feature[field_name] = feature[field_name]

            new_features.append(new_feature)

        # Append new features to the target layer
        Paste_to_Layer.dataProvider().addFeatures(new_features)
        
        # Commit changes
        Paste_to_Layer.commitChanges()
        Paste_to_Layer.triggerRepaint()

        QMessageBox.information(self, "Success", "Features copied successfully")

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()