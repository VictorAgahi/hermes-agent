import sys
from . import common
from .common import v1 as common_v1
from .common.v1 import event_pb2

sys.modules["common"] = common
sys.modules["common.v1"] = common_v1
sys.modules["common.v1.event_pb2"] = event_pb2

