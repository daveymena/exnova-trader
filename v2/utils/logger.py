"""
Sistema de logging centralizado y estructurado
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional
import json


class JSONFormatter(logging.Formatter):
    """Formatter que output logs en formato JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
            
        return json.dumps(log_data)


class TradingLogger:
    """Logger centralizado para el trading bot"""
    
    _instance: Optional["TradingLogger"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        
        self._initialized = True
        self.logger = logging.getLogger("exnova_trader")
        self.logger.setLevel(logging.DEBUG)
        
        # Limpiar handlers existentes
        self.logger.handlers.clear()
        
        # Crear directorio de logs
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        
        # Handler de archivo
        log_file = log_dir / f"trading_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Handler de consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra={"extra_data": kwargs} if kwargs else None)
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra={"extra_data": kwargs} if kwargs else None)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra={"extra_data": kwargs} if kwargs else None)
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, extra={"extra_data": kwargs} if kwargs else None)
    
    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra={"extra_data": kwargs} if kwargs else None)
    
    def log_trade(self, asset: str, direction: str, entry: float, exit: float, 
                  result: str, reason: str, confidence: float):
        """Log de operaciones de trading"""
        trade_data = {
            "asset": asset,
            "direction": direction,
            "entry": entry,
            "exit": exit,
            "result": result,
            "reason": reason,
            "confidence": confidence,
        }
        self.info(f"TRADE: {asset} {direction}", **trade_data)
    
    def log_analysis(self, asset: str, analysis_type: str, scores: dict):
        """Log de análisis"""
        analysis_data = {
            "asset": asset,
            "type": analysis_type,
            "scores": scores,
        }
        self.debug(f"ANALYSIS: {asset} - {analysis_type}", **analysis_data)
    
    def log_signal(self, asset: str, signal: str, strength: float, indicators: dict):
        """Log de señales"""
        signal_data = {
            "asset": asset,
            "signal": signal,
            "strength": strength,
            "indicators": indicators,
        }
        self.info(f"SIGNAL: {asset} - {signal}", **signal_data)


def get_logger() -> TradingLogger:
    """Obtiene la instancia singleton del logger"""
    return TradingLogger()
