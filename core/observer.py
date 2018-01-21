"""
Log Observers for FakeDNSProxy
"""

from zope.interface import implementer

from twisted.python.compat import ioType, unicode
from twisted.logger._observer import ILogObserver
from twisted.logger._format import formatTime
from twisted.logger._format import timeFormatRFC3339
from twisted.logger._format import formatEventAsClassicLogText



@implementer(ILogObserver)
class MyLogObserver(object):
    def __init__(self, outFile, formatEvent):
        if ioType(outFile) is not unicode:
            self._encoding = "utf-8"
        else:
            self._encoding = None

        self._outFile = outFile
        self.formatEvent = formatEvent


    def __call__(self, event):
        """
        Write event to file.
        @param event: An event.
        @type event: L{dict}
        """
        # surpress those messages that come from the legacy log. These
        # are related to twisted and we don't want them. We need to provide
        # our own messages if appropriate
        if event['log_namespace'] == "log_legacy":
            return
        text = self.formatEvent(event)

        if text is None:
            text = u""

        if self._encoding is not None:
            text = text.encode(self._encoding)

        if text:
           self._outFile.write(text)
           self._outFile.flush()



def createLoggerObserver(outFile, timeFormat=timeFormatRFC3339):
    """
    Create a L{FileLogObserver} that emits text to a specified (writable)
    file-like object.
    @param outFile: A file-like object.  Ideally one should be passed which
        accepts L{unicode} data.  Otherwise, UTF-8 L{bytes} will be used.
    @type outFile: L{io.IOBase}
    @param timeFormat: The format to use when adding timestamp prefixes to
        logged events.  If L{None}, or for events with no C{"log_timestamp"}
        key, the default timestamp prefix of C{u"-"} is used.
    @type timeFormat: L{unicode} or L{None}
    @return: A file log observer.
    @rtype: L{FileLogObserver}
    """
    def formatEvent(event):
        return formatEventAsClassicLogText(
            event, formatTime=lambda e: formatTime(e, timeFormat)
        )

    return MyLogObserver(outFile, formatEvent)

