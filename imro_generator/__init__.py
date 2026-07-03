from .core.imro_generator import ImroGenerator

try:
    from .gui.imro_config_gui import ImroConfigGUI, main
    __all__ = ['ImroGenerator', 'ImroConfigGUI', 'main']
except ImportError:
    __all__ = ['ImroGenerator']

__version__ = '0.1.0'

