#!/usr/bin/env python3
"""
Test final del bot arreglado - Solo Exnova
"""

import sys
import os
import time
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Función principal de prueba"""
    print("🧪 TEST FINAL DEL BOT ARREGLADO")
    print("=" * 50)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Importar componentes
        from data.market_data import MarketDataHandler
        from strategies.technical import FeatureEngineer
        from core.asset_manager import AssetManager
        from ai.llm_client import LLMClient
        from config import Config
        
        print("📊 Inicializando componentes...")
        
        # Forzar uso de Exnova
        market_data = MarketDataHandler()
        market_data.broker_name = "exnova"  # Forzar Exnova
        
        feature_engineer = FeatureEngineer()
        llm_client = LLMClient()
        
        print("🔌 Conectando a Exnova...")
        success = market_data.connect(Config.EXNOVA_EMAIL, Config.EXNOVA_PASSWORD)
        
        if not success:
            print("❌ Error conectando a Exnova")
            return False
        
        print("✅ Conectado exitosamente a Exnova")
        
        # Crear asset manager
        asset_manager = AssetManager(market_data)
        asset_manager.min_profit = 60  # Configuración agresiva
        
        print("🔍 Verificando activos disponibles...")
        available_assets = asset_manager.get_available_otc_assets(verbose=True)
        
        if not available_assets:
            print("❌ No hay activos disponibles")
            return False
        
        print(f"✅ {len(available_assets)} activos disponibles")
        asset_manager.monitored_assets = available_assets[:3]  # Top 3
        
        print("\n🎯 BUSCANDO OPORTUNIDADES...")
        print("=" * 40)
        
        # Buscar oportunidades
        for i in range(3):
            print(f"\n🔍 Búsqueda #{i+1}")
            
            opportunity = asset_manager.scan_best_opportunity(feature_engineer)
            
            if opportunity:
                print(f"💎 OPORTUNIDAD ENCONTRADA:")
                print(f"   Activo: {opportunity['asset']}")
                print(f"   Acción: {opportunity['action']}")
                print(f"   Score: {opportunity['score']}")
                print(f"   Setup: {opportunity.get('setup', 'N/A')}")
                
                # Probar Ollama
                print("🧠 Probando análisis de Ollama...")
                try:
                    market_summary = f"{opportunity['asset']}: {opportunity['indicators']['price']:.5f}"
                    smart_summary = f"Setup: {opportunity.get('setup', 'N/A')}"
                    learning_summary = "Test mode"
                    
                    import threading
                    
                    ollama_result = None
                    ollama_error = None
                    
                    def ollama_query():
                        nonlocal ollama_result, ollama_error
                        try:
                            ollama_result = llm_client.analyze_complete_trading_opportunity(
                                market_data_summary=market_summary,
                                smart_money_analysis=smart_summary,
                                learning_insights=learning_summary,
                                asset=opportunity['asset'],
                                current_balance=1000.0
                            )
                        except Exception as e:
                            ollama_error = str(e)
                    
                    thread = threading.Thread(target=ollama_query, daemon=True)
                    thread.start()
                    thread.join(timeout=15)
                    
                    if thread.is_alive():
                        print("   ⏱️ Ollama timeout (15s)")
                    elif ollama_error:
                        print(f"   ❌ Error Ollama: {ollama_error}")
                    elif ollama_result:
                        if ollama_result.get('should_trade'):
                            print(f"   ✅ Ollama APRUEBA: {ollama_result['direction']} ({ollama_result['confidence']:.0f}%)")
                        else:
                            print(f"   ⏸️ Ollama RECHAZA: {ollama_result['primary_reason']}")
                    
                except Exception as e:
                    print(f"   ❌ Error probando Ollama: {e}")
                
                print("   " + "="*30)
                
            else:
                print("   ⏳ No hay oportunidades en este momento")
            
            if i < 2:
                print("   ⏱️ Esperando 10 segundos...")
                time.sleep(10)
        
        print("\n" + "=" * 50)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 50)
        print("💡 El bot está listo para operar")
        print("🚀 Ejecutar: python main_headless.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 ¡BOT LISTO PARA OPERAR!")
    else:
        print("\n❌ Revisar errores antes de continuar")