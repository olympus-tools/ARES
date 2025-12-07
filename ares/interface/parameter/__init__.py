from ares.interface.parameter.ares_param_interface import AresParamInterface
from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.dcm_handler import DCMHandler
from ares.interface.parameter.jsonparam_handler import JSONParamHandler

AresParamInterface.register(".dcm", DCMHandler)
AresParamInterface.register(".json", JSONParamHandler)

__all__ = ["AresParamInterface", "DCMHandler", "JSONParamHandler", "AresParameter"]
