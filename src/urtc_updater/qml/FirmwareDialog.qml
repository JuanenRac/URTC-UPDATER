// =============================================================================
// URTC-UPDATER - qml/FirmwareDialog.qml
// Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
// GPL-3.0-or-later - see LICENSE
// =============================================================================
// Checks the release signature of a firmware image and opens the Flasher with it selected. Nothing is written to a board here.
import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Dialog {
    id: dialog
    objectName: "firmwareDialog"
    property var bridge
    property var tick: 0
    property color panelColor: "#101d30"
    property color borderColor: "#294965"
    property color textColor: "#edf7ff"
    property color mutedColor: "#91a8bd"
    property color accentColor: "#38d4e6"
    property string answer: ""
    function tr(key) { tick; return bridge ? bridge.text(key) : key }

    anchors.centerIn: parent
    modal: true
    width: Math.min(parent ? parent.width - 48 : 700, 700)
    title: tr("fw_title")
    standardButtons: Dialog.NoButton
    onAboutToShow: answer = ""
    background: Rectangle { color: dialog.panelColor; radius: 16; border.width: 1; border.color: dialog.borderColor }

    FileDialog {
        id: imageChooser
        title: dialog.tr("fw_path_label")
        nameFilters: ["*.bin"]
        onAccepted: { pathField.text = bridge.firmwareLocalPath(selectedFile.toString()); dialog.answer = "" }
    }

    contentItem: ColumnLayout {
        spacing: 10
        Text { Layout.fillWidth: true; text: dialog.tr("fw_intro"); color: dialog.mutedColor; wrapMode: Text.WordWrap; font.pixelSize: 12 }
        Text { text: dialog.tr("fw_path_label"); color: dialog.textColor; font.pixelSize: 12 }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            TextField { id: pathField; objectName: "firmwarePath"; Layout.fillWidth: true; selectByMouse: true; onTextEdited: dialog.answer = "" }
            Button { text: dialog.tr("fw_choose"); onClicked: imageChooser.open() }
        }
        Text {
            objectName: "firmwareAnswer"
            Layout.fillWidth: true
            visible: text.length > 0
            text: dialog.answer
            color: dialog.textColor
            wrapMode: Text.WordWrap
            font.pixelSize: 12
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Button { objectName: "firmwareCheck"; text: dialog.tr("fw_check"); enabled: pathField.text.trim().length > 0; onClicked: dialog.answer = bridge.firmwareCheck(pathField.text) }
            Button { objectName: "firmwareOpen"; text: dialog.tr("fw_open"); enabled: pathField.text.trim().length > 0; onClicked: dialog.answer = bridge.firmwareOpen(pathField.text) }
            Item { Layout.fillWidth: true }
            Button { text: dialog.tr("about_close_button"); onClicked: dialog.close() }
        }
    }
}
