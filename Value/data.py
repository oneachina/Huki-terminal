from dataclasses import dataclass


@dataclass
class Config:
    color: str = "white"
    name: str = "Huki"
    version: float = 1.0
    # 日志记录设置
    logging_enabled: bool = True  # 默认开启日志记录
    log_file_max_size: int = 10240  # 默认日志文件最大大小为10KB
    log_file_max_age: int = 30  # 默认日志文件保留时间为30天
    log_file_max_count: int = 10  # 默认日志文件保留数量为10

