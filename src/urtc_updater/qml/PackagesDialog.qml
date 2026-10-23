// =============================================================================
// URTC-UPDATER - qml/PackagesDialog.qml
// Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
// GPL-3.0-or-later - see LICENSE
// =============================================================================
// The Packages window: one row per program whose release carries a signed package. `model` is a PackagesModel (packages_qt.py), `tick`
// changes when the language does. Nothing here checks, downloads or installs by itself: every step is a button, and the install asks first.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: dialog
    objectName: "packagesDialog"
    property var model
    property string tick: ""
    property color panelColor: "#101d30"
    property color borderColor: "#294965"
    property color textColor: "#edf7ff"
    property color mutedColor: "#91a8bd"
    property color accentColor: "#38d4e6"
    property color errorColor: "#e07a7a"

    function tr(key) {
        var ignored = tick
        return model ? model.t(key) : ""
    }

    anchors.centerIn: parent
    modal: true
    width: Math.min(parent ? parent.width - 48 : 760, 760)
    height: Math.min(parent ? parent.height - 48 : 620, 620)
    title: tr("pkg_title")
    standardButtons: Dialog.NoButton
    background: Rectangle { color: dialog.panelColor; radius: 16; border.width: 1; border.color: dialog.borderColor }

    contentItem: ColumnLayout {
        spacing: 10
        Text {
            Layout.fillWidth: true
            text: dialog.tr("pkg_intro")
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
                spacing: 10
                Repeater {
                    model: dialog.model ? dialog.model.entries : []
                    delegate: Rectangle {
                        id: row
                        required property var modelData
                        property var entry: modelData
                        Layout.fillWidth: true
                        implicitHeight: rowColumn.implicitHeight + 24
                        radius: 12
                        color: Qt.darker(dialog.panelColor, 1.15)
                        border.width: 1
                        border.color: dialog.borderColor

                        ColumnLayout {
                            id: rowColumn
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 6
                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: row.entry.appName; color: dialog.accentColor; font.bold: true; font.pixelSize: 14 }
                                Item { Layout.fillWidth: true }
                                Text { text: dialog.tr("pkg_installed_label") + ": " + row.entry.installedText; color: dialog.textColor; font.pixelSize: 12 }
                            }
                            Text {
                                Layout.fillWidth: true
                                text: dialog.tr("pkg_kept_label") + ": " + row.entry.keptText
                                color: dialog.mutedColor
                                font.pixelSize: 11
                            }
                            Text {
                                Layout.fillWidth: true
                                text: row.entry.statusText
                                color: row.entry.isError ? dialog.errorColor : dialog.textColor
                                wrapMode: Text.WordWrap
                                font.pixelSize: 12
                                visible: text.length > 0
                            }
                            ProgressBar {
                                Layout.fillWidth: true
                                from: 0
                                to: 100
                                value: row.entry.progress
                                visible: row.entry.state === "downloading"
                            }
                            ScrollView {
                                visible: row.entry.notes.length > 0 && (row.entry.state === "available" || row.entry.state === "ready")
                                Layout.fillWidth: true
                                Layout.preferredHeight: 80
                                clip: true
                                TextArea {
                                    readOnly: true
                                    text: row.entry.notes
                                    wrapMode: Text.WordWrap
                                    color: dialog.textColor
                                    font.pixelSize: 11
                                    background: Rectangle { color: Qt.darker(dialog.panelColor, 1.3); radius: 8 }
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Button { text: dialog.tr("UPD_BTN_CHECK"); enabled: row.entry.canCheck; onClicked: row.entry.check() }
                                Button { text: dialog.tr("UPD_BTN_DOWNLOAD"); visible: row.entry.canDownload; onClicked: row.entry.download() }
                                Button {
                                    text: dialog.tr("UPD_BTN_INSTALL").replace("{version}", row.entry.version)
                                    visible: row.entry.canInstall
                                    onClicked: installConfirm.open()
                                }
                                Button { text: dialog.tr("UPD_BTN_ROLLBACK"); visible: row.entry.canRollBack; onClicked: rollbackConfirm.open() }
                                Item { Layout.fillWidth: true }
                            }
                        }

                        Dialog {
                            id: installConfirm
                            parent: Overlay.overlay
                            anchors.centerIn: parent
                            modal: true
                            width: 420
                            title: row.entry.appName
                            background: Rectangle { color: dialog.panelColor; radius: 12; border.width: 1; border.color: dialog.borderColor }
                            contentItem: Text { text: dialog.tr("UPD_CONFIRM").replace("{version}", row.entry.version); color: dialog.textColor; wrapMode: Text.WordWrap }
                            footer: DialogButtonBox {
                                Button { text: dialog.tr("UPD_BTN_CANCEL"); DialogButtonBox.buttonRole: DialogButtonBox.RejectRole }
                                Button { text: dialog.tr("UPD_BTN_YES"); DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole }
                            }
                            onAccepted: row.entry.install()
                        }

                        Dialog {
                            id: rollbackConfirm
                            parent: Overlay.overlay
                            anchors.centerIn: parent
                            modal: true
                            width: 420
                            title: row.entry.appName
                            background: Rectangle { color: dialog.panelColor; radius: 12; border.width: 1; border.color: dialog.borderColor }
                            contentItem: Text { text: dialog.tr("pkg_rollback_confirm"); color: dialog.textColor; wrapMode: Text.WordWrap }
                            footer: DialogButtonBox {
                                Button { text: dialog.tr("UPD_BTN_CANCEL"); DialogButtonBox.buttonRole: DialogButtonBox.RejectRole }
                                Button { text: dialog.tr("UPD_BTN_YES"); DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole }
                            }
                            onAccepted: row.entry.rollBack()
                        }
                    }
                }
            }
        }
        Text {
            Layout.fillWidth: true
            text: dialog.tr("pkg_safety")
            color: dialog.mutedColor
            wrapMode: Text.WordWrap
            font.pixelSize: 10
        }
        Button { text: dialog.tr("UPD_BTN_CLOSE"); Layout.alignment: Qt.AlignRight; onClicked: dialog.close() }
    }
}
