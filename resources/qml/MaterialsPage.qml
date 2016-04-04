// Copyright (c) 2016 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2

import UM 1.1 as UM

UM.ManagementPage
{
    id: base;

    title: catalog.i18nc("@title:tab", "Materials");

    model: UM.MaterialsModel { }
/*
    onAddObject: { var selectedMaterial = UM.MaterialManager.createProfile(); base.selectMaterial(selectedMaterial); }
    onRemoveObject: confirmDialog.open();
    onRenameObject: { renameDialog.open(); renameDialog.selectText(); }
*/
    addEnabled: false
    removeEnabled: false;
    renameEnabled: false;

    scrollviewCaption: catalog.i18nc("@label","Supplier:")
    detailsVisible: true

    Item {
        UM.I18nCatalog { id: catalog; name: "cura"; }

        visible: base.currentItem != null
        anchors.fill: parent

        Label { id: profileName; text: base.currentItem ? base.currentItem.name : ""; font: UM.Theme.getFont("large"); width: parent.width; }

        ScrollView {
            anchors.left: parent.left
            anchors.top: profileName.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.right: parent.right
            anchors.bottom: parent.bottom

            Grid {
                id: containerGrid
                columns: 2
                spacing: UM.Theme.getSize("default_margin").width

                Column {
                    Label { text: catalog.i18nc("@label", "Supplier") }
                    Label { text: catalog.i18nc("@label", "Material Type") }
                    Label { text: catalog.i18nc("@label", "Color") }
                }
                Column {
                    Label { text: base.currentItem && base.currentItem.supplier ? base.currentItem.supplier : ""}
                    Label { text: base.currentItem && base.currentItem.group ? base.currentItem.group : "" }
                    Column {
                        Label { text: base.currentItem && base.currentItem.variant ? base.currentItem.variant : "" }
                        Row {
                            spacing: UM.Theme.getSize("default_margin").width/2
                            Rectangle {
                                color: base.currentItem && base.currentItem.colorDisplay ? base.currentItem.colorDisplay : "yellow"
                                width: colorLabel.height
                                height: colorLabel.height
                                border.width: UM.Theme.getSize("default_lining").height
                            }
                            Label { id: colorLabel; text: base.currentItem && base.currentItem.colorRAL ? base.currentItem.colorRAL : "" }
                        }
                    }
                }
                Column {
                    Label { text: catalog.i18nc("@label", "Density") }
                    Label { text: catalog.i18nc("@label", "Diameter") }
                    Label { text: catalog.i18nc("@label", "Spool cost") }
                    Label { text: catalog.i18nc("@label", "Spool weight") }
                    Label { text: catalog.i18nc("@label", "Spool lenght") }
                    Label { text: catalog.i18nc("@label", "Cost per meter") }
                }
                Column {
                    Label { text: base.currentItem && base.currentItem.density ? base.currentItem.density : "" }
                    Label { text: base.currentItem && base.currentItem.diameter ? base.currentItem.diameter : ""}
                    Label { text: base.currentItem && base.currentItem.spoolCost ? base.currentItem.spoolCost : "" }
                    Label { text: base.currentItem && base.currentItem.spoolWeight ? base.currentItem.spoolWeight : "" }
                    Label { text: {
                        if (base.currentItem && base.currentItem.density && base.currentItem.diameter && base.currentItem.spoolWeight) {
                            var volume = parseFloat(base.currentItem.spoolWeight) / parseFloat(base.currentItem.density);
                            var surface = Math.PI * Math.pow(parseFloat(base.currentItem.diameter) / 2, 2);
                            var length = Math.round(1000 * volume/surface).toString();
                            return length;
                        } else return "";
                    }}
                    Label { text: {
                        if (base.currentItem && base.currentItem.density && base.currentItem.diameter && base.currentItem.spoolWeight && base.currentItem.spoolCost) {
                            var volume = parseFloat(base.currentItem.spoolWeight) / parseFloat(base.currentItem.density);
                            var surface = Math.PI * Math.pow(parseFloat(base.currentItem.diameter) / 2, 2);
                            var cost = (parseFloat(base.currentItem.spoolCost) / (1000 * volume/surface)).toString().substring(0,5);
                            return cost;
                        } else return "";
                    }}
                }
                Button {
                    visible: base.currentItem && base.currentItem.linkOrder
                    text: catalog.i18nc("@label", "Order")
                    onClicked: {
                        Qt.openUrlExternally(base.currentItem.linkOrder)
                    }
                }
            }
        }
    }
}