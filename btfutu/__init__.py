from .futubroker import *
from .futufeed import *
from .futustore import *
import futu as ft


def set_futu_debug_model(on_off=True):
    ft.common.set_debug_model(on_off)


set_futu_debug_model(True)
