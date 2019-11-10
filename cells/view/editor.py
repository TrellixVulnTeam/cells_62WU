from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QFrame, QHBoxLayout, QMessageBox, QScrollArea,
                               QWidget)

from cells import events
from cells.model import TrackTemplateModel
from cells.observation import Observation

from .code import CodeView
from .dialogs import ConfirmationDialog
from .track import Track
from .track_editor import TrackEditor


class Editor(Observation, QScrollArea):
    def __init__(self, subject):
        Observation.__init__(self, subject)
        QScrollArea.__init__(self)

        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumSize(200, 300)

        self.codeView = CodeView(subject)
        self.trackEditor = TrackEditor(self.subject)

        self.selectedTrackIndex = -1

        self.innerLayout = QHBoxLayout()

        self.innerLayout.setSpacing(0)
        self.innerLayout.setContentsMargins(0, 0, 0, 0)
        self.innerLayout.setAlignment(Qt.AlignLeft)

        widget = QWidget()
        widget.setLayout(self.innerLayout)
        self.setWidget(widget)
        self.setWidgetResizable(True)

        self.add_responder(events.document.Open, self.documentOpenResponder)
        self.add_responder(events.view.main.TrackNew, self.trackNewResponder)
        self.add_responder(events.view.browser.TrackNewFromTemplate,
                           self.trackNewFromTemplateResponder)
        self.add_responder(events.view.track.Clicked,
                           self.trackClickedResponder)
        self.add_responder(events.view.main.TrackSelectLeft,
                           self.trackSelectLeftResponder)
        self.add_responder(events.view.main.TrackSelectRight,
                           self.trackSelectRightResponder)
        self.add_responder(events.view.main.TrackMoveLeft,
                           self.trackMoveLeftResponder)
        self.add_responder(events.view.main.TrackMoveRight,
                           self.trackMoveRightResponder)
        self.add_responder(events.view.main.TrackRemove,
                           self.trackRemoveResponder)
        self.add_responder(events.view.main.RowRemove, self.rowRemoveResponder)
        self.add_responder(events.view.track.CellSelected,
                           self.cellSelectedResponder)
        self.add_responder(events.view.main.CellEvaluate,
                           self.cellEvaluateResponder)
        self.add_responder(events.view.main.CellClear, self.cellClearResponder)
        self.add_responder(events.view.main.CellEdit, self.cellEditResponder)
        self.add_responder(events.view.main.TrackSetup,
                           self.trackSetupResponder)
        self.add_responder(events.view.main.TrackSaveAsTemplate,
                           self.trackSaveAsTemplateResponder)
        self.add_responder(events.track.TrackTemplateSaved,
                           self.trackTemplateSavedResponder)
        self.add_responder(events.view.main.TrackRestartInterpreter,
                           self.trackRestartInterpreterResponder)

    def documentOpenResponder(self, e):
        self.clear()

        for (n, track) in enumerate(e.document.tracks):
            trackView = Track(self, self.subject, n, track.name,
                              track.template)
            trackView.deserialize(track)
            self.innerLayout.addWidget(trackView)

    def trackClickedResponder(self, e):
        self.selectTrackAt(e.index)

    def trackSelectLeftResponder(self, e):
        if self.numOfTracks() < 1:
            return

        if not self.hasSelectedTrack():
            self.selectTrackAt(self.numOfTracks() - 1)
        else:
            self.selectTrackAt(self.selectedTrackIndex - 1)

    def trackSelectRightResponder(self, e):
        if self.numOfTracks() < 1:
            return

        if not self.hasSelectedTrack():
            self.selectTrackAt(0)
        else:
            self.selectTrackAt(self.selectedTrackIndex + 1)

    def trackNewResponder(self, e):
        self.newTrack(TrackTemplateModel())

    def trackNewFromTemplateResponder(self, e):
        self.newTrack(e.template)

    def trackMoveLeftResponder(self, e):
        self.moveSelectedTrackTo(self.selectedTrackIndex - 1)

    def trackMoveRightResponder(self, e):
        self.moveSelectedTrackTo(self.selectedTrackIndex + 1)

    def moveSelectedTrackTo(self, index):
        if self.numOfTracks() < 2 or \
                not self.hasSelectedTrack() or \
                not index in range(self.numOfTracks()) or \
                self.selectedTrackIndex == index:

            return

        track = self.innerLayout.takeAt(self.selectedTrackIndex)
        self.innerLayout.insertWidget(index, track.widget())
        track.widget().setIndex(index)

        previous = self.trackAt(self.selectedTrackIndex)
        previous.setIndex(self.selectedTrackIndex)

        self.notify(events.view.track.Move(self.selectedTrackIndex, index))

        self.selectTrackAt(index)

    def trackRemoveResponder(self, e):
        if not self.hasSelectedTrack():
            return

        track = self.trackAt(self.selectedTrackIndex)
        question = f'Do you really want to delete track {track.name()}?'
        confirmation = ConfirmationDialog("Delete Track", question)

        if confirmation.exec_() == ConfirmationDialog.No:
            return

        self.notify(
            events.view.track.Remove(self.selectedTrackIndex, track.template))
        track.delete()
        self.selectTrackAt(self.selectedTrackIndex - 1)

        for n in range(self.selectedTrackIndex + 1, self.numOfTracks()):
            track = self.trackAt(n)
            track.setIndex(track.index - 1)

    def rowRemoveResponder(self, e):
        if not self.hasSelectedTrack():
            return

        track = self.trackAt(self.selectedTrackIndex)

        if not track.hasSelectedCell() or len(track.cells) < 1:
            return

        confirmation = ConfirmationDialog(
            "Delete Row", "Do you really want to delete selected row?")

        if confirmation.exec_() == ConfirmationDialog.No:
            return

        self.notify(events.view.track.RowRemove(track.selectedCellIndex))

    def cellSelectedResponder(self, e):
        self.ensureTrackVisible(self.selectedTrackIndex)

    def cellEvaluateResponder(self, e):
        if not self.hasSelectedTrack():
            return

        track = self.trackAt(self.selectedTrackIndex)

        if not track.hasSelectedCell():
            return

        track.cells[track.selectedCellIndex].evaluate()

    def cellClearResponder(self, e):
        if not self.hasSelectedTrack():
            return

        track = self.trackAt(self.selectedTrackIndex)

        if not track.hasSelectedCell():
            return

        track.cells[track.selectedCellIndex].clear()

    def cellEditResponder(self, e):
        if not self.hasSelectedTrack():
            return

        track = self.trackAt(self.selectedTrackIndex)

        if not track.hasSelectedCell():
            return

        track.cells[track.selectedCellIndex].edit()

    def trackSetupResponder(self, e):
        if not self.hasSelectedTrack():
            return

        track = self.trackAt(self.selectedTrackIndex)
        track.edit()

    def trackSaveAsTemplateResponder(self, e):
        if not self.hasSelectedTrack():
            return

        self.trackAt(self.selectedTrackIndex).saveAsTemplate()

    def trackTemplateSavedResponder(self, e):
        msgBox = QMessageBox()
        msgBox.setText("Track Template Saved Succesfully")
        msgBox.setDetailedText(repr(e.template))
        msgBox.exec()

    def trackRestartInterpreterResponder(self, e):
        # TODO

        if not self.hasSelectedTrack():
            return

        track = self.trackAt(self.selectedTrackIndex)

    def newTrack(self, template):
        length = self.innerLayout.count()
        name = "Track " + str(length + 1)
        track = Track(self, self.subject, length, name, template)
        self.innerLayout.addWidget(track)
        self.notify(events.view.track.New(name, template))

        if self.numOfTracks() > 1:
            firstTrack = self.trackAt(0)
            [track.addCell() for _ in firstTrack.cells]
            track.selectCellAt(firstTrack.selectedCellIndex)
            not firstTrack.isPasteBufferEmpty() and track.fillPasteBuffer()

    def selectTrackAt(self, index):
        if self.selectedTrackIndex == index:
            return

        if self.hasSelectedTrack():
            track = self.trackAt(self.selectedTrackIndex)
            track.setSelected(False)

        if index in range(self.numOfTracks()):
            track = self.trackAt(index)
            track.setSelected(True)
            self.ensureTrackVisible(index)

        self.selectedTrackIndex = min(max(-1, index), self.numOfTracks())
        self.notify(events.view.track.Select(self.selectedTrackIndex))

    def ensureTrackVisible(self, index):
        if index not in range(self.numOfTracks()):
            return

        track = self.trackAt(index)

        if track.selectedCellIndex in range(len(track.cells)):
            cell = track.cells[track.selectedCellIndex]
            self.ensureWidgetVisible(cell, track.header.width(),
                                     track.header.height())
        else:
            self.ensureWidgetVisible(track, track.header.width(),
                                     track.header.height())

    def hasSelectedTrack(self):
        return self.selectedTrackIndex in range(self.numOfTracks())

    def numOfTracks(self):
        return self.innerLayout.count()

    def clear(self):
        for i in reversed(range(self.numOfTracks())):
            self.trackAt(i).setParent(None)

    def trackAt(self, index):
        return self.innerLayout.itemAt(index).widget()

    def closeEvent(self, e):
        self.codeView.delete()
        self.trackEditor.delete()
        self.unregister()

        return super().closeEvent(e)
