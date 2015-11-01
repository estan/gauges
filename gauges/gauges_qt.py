from argparse import ArgumentParser
from argparse import ArgumentTypeError
from random import randint
from sys import argv
from functools import partial

from autobahn.twisted.wamp import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner
from autobahn.wamp.types import PublishOptions
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import qApp
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
import qt5reactor
from twisted.internet.defer import inlineCallbacks

from gauges.ui.main_window_ui import Ui_MainWindow


PREFIX = 'io.crossbar.demo.gauges'


class GaugesSessionWindow(QMainWindow, Ui_MainWindow, ApplicationSession):

    def __init__(self, config=None):
        QMainWindow.__init__(self)
        ApplicationSession.__init__(self, config)

        self.setupUi(self)

        self._channel = config.extra['channel']
        self._subscriptions_ = []
        self._controls = [
            (self.bigFellaDial, self.bigFellaSlider),
            (self.smallBuddyDial, self.smallBuddySlider),
            (self.tinyLadDial, self.tinyLadSlider),
            (self.littlePalDial, self.littlePalSlider),
        ]
        for i, (_, slider) in enumerate(self._controls):
            slider.valueChanged.connect(partial(self.changeValue, i))

        self.channelEdit.setValidator(QIntValidator(100000, 999999))
        self.channelEdit.setText(str(self._channel))

    @inlineCallbacks
    def onJoin(self, details):
        self.setEnabled(True)
        yield self.switchChannel(self._channel)

    def onLeave(self, details):
        from twisted.internet import reactor
        if reactor.threadpool is not None:
            reactor.threadpool.stop()
        qApp.quit()

    def closeEvent(self, event):
        self.leave()
        event.accept()

    def on_channelEdit_textChanged(self, text):
        backgroundFormat = 'QLineEdit {{ background-color: {}; }}'
        if self.channelEdit.hasAcceptableInput():
            self.channelEdit.setStyleSheet(backgroundFormat.format('#efe'))
            self.channelSwitchButton.setEnabled(int(text) != self._channel)
        else:
            self.channelEdit.setStyleSheet(backgroundFormat.format('#fee'))
            self.channelSwitchButton.setEnabled(False)
        self.channelCancelButton.setEnabled(int(text) != self._channel)

    @pyqtSlot()
    def on_channelCancelButton_clicked(self):
        self.channelEdit.setText(str(self._channel))

    @pyqtSlot()
    def on_channelSwitchButton_clicked(self):
        self.switchChannel(int(self.channelEdit.text()))

    @inlineCallbacks
    def switchChannel(self, channel):
        # Unsubscribe from old channel topics.
        for subscription in self._subscriptions_:
            yield subscription.unsubscribe()
        self._subscriptions_ = []

        # Subscribe to new channel topics.
        for i in range(len(self._controls)):
            handler = partial(self.updateControls, i)
            topic = self.topic(channel, i)
            subscription = yield self.subscribe(handler, topic)
            self._subscriptions_.append(subscription)

        self._channel = channel

        # Set some random initial slider values.
        for i, (_, slider) in enumerate(self._controls):
            slider.setValue(randint(0, 100))

        self.statusBar().showMessage('Subscribed to channel {} in realm {} at {}'
                                     .format(self._channel, self.config.realm,
                                             self.config.extra['url']))

    def updateControls(self, index, value):
        self.dial(index).setValue(value)
        self.slider(index).blockSignals(True)
        self.slider(index).setValue(value)
        self.slider(index).blockSignals(False)

    @inlineCallbacks
    def changeValue(self, index, value):
        yield self.publish(
            self.topic(self._channel, index), value,
            options=PublishOptions(exclude_me=False))

    def dial(self, index):
        return self._controls[index][0]

    def slider(self, index):
        return self._controls[index][1]

    @classmethod
    def topic(cls, channel, index):
        return '.'.join([PREFIX, str(channel), 'g' + str(index)])


def make(config):
    session = GaugesSessionWindow(config)
    session.show()
    return session


def parse_args():
    def channel(string):
        value = int(string)
        if value < 100000 or 999999 < value:
            raise ArgumentTypeError('must be a 6-digit integer')
        return value

    parser = ArgumentParser(description='PyQt version of Crossbar Gauges demo.')
    parser.add_argument('--url',
                        type=unicode,
                        default=u'ws://127.0.0.1:8080/ws',
                        metavar='<url>',
                        help='WAMP router URL (default: ws://127.0.0.1:8080/ws).')
    parser.add_argument('--channel',
                        type=channel,
                        default=randint(100000, 999999),
                        metavar='<channel>',
                        help='Initial 6-digit controller channel (default: random)')

    return parser.parse_args()


def main():
    args = parse_args()

    app = QApplication(argv)
    qt5reactor.install()

    runner = ApplicationRunner(args.url, u'crossbardemo', extra=vars(args))
    runner.run(make)


if __name__ == '__main__':
    main()
