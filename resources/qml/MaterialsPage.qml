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

                Label { text: catalog.i18nc("@label", "Material Type"); width: 155 }
                Label { text: base.currentItem && base.currentItem.group ? base.currentItem.group : "" }

                Label { text: catalog.i18nc("@label", "Supplier"); }
                Label { text: base.currentItem && base.currentItem.supplier ? base.currentItem.supplier : "" }

                Label { text: catalog.i18nc("@label", "Color"); }
                Label { text: base.currentItem && base.currentItem.variant ? base.currentItem.variant : "" }
            }
        }
    }
}