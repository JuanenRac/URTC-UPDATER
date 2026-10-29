// =============================================================================
// URTC-COMMON - qml/CompatDialog.qml
// Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
// GPL-3.0-or-later - see LICENSE
// =============================================================================
// The compatibility matrix against what is installed. `model` is a CompatModel (compat_qt.py); the colours are properties so each program gives
// its own. Nothing here changes anything: the window only shows.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: dialog
    objectName: "compatDialog"
    property var model
    property color panelColor: "#101d30"
    property color borderColor: "#294965"
    property color textColor: "#edf7ff"
    property color mutedColor: "#91a8bd"
    property color accentColor: "#38d4e6"
    property color okColor: "#5fcf8a"
    property color warnColor: "#e0b45a"

    function stateColor(state) {
        return state === "match" ? okColor : (state === "missing" ? mutedColor : warnColor)
    }

    anchors.centerIn: parent
    modal: true
    width: Math.min(parent ? parent.width - 48 : 760, 760)
    height: Math.min(parent ? parent.height - 48 : 600, 600)
    title: model ? model.title : ""
    standardButtons: Dialog.NoButton
    onAboutToShow: if (model) model.refresh()
    background: Rectangle { color: dialog.panelColor; radius: 16; border.width: 1; border.color: dialog.borderColor }

    contentItem: ColumnLayout {
        spacing: 10
        Text {
            Layout.fillWidth: true
            text: model ? model.intro : ""
            color: dialog.mutedColor
            wrapMode: Text.WordWrap
            font.pixelSize: 12
        }
        Text {
            Layout.fillWidth: true
            visible: text !== ""
            text: model ? model.emptyText : ""
            color: dialog.warnColor
            wrapMode: Text.WordWrap
            font.pixelSize: 12
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Repeater {
                model: dialog.model ? dialog.model.headers : []
                delegate: Text {
                    required property var modelData
                    required property int index
                    Layout.preferredWidth: index === 0 ? 190 : (index === 3 ? 170 : 90)
                    Layout.fillWidth: index === 3
                    text: modelData
                    color: dialog.accentColor
                    font.bold: true
                    font.pixelSize: 12
                    elide: Text.ElideRight
                }
            }
        }
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ColumnLayout {
                width: dialog.width - 64
                spacing: 6
                Repeater {
                    model: dialog.model ? dialog.model.rows : []
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 8
                        Text { Layout.preferredWidth: 190; text: modelData.repo; color: dialog.textColor; font.pixelSize: 12; elide: Text.ElideRight }
                        Text { Layout.preferredWidth: 90; text: modelData.expected; color: dialog.textColor; font.pixelSize: 12 }
                        Text { Layout.preferredWidth: 90; text: modelData.found; color: dialog.textColor; font.pixelSize: 12 }
                        Text { Layout.preferredWidth: 170; Layout.fillWidth: true; text: modelData.stateText; color: dialog.stateColor(modelData.state); font.pixelSize: 12; wrapMode: Text.WordWrap }
                        Text { Layout.preferredWidth: 90; text: modelData.common; color: dialog.stateColor(modelData.commonState); font.pixelSize: 12 }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    Layout.topMargin: 8
                    text: model ? model.firmwareTitle : ""
                    color: dialog.accentColor
                    font.bold: true
                    font.pixelSize: 13
                }
                Repeater {
                    model: dialog.model ? dialog.model.firmwareLines : []
                    delegate: Text {
                        required property var modelData
                        Layout.fillWidth: true
                        text: modelData
                        color: dialog.textColor
                        wrapMode: Text.WordWrap
                        font.pixelSize: 12
                    }
                }
            }
        }
        Button { text: model ? model.closeText : ""; Layout.alignment: Qt.AlignRight; onClicked: dialog.close() }
    }
}
