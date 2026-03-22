"""
Orquestador Principal de Decisiones - v2
Fusiona múltiples sistemas de análisis de forma inteligente
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum
import numpy as np
from v2.config.settings import StrategyConfig
from v2.utils.logger import get_logger


logger = get_logger()


class TradeSignal(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    NO_SIGNAL = "NO_SIGNAL"


@dataclass
class AnalysisResult:
    """Resultado de un análisis individual"""
    analyzer_name: str
    signal: TradeSignal
    score: float  # 0-1
    confidence: float  # 0-1
    indicators: Dict[str, float] = None
    reasoning: str = ""
    
    def __post_init__(self):
        if self.indicators is None:
            self.indicators = {}


@dataclass
class OrchestratorDecision:
    """Decisión final del orquestador"""
    asset: str
    signal: TradeSignal
    direction: str  # "CALL" o "PUT"
    confluencia_score: float  # 0-1, porcentaje de acuerdo entre analizadores
    final_confidence: float  # 0-1, confianza en la decisión
    analysis_results: List[AnalysisResult]
    reasoning: str
    can_trade: bool  # Si es seguro operar
    
    @property
    def as_dict(self) -> dict:
        return {
            "asset": self.asset,
            "signal": self.signal.value,
            "direction": self.direction,
            "confluencia_score": self.confluencia_score,
            "confidence": self.final_confidence,
            "can_trade": self.can_trade,
            "reasoning": self.reasoning,
        }


class TradingOrchestrator:
    """Orquestador de decisiones de trading"""
    
    # Mapeo de señales a valores numéricos
    SIGNAL_SCORES = {
        TradeSignal.STRONG_BUY: 1.0,
        TradeSignal.BUY: 0.75,
        TradeSignal.NEUTRAL: 0.5,
        TradeSignal.SELL: 0.25,
        TradeSignal.STRONG_SELL: 0.0,
        TradeSignal.NO_SIGNAL: 0.5,
    }
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.history: List[OrchestratorDecision] = []
        
        # Validar que los pesos sumen aproximadamente 1.0
        total_weight = (
            config.technical_weight +
            config.smart_money_weight +
            config.ml_weight +
            config.llm_weight
        )
        
        if not (0.95 <= total_weight <= 1.05):
            logger.warning(f"Suma de pesos no es 1.0: {total_weight}. Normalizando...")
            # Normalizar
            self.config.technical_weight /= total_weight
            self.config.smart_money_weight /= total_weight
            self.config.ml_weight /= total_weight
            self.config.llm_weight /= total_weight
        
        logger.info("TradingOrchestrator inicializado")
    
    def make_decision(
        self,
        asset: str,
        technical_analysis: Optional[AnalysisResult] = None,
        smart_money_analysis: Optional[AnalysisResult] = None,
        ml_analysis: Optional[AnalysisResult] = None,
        llm_analysis: Optional[AnalysisResult] = None,
    ) -> OrchestratorDecision:
        """
        Integra múltiples análisis para tomar una decisión de trading
        
        Args:
            asset: Par de divisas a analizar
            technical_analysis: Análisis técnico
            smart_money_analysis: Análisis Smart Money
            ml_analysis: Análisis de Machine Learning
            llm_analysis: Análisis de LLM
        
        Returns:
            Decisión final del orquestador
        """
        
        # Recopilar análisis disponibles
        analyses = []
        weights = {}
        
        if technical_analysis:
            analyses.append(technical_analysis)
            weights["technical"] = self.config.technical_weight
        
        if smart_money_analysis:
            analyses.append(smart_money_analysis)
            weights["smart_money"] = self.config.smart_money_weight
        
        if ml_analysis:
            analyses.append(ml_analysis)
            weights["ml"] = self.config.ml_weight
        
        if llm_analysis:
            analyses.append(llm_analysis)
            weights["llm"] = self.config.llm_weight
        
        if not analyses:
            logger.warning(f"No hay análisis disponibles para {asset}")
            return self._create_no_signal_decision(asset, analyses)
        
        # Normalizar pesos basado en análisis disponibles
        normalized_weights = self._normalize_weights(weights)
        
        # Calcular confluencia (acuerdo entre analizadores)
        confluencia_score = self._calculate_confluencia(analyses, normalized_weights)
        
        # Calcular señal final
        final_signal = self._calculate_final_signal(analyses, normalized_weights)
        
        # Calcular confianza ponderada
        final_confidence = self._calculate_confidence(analyses, normalized_weights)
        
        # Validar confluencia mínima
        if confluencia_score < self.config.min_confluencia_score:
            logger.debug(
                f"Confluencia insuficiente para {asset}: {confluencia_score:.2%}. "
                f"Mínimo requerido: {self.config.min_confluencia_score:.2%}"
            )
            return self._create_no_signal_decision(asset, analyses, confluencia_score)
        
        # Determinar dirección (CALL o PUT)
        direction = self._determine_direction(final_signal)
        
        # Generar razonamiento
        reasoning = self._generate_reasoning(analyses, confluencia_score, final_signal)
        
        # Crear decisión
        decision = OrchestratorDecision(
            asset=asset,
            signal=final_signal,
            direction=direction,
            confluencia_score=confluencia_score,
            final_confidence=final_confidence,
            analysis_results=analyses,
            reasoning=reasoning,
            can_trade=True,
        )
        
        # Registrar en historial
        self.history.append(decision)
        
        logger.log_signal(
            asset=asset,
            signal=final_signal.value,
            strength=confluencia_score,
            indicators={
                "confluencia": confluencia_score,
                "confidence": final_confidence,
                "analyses_count": len(analyses),
            }
        )
        
        return decision
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Normaliza pesos para que sumen 1.0"""
        total = sum(weights.values())
        if total == 0:
            return weights
        return {k: v / total for k, v in weights.items()}
    
    def _calculate_confluencia(self, analyses: List[AnalysisResult], 
                               weights: Dict[str, float]) -> float:
        """
        Calcula confluencia (porcentaje de acuerdo entre analizadores)
        
        Confluencia = qué tan similares son las señales entre análisis
        """
        if not analyses:
            return 0.0
        
        # Convertir señales a scores numéricos
        signal_scores = [self.SIGNAL_SCORES[a.signal] for a in analyses]
        
        # Calcular desviación estándar (menor = más acuerdo)
        if len(signal_scores) == 1:
            return 1.0  # 100% de acuerdo si solo hay un análisis
        
        std_dev = np.std(signal_scores)
        
        # Convertir desviación a confluencia (0-1)
        # std_dev=0 (perfecto acuerdo) -> confluencia=1.0
        # std_dev=1 (máximo desacuerdo) -> confluencia~0.0
        confluencia = max(0.0, 1.0 - std_dev)
        
        return confluencia
    
    def _calculate_final_signal(self, analyses: List[AnalysisResult],
                               weights: Dict[str, float]) -> TradeSignal:
        """Calcula la señal final ponderada"""
        if not analyses:
            return TradeSignal.NO_SIGNAL
        
        # Calcular score ponderado
        weighted_score = 0.0
        total_weight = 0.0
        
        for i, analysis in enumerate(analyses):
            score = self.SIGNAL_SCORES[analysis.signal]
            # Obtener peso correspondiente
            weight = list(weights.values())[i] if i < len(weights) else 0.25
            weighted_score += score * weight * analysis.confidence
            total_weight += weight
        
        if total_weight == 0:
            return TradeSignal.NEUTRAL
        
        final_score = weighted_score / total_weight
        
        # Convertir score a señal
        if final_score >= 0.75:
            return TradeSignal.STRONG_BUY
        elif final_score >= 0.625:
            return TradeSignal.BUY
        elif final_score >= 0.375:
            return TradeSignal.NEUTRAL
        elif final_score >= 0.25:
            return TradeSignal.SELL
        else:
            return TradeSignal.STRONG_SELL
    
    def _calculate_confidence(self, analyses: List[AnalysisResult],
                             weights: Dict[str, float]) -> float:
        """Calcula confianza ponderada"""
        if not analyses:
            return 0.0
        
        weighted_confidence = 0.0
        total_weight = 0.0
        
        for i, analysis in enumerate(analyses):
            weight = list(weights.values())[i] if i < len(weights) else 0.25
            weighted_confidence += analysis.confidence * weight
            total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _determine_direction(self, signal: TradeSignal) -> str:
        """Determina si es CALL o PUT basado en la señal"""
        if signal in [TradeSignal.STRONG_BUY, TradeSignal.BUY]:
            return "CALL"
        elif signal in [TradeSignal.STRONG_SELL, TradeSignal.SELL]:
            return "PUT"
        else:
            # Para NEUTRAL, default a CALL
            return "CALL"
    
    def _generate_reasoning(self, analyses: List[AnalysisResult],
                           confluencia: float, signal: TradeSignal) -> str:
        """Genera explicación de la decisión"""
        reasons = []
        
        for analysis in analyses:
            reasons.append(f"{analysis.analyzer_name}: {analysis.signal.value} ({analysis.confidence:.1%})")
        
        reasoning = f"Confluencia: {confluencia:.1%} | Señal: {signal.value} | "
        reasoning += " | ".join(reasons)
        
        return reasoning
    
    def _create_no_signal_decision(self, asset: str, analyses: List[AnalysisResult],
                                   confluencia: float = 0.0) -> OrchestratorDecision:
        """Crea decisión de NO_SIGNAL"""
        return OrchestratorDecision(
            asset=asset,
            signal=TradeSignal.NO_SIGNAL,
            direction="CALL",
            confluencia_score=confluencia,
            final_confidence=0.0,
            analysis_results=analyses,
            reasoning="Confluencia insuficiente o no hay análisis disponibles",
            can_trade=False,
        )
    
    def get_statistics(self) -> dict:
        """Retorna estadísticas del orquestador"""
        if not self.history:
            return {
                "total_decisions": 0,
                "avg_confluencia": 0.0,
                "avg_confidence": 0.0,
                "signal_distribution": {},
            }
        
        confluencias = [d.confluencia_score for d in self.history]
        confidences = [d.final_confidence for d in self.history]
        signals = {}
        
        for decision in self.history:
            signal = decision.signal.value
            signals[signal] = signals.get(signal, 0) + 1
        
        return {
            "total_decisions": len(self.history),
            "avg_confluencia": np.mean(confluencias),
            "avg_confidence": np.mean(confidences),
            "signal_distribution": signals,
        }
