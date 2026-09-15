"""
Visualizer module
Crea visualizzazioni dei danni rilevati
"""

import cv2
import numpy as np
from typing import List
import logging
from .damage_detector import Damage

logger = logging.getLogger(__name__)


class Visualizer:
    """Classe per la visualizzazione dei risultati"""
    
    def __init__(self, config):
        """
        Inizializza il Visualizer
        
        Args:
            config: Oggetto ConfigLoader
        """
        self.config = config
        self.damage_types = config.get_damage_types()
    
    def draw_damage_contours(self, image: np.ndarray, damages: List[Damage], 
                            thickness: int = 2) -> np.ndarray:
        """
        Disegna i contorni dei danni sull'immagine
        
        Args:
            image: Immagine di base (BGR)
            damages: Lista dei danni rilevati
            thickness: Spessore dei contorni
        
        Returns:
            Immagine con contorni disegnati
        """
        result = image.copy()
        
        for damage in damages:
            # Ottiene il colore per il tipo di danno
            color = self.config.get_damage_color(damage.damage_type)
            
            # Disegna il contorno
            cv2.drawContours(result, [damage.contour], 0, color, thickness)
            
            # Disegna il bounding box
            cv2.rectangle(result, 
                         (damage.x, damage.y),
                         (damage.x + damage.width, damage.y + damage.height),
                         color, thickness)
            
            # Aggiungi testo con il tipo di danno
            text = f"{damage.damage_type} ({damage.confidence:.2f})"
            cv2.putText(result, text,
                       (damage.x, damage.y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, color, 1)
        
        logger.info(f"Drew contours for {len(damages)} damages")
        return result
    
    def create_heatmap(self, image: np.ndarray, damages: List[Damage], 
                      sigma: float = 15) -> np.ndarray:
        """
        Crea una heatmap dei danni
        
        Args:
            image: Immagine di base
            damages: Lista dei danni rilevati
            sigma: Parametro di blur gaussiano
        
        Returns:
            Immagine heatmap
        """
        h, w = image.shape[:2]
        
        # Crea mappa di calore vuota
        heatmap = np.zeros((h, w), dtype=np.float32)
        
        # Per ogni danno, aggiungi il contributo
        for damage in damages:
            # Crea una maschera per il danno
            mask = np.zeros((h, w), dtype=np.float32)
            cv2.drawContours(mask, [damage.contour], 0, 1.0, -1)
            
            # Intensità basata sulla confidence e area normalizzata
            intensity = damage.confidence * (damage.area / (h * w))
            heatmap += mask * intensity
        
        # Applica blur gaussiano
        heatmap = cv2.GaussianBlur(heatmap, (int(sigma), int(sigma)), 0)
        
        # Normalizza a 0-255
        heatmap = (heatmap / heatmap.max() * 255).astype(np.uint8) if heatmap.max() > 0 else heatmap
        
        # Applica colormap
        heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        logger.info("Created heatmap")
        return heatmap_color
    
    def create_severity_map(self, image: np.ndarray, damages: List[Damage]) -> np.ndarray:
        """
        Crea una mappa di severità basata sulla densità dei danni
        
        Args:
            image: Immagine di base
            damages: Lista dei danni rilevati
        
        Returns:
            Immagine mappa di severità
        """
        h, w = image.shape[:2]
        severity_map = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Crea una mappa di densità
        density_map = np.zeros((h, w), dtype=np.float32)
        
        for damage in damages:
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.drawContours(mask, [damage.contour], 0, 1, -1)
            
            # Dilatazione per espandere l'area di influenza
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
            dilated_mask = cv2.dilate(mask, kernel, iterations=1).astype(np.float32)
            
            density_map += dilated_mask * damage.confidence
        
        # Normalizza
        if density_map.max() > 0:
            density_map = (density_map / density_map.max() * 255).astype(np.uint8)
        
        # Assegna colori in base alla severità
        for i in range(h):
            for j in range(w):
                val = density_map[i, j]
                if val < 85:  # Verde - basso rischio
                    severity_map[i, j] = [0, 255, 0]
                elif val < 170:  # Giallo - rischio medio
                    severity_map[i, j] = [0, 255, 255]
                else:  # Rosso - rischio alto
                    severity_map[i, j] = [0, 0, 255]
        
        # Blend con immagine originale
        result = cv2.addWeighted(image, 0.6, severity_map, 0.4, 0)
        
        logger.info("Created severity map")
        return result
    
    def create_damage_summary_image(self, image: np.ndarray, damages: List[Damage]) -> np.ndarray:
        """
        Crea un'immagine di riepilogo con statistiche
        
        Args:
            image: Immagine di base
            damages: Lista dei danni rilevati
        
        Returns:
            Immagine con riepilogo
        """
        result = image.copy()
        
        # Aggiungi background per il testo
        overlay = result.copy()
        cv2.rectangle(overlay, (10, 10), (400, 150), (255, 255, 255), -1)
        result = cv2.addWeighted(overlay, 0.3, result, 0.7, 0)
        
        # Contiamo i danni per tipo
        damage_counts = {}
        total_area = 0
        
        for damage in damages:
            damage_type = damage.damage_type
            damage_counts[damage_type] = damage_counts.get(damage_type, 0) + 1
            total_area += damage.area
        
        # Scrivi il riepilogo
        y_offset = 30
        cv2.putText(result, f"Total damages: {len(damages)}", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        y_offset += 30
        cv2.putText(result, f"Total affected area: {total_area} px", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        y_offset += 30
        for damage_type, count in damage_counts.items():
            text = f"{damage_type}: {count}"
            cv2.putText(result, text, (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            y_offset += 25
        
        logger.info("Created summary image")
        return result
    
    def create_comparison_image(self, original: np.ndarray, analyzed: np.ndarray) -> np.ndarray:
        """
        Crea un'immagine di confronto (prima/dopo)
        
        Args:
            original: Immagine originale
            analyzed: Immagine analizzata
        
        Returns:
            Immagine di confronto
        """
        h, w = original.shape[:2]
        
        # Crea immagine composita
        comparison = np.zeros((h, w * 2 + 20, 3), dtype=np.uint8)
        
        # Aggiungi originale a sinistra
        comparison[:, :w] = original
        
        # Aggiungi analizzata a destra
        comparison[:, w + 20:] = analyzed
        
        # Aggiungi separatore
        cv2.line(comparison, (w + 10, 0), (w + 10, h), (255, 255, 255), 2)
        
        # Aggiungi etichette
        cv2.putText(comparison, "Original", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(comparison, "Analyzed", (w + 30, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        logger.info("Created comparison image")
        return comparison
