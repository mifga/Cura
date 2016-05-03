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
    activateEnabled: false
    addEnabled: false
    removeEnabled: false
    renameEnabled: false

    scrollviewCaption: " "
    detailsVisible: true

    property string currency: UM.Preferences.getValue("general/currency")

    Item {
        UM.I18nCatalog { id: catalog; name: "cura"; }

        visible: base.currentItem != null
        anchors.fill: parent

        Label { id: profileName; text: base.currentItem ? base.currentItem.name : ""; font: UM.Theme.getFont("large"); width: parent.width; }

        TabView {
            id: scrollView
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: profileName.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.bottom: parent.bottom

            Tab {
                title: "Information"
                anchors.margins: UM.Theme.getSize("default_margin").height

                Column {
                    spacing: UM.Theme.getSize("default_margin").height

                    Grid {
                        id: containerGrid
                        columns: 2
                        spacing: UM.Theme.getSize("default_margin").width

                        Column {
                            Label { text: catalog.i18nc("@label", "Profile Type") }
                            Label { text: catalog.i18nc("@label", "Supplier") }
                            Label { text: catalog.i18nc("@label", "Material Type") }
                            Label { text: catalog.i18nc("@label", "Color") }
                        }
                        Column {
                            Label { text: base.currentItem && base.currentItem.profileType ? base.currentItem.profileType : ""}
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
                            Label { text: "<b>" + catalog.i18nc("@label", "Properties") + "</b>" }
                            Label { text: catalog.i18nc("@label", "Density") }
                            Label { text: catalog.i18nc("@label", "Diameter") }
                            Label { text: catalog.i18nc("@label", "Filament cost") }
                            Label { text: catalog.i18nc("@label", "Filament weight") }
                            Label { text: catalog.i18nc("@label", "Filament length") }
                            Label { text: catalog.i18nc("@label", "Cost per meter") }
                        }
                        Column {
                            Label { text: " " }
                            Label { text: base.currentItem && base.currentItem.density ? base.currentItem.density + " " + "kg/m3" : "" }
                            Label { text: base.currentItem && base.currentItem.diameter ? base.currentItem.diameter + " " + "mm" : ""}
                            Label { text: base.currentItem && base.currentItem.spoolCost ? base.currency + " " + base.currentItem.spoolCost : "" }
                            Label { text: base.currentItem && base.currentItem.spoolWeight ? base.currentItem.spoolWeight + " " + "kg" : "" }
                            Label { text: base.currentItem && base.currentItem.spoolLength ? catalog.i18nc("@label", "approx.") + " " + base.currentItem.spoolLength + " " + "m" : "" }
                            Label { text: base.currentItem && base.currentItem.lenghtCost ? catalog.i18nc("@label", "approx.") + " " + base.currency + " " + base.currentItem.lenghtCost + "/m" : "" }
                        }
                    }
                    Label {
                        text: base.currentItem && base.currentItem.infoGeneral ? "<b>" + catalog.i18nc("@label", "Information") + "</b><br>" + base.currentItem.infoGeneral : ""
                        width: scrollView.width - 2 * UM.Theme.getSize("default_margin").width
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        text: base.currentItem && base.currentItem.infoAdhesion ? "<b>" + catalog.i18nc("@label", "Adhesion") + "</b><br>" + base.currentItem.infoAdhesion : ""
                        width: scrollView.width - 2 * UM.Theme.getSize("default_margin").width
                        wrapMode: Text.WordWrap
                    }
                }
            }
            Tab {
                title: catalog.i18nc("@label", "Print settings")
                anchors.margins: UM.Theme.getSize("default_margin").height

                Grid {
                    columns: 2
                    spacing: UM.Theme.getSize("default_margin").width

                    Column {
                        Repeater {
                            model: base.currentItem ? base.currentItem.settings : null
                            Label {
                                text: modelData.name.toString();
                                elide: Text.ElideMiddle;
                            }
                        }
                    }
                    Column {
                        Repeater {
                            model: base.currentItem ? base.currentItem.settings : null
                            Label { text: modelData.value.toString() + " " + modelData.unit.toString(); }
                        }
                    }
                }
            }
        }
    }
}