"""通用工具函数"""
import sys
import json
import logging
from pathlib import Path


def get_base_dir():
    """获取基础目录（兼容 PyInstaller）"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent

def get_machine_code() -> str:
    """
    获取机器唯一标识
    
    Returns:
        str: 机器码（基于硬件信息生成的哈希）
    """
    import platform
    import hashlib
    
    # 收集硬件信息
    info = []
    
    # CPU 信息
    try:
        if platform.system() == 'Windows':
            import subprocess
            result = subprocess.check_output('wmic cpu get processorid', shell=True)
            cpu_id = result.decode().strip().split('\n')[1].strip()
            info.append(cpu_id)
        else:
            # Linux/Mac
            result = subprocess.check_output(['cat', '/proc/cpuinfo'])
            cpu_info = result.decode()
            for line in cpu_info.split('\n'):
                if 'serial' in line.lower():
                    info.append(line.split(':')[1].strip())
                    break
    except:
        info.append(platform.processor())
    
    # MAC 地址
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                       for elements in range(0,2*6,2)][::-1])
        info.append(mac)
    except:
        pass
    
    # 生成哈希
    machine_info = '|'.join(info)
    machine_code = hashlib.md5(machine_info.encode()).hexdigest()[:8].upper()
    
    return machine_code
    
def get_resource_path(relative_path: str) -> Path:
    """
    获取资源文件的绝对路径
    支持 PyInstaller 打包后的内部资源访问
    
    Args:
        relative_path: 相对路径（如 "lang/Chinese.json"）
        
    Returns:
        资源的绝对路径
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的临时目录
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境
        base_path = Path(__file__).parent.parent
    
    return base_path / relative_path


def format_file_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def load_config(config_path: str) -> dict:
    """
    加载JSON配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    try:
        path = Path(config_path)
        if not path.exists():
            print(f"Warning: Config file not found: {config_path}")
            return {}
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def setup_logger(name: str, log_file: str, level: str = "INFO") -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 创建日志目录
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # 添加处理器
    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger


def normalize_lot_size(volume: float, min_lot: float = 0.01, max_lot: float = 100.0, step: float = 0.01) -> float:
    """
    标准化手数

    Args:
        volume: 原始手数
        min_lot: 最小手数
        max_lot: 最大手数
        step: 手数步长

    Returns:
        标准化后的手数
    """
    # 限制在最小和最大范围内
    volume = max(min_lot, min(max_lot, volume))
    
    # 按照步长标准化
    volume = round(volume / step) * step
    
    return round(volume, 2)