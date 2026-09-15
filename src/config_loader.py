"""
Configuration loader module
Carica e gestisce i parametri di configurazione del progetto
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Classe per caricare e gestire la configurazione del progetto"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Inizializza il ConfigLoader
        
        Args:
            config_path: Percorso al file di configurazione YAML
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._create_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Carica il file di configurazione YAML
        
        Returns:
            Dizionario con i parametri di configurazione
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _create_directories(self):
        """Crea le directory necessarie se non esistono"""
        paths = self.config.get('paths', {})
        
        for key, path in paths.items():
            if isinstance(path, str) and not path.endswith('.db'):
                Path(path).mkdir(parents=True, exist_ok=True)
        
        # Crea anche directory logs
        Path('logs').mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Ottiene un valore di configurazione
        
        Args:
            key: Chiave di configurazione (supporta notazione punto: 'paths.input_images')
            default: Valore di default se la chiave non esiste
        
        Returns:
            Il valore di configurazione richiesto
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def get_all(self) -> Dict[str, Any]:
        """Ritorna l'intera configurazione"""
        return self.config
    
    def get_damage_types(self) -> Dict[str, Dict[str, Any]]:
        """Ritorna i tipi di danno configurati"""
        return self.config.get('damage_detection', {}).get('damage_types', {})
    
    def get_damage_color(self, damage_type: str) -> tuple:
        """
        Ottiene il colore BGR per un tipo di danno
        
        Args:
            damage_type: Tipo di danno
        
        Returns:
            Tupla (B, G, R) per il colore
        """
        damage_types = self.get_damage_types()
        if damage_type in damage_types:
            return tuple(damage_types[damage_type]['color'])
        return (128, 128, 128)  # Grigio di default


# Istanza globale di configurazione
config = ConfigLoader()
