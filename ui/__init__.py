# ui/__init__.py
from .dashboard import DashboardTab
from .master_config import MasterConfigTab
from .slave_config import SlaveConfigTab
from .monitoring import MonitoringTab
from .logs import LogsTab

__all__ = [
    'DashboardTab',
    'MasterConfigTab', 
    'SlaveConfigTab',
    'MonitoringTab',
    'LogsTab'
]
