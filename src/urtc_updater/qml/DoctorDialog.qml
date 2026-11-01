// =============================================================================
// URTC-UPDATER - qml/DoctorDialog.qml
// Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
// GPL-3.0-or-later - see LICENSE
// =============================================================================
// The doctor: the tools of this computer, the adapters, the projects and the offer to bring the firmware to the Flasher. `model` is a DoctorModel
// (doctor_qt.py). The report only reads; the ports are opened only by the probe button; the firmware is copied only after the question is answered.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: dialog
    objectName: "doctorDialog"
    property var model
    property color panelColor: "#101d30"
    property color borderColor: "#294965"
    property color textColor: "#edf7ff"
    property color mutedColor: "#91a8bd"
    property color accentColor: "#38d4e6"
    property color okColor: "#5fcf8a"
    property color warnColor: "#e0b45a"
    property color failColor: "#ef7a7a"

    function stateColor(state) {
        return state === "ok" ? okColor : (state === "warn" ? warnColor : (state === "fail" ? failColor : mutedColor))
    }
    function askSync() {
        planText.text = model.syncPlanLines().join("\n")
        confirmSync.open()
    }

    anchors.centerIn: parent
    modal: true
    width: Math.min(parent ? parent.width - 48 : 820, 820)
    height: Math.min(parent ? parent.height - 48 : 640, 640)
    title: model ? model.title : ""
    standardButtons: Dialog.NoButton
    onAboutToShow: if (model) model.refresh()
    background: Rectangle { color: dialog.panelColor; radius: 16; border.width: 1; border.color: dialog.borderColor }

    Dialog {
        id: confirmSync
        objectName: "doctorConfirmSync"
        anchors.centerIn: parent
        modal: true
        width: Math.min(parent ? parent.width - 48 : 640, 640)
        title: dialog.model ? dialog.model.text("sync_now") : ""
        background: Rectangle { color: dialog.panelColor; radius: 14; border.width: 1; border.color: dialog.borderColor }
        contentItem: ColumnLayout {
            spacing: 10
            Text { Layout.fillWidth: true; text: dialog.model ? dialog.model.text("sync_confirm") : ""; color: dialog.textColor; wrapMode: Text.WordWrap; font.pixelSize: 13 }
            Text { id: planText; Layout.fillWidth: true; color: dialog.mutedColor; wrapMode: Text.WordWrap; font.pixelSize: 12 }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8
                Button { text: dialog.model ? dialog.model.text("sync_no") : ""; onClicked: { dialog.model.answerSync(false); confirmSync.close() } }
                Button { text: dialog.model ? dialog.model.text("sync_now") : ""; onClicked: { dialog.model.answerSync(true); confirmSync.close() } }
            }
        }
    }

    contentItem: ColumnLayout {
        spacing: 10
        Text {
            Layout.fillWidth: true
            text: model ? model.intro : ""
            color: dialog.mutedColor
            wrapMode: Text.WordWrap
            font.pixelSize: 12
        }
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ColumnLayout {
                width: dialog.width - 64
                spacing: 4
                Repeater {
                    model: dialog.model ? dialog.model.lines : []
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.topMargin: modelData.header ? 8 : 0
                        spacing: 8
                        Text { visible: modelData.header; Layout.fillWidth: true; text: modelData.text; color: dialog.accentColor; font.bold: true; font.pixelSize: 13 }
                        Text { visible: !modelData.header; Layout.preferredWidth: 70; text: modelData.stateText; color: dialog.stateColor(modelData.state); font.bold: true; font.pixelSize: 12 }
                        Text { visible: !modelData.header; Layout.fillWidth: true; text: modelData.text; color: dialog.textColor; wrapMode: Text.WordWrap; font.pixelSize: 12 }
                    }
                }
            }
        }
        Text { Layout.fillWidth: true; visible: text !== ""; text: model ? model.message : ""; color: dialog.warnColor; wrapMode: Text.WordWrap; font.pixelSize: 12 }
        CheckBox {
            id: syncBox
            objectName: "doctorSyncSwitch"
            text: model ? model.text("sync_switch") : ""
            checked: model ? model.syncEnabled : false
            palette.windowText: dialog.textColor
            onToggled: model.setSyncEnabled(checked)
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Button { text: model ? model.text("refresh") : ""; enabled: model && !model.running; onClicked: model.refresh() }
            Button { text: model ? model.text("probe_button") : ""; enabled: model && !model.running; onClicked: model.probe() }
            Button { text: model ? model.text("sync_now") : ""; enabled: model && model.syncCanRun; onClicked: dialog.askSync() }
            Item { Layout.fillWidth: true }
            Button { text: model ? model.text("close") : ""; onClicked: dialog.close() }
        }
    }
}
