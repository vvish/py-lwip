"""The observer for the ethernet bus that records transmitted frames."""


class EthernetRecorder(object):
    """Class records the data blocks transmitted on the bus."""

    recorded_frames = []

    def __call__(self, netif, frame_to_record, was_forwarded):
        """
        Record transmitted frame.

        Parameters
        ----------
        netif : NetIf
            sending interface
        frame_to_record : bytearray
            frame bytes
        was_forwarded : boolean
            indicated if the data was forwarded or filtered out
        """
        self.recorded_frames.append(frame_to_record)