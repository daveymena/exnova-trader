"""
Configuración centralizada del Trading Bot v2
Valida y centraliza todas las configuraciones del sistema
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()


class AccountType(Enum):
    PRACTICE = "PRACTICE"
    REAL = "REAL"


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class BrokerConfig:
    """Configuración del broker Exnova"""
    email: str
    password: str
    account_type: AccountType = AccountType.PRACTICE
    api_url: str = "https://www.exnova.com"
    
    def __post_init__(self):
        if not self.email or not self.password:
            raise ValueError("Email y password de Exnova son requeridos")
        if self.account_type not in AccountType:
            raise ValueError(f"Tipo de cuenta inválido: {self.account_type}")


@dataclass
class TradingConfig:
    """Configuración de parámetros de trading"""
    # Capital y riesgo
    capital_per_trade: float = 1.0
    max_daily_loss: float = 50.0
    max_daily_trades: int = 20
    max_consecutive_losses: int = 3
    
    # Martingala - MEJORADO: controlado y limitado
    use_martingale: bool = False
    martingale_multiplier: float = 2.0  # 2x, máximo
    martingale_max_steps: int = 2  # Máximo 2 aumentos: 1 -> 2 -> 4
    
    # Temporalidad
    expiration_seconds: int = 300  # 5 minutos
    min_trade_interval: float = 10.0  # 10 segundos entre trades
    
    # Horarios de operación
    trading_hours: tuple = (7, 23)  # 7:00 AM - 11:00 PM
    min_hourly_trades: int = 0
    max_hourly_trades: int = 5
    
    # Posiciones
    max_simultaneous_positions: int = 3  # Máximo 3 posiciones simultáneas
    
    # Indicadores técnicos
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    bb_period: int = 20
    bb_std_dev: float = 2.0
    
    sma_short: int = 20
    sma_long: int = 50
    
    atr_period: int = 14
    atr_threshold: float = 0.0005  # Volatilidad mínima
    
    def validate(self):
        """Valida la configuración"""
        if self.capital_per_trade <= 0:
            raise ValueError("capital_per_trade debe ser positivo")
        if self.max_daily_loss <= 0:
            raise ValueError("max_daily_loss debe ser positivo")
        if self.max_consecutive_losses <= 0:
            raise ValueError("max_consecutive_losses debe ser positivo")
        if self.martingale_multiplier < 1.5:
            raise ValueError("martingale_multiplier debe ser >= 1.5")
        if self.martingale_max_steps > 3:
            raise ValueError("martingale_max_steps no puede exceder 3")
        if self.max_simultaneous_positions < 1:
            raise ValueError("max_simultaneous_positions debe ser >= 1")
        if self.max_simultaneous_positions > 10:
            raise ValueError("max_simultaneous_positions no puede exceder 10")
        if self.expiration_seconds < 60 or self.expiration_seconds > 3600:
            raise ValueError("expiration_seconds debe estar entre 60 y 3600")


@dataclass
class LLMConfig:
    """Configuración de modelos LLM"""
    provider: str = "groq"  # "groq" o "ollama"
    groq_api_key: Optional[str] = None
    ollama_url: str = "http://localhost:11434"
    model_name: str = "mixtral-8x7b-32768"
    timeout: int = 10
    use_llm: bool = False
    
    def validate(self):
        if self.use_llm and self.provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY requerida si use_llm=True")


@dataclass
class LoggingConfig:
    """Configuración de logging"""
    level: LogLevel = LogLevel.INFO
    log_dir: str = "./logs"
    log_file: str = "trading_bot.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    console_output: bool = True
    detailed_trades: bool = True


@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    db_type: str = "sqlite"  # "sqlite" o "postgresql"
    db_path: str = "./data/trading_bot.db"
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "trading_bot"
    postgres_password: str = ""
    postgres_db: str = "trading_bot"


@dataclass
class StrategyConfig:
    """Configuración de estrategias de análisis"""
    # Pesos de confluencia (deben sumar ~1.0)
    technical_weight: float = 0.25
    smart_money_weight: float = 0.25
    ml_weight: float = 0.25
    llm_weight: float = 0.25
    
    # Umbrales de confluencia
    min_confluencia_score: float = 0.65  # Mínimo 65% de confluencia
    
    # Análisis
    use_smart_money: bool = True
    use_pattern_detection: bool = True
    use_regime_detection: bool = True
    use_volatility_filter: bool = True


@dataclass
class Settings:
    """Configuración principal del sistema"""
    # Configuraciones
    broker: BrokerConfig
    trading: TradingConfig
    llm: LLMConfig
    logging: LoggingConfig
    database: DatabaseConfig
    strategy: StrategyConfig
    
    # Metadata
    version: str = "2.0.0"
    environment: str = "development"
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Crea Settings desde variables de entorno"""
        # Broker
        broker = BrokerConfig(
            email=os.getenv("EXNOVA_EMAIL", ""),
            password=os.getenv("EXNOVA_PASSWORD", ""),
            account_type=AccountType[os.getenv("ACCOUNT_TYPE", "PRACTICE")],
        )
        
        # Trading
        trading = TradingConfig(
            capital_per_trade=float(os.getenv("CAPITAL_PER_TRADE", 1.0)),
            use_martingale=os.getenv("USE_MARTINGALE", "False").lower() == "true",
            martingale_multiplier=float(os.getenv("MARTINGALE_MULTIPLIER", 2.0)),
            martingale_max_steps=int(os.getenv("MARTINGALE_MAX_STEPS", 2)),
            max_consecutive_losses=int(os.getenv("MAX_CONSECUTIVE_LOSSES", 3)),
        )
        
        # LLM
        llm = LLMConfig(
            use_llm=os.getenv("USE_LLM", "False").lower() == "true",
            groq_api_key=os.getenv("GROQ_API_KEY"),
            provider=os.getenv("LLM_PROVIDER", "groq"),
        )
        
        # Logging
        logging_cfg = LoggingConfig(
            level=LogLevel[os.getenv("LOG_LEVEL", "INFO")],
            console_output=os.getenv("CONSOLE_OUTPUT", "True").lower() == "true",
        )
        
        # Database
        database = DatabaseConfig(
            db_type=os.getenv("DB_TYPE", "sqlite"),
            db_path=os.getenv("DB_PATH", "./data/trading_bot.db"),
        )
        
        # Strategy
        strategy = StrategyConfig(
            min_confluencia_score=float(os.getenv("MIN_CONFLUENCIA_SCORE", 0.65)),
        )
        
        # Crear Settings
        settings = cls(
            broker=broker,
            trading=trading,
            llm=llm,
            logging=logging_cfg,
            database=database,
            strategy=strategy,
        )
        
        # Validar
        settings.validate()
        
        return settings
    
    def validate(self):
        """Valida todas las configuraciones"""
        self.broker.__post_init__()
        self.trading.validate()
        self.llm.validate()
        
        if self.strategy.technical_weight < 0:
            raise ValueError("technical_weight debe ser positivo")
        if self.strategy.min_confluencia_score < 0.5 or self.strategy.min_confluencia_score > 1.0:
            raise ValueError("min_confluencia_score debe estar entre 0.5 y 1.0")
