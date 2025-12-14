from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.interface.data.mf4_handler import MF4Handler

AresDataInterface.register(".mf4", MF4Handler)

__all__ = ["AresDataInterface", "MF4Handler", "AresSignal"]
