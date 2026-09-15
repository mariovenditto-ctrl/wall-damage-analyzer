"""
Damage Detector module
Rileva e classifica i danni sulle pareti
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Damage:
    """Classe per rappresentare un danno rilevato"""
    damage_type: str
    x: int
    y: int
    width: int
    height: int
    area: int
    confidence: float
    contour: np.ndarray
    
    def to_dict(self) -> Dict:
        """Converte a dizionario"""
        return {
            'type': self.damage_type,
            'x': int(self.x),
            'y': int(self.y),
            'width': int(self.width),
            'height': int(self.height),
            'area': int(self.area),
            'confidence': float(self.confidence),
            'center_x': int(self.x + self.width / 2),
            'center_y': int(self.y + self.height / 2)
        }


class DamageDetector:
    """Classe per la rilevazione dei danni"""
    
    def __init__(self, config):
        """
        Inizializza il DamageDetector
        
        Args:
            config: Oggetto ConfigLoader con i parametri
        """
        self.config = config
        self.confidence_threshold = config.get('damage_detection.confidence_threshold', 0.6)
        self.min_area = config.get('damage_detection.min_area_pixels', 100)
        self.max_area = config.get('damage_detection.max_area_pixels', 500000)
        self.damage_types = config.get_damage_types()
    
    def detect_cracks(self, image: np.ndarray, image_gray: np.ndarray) -> List[Damage]:
        """
        Rileva crepe e fessure
        
        Args:
            image: Immagine BGR
            image_gray: Immagine in grayscale
        
        Returns:
            Lista di danni rilevati
        """
        damages = []
        
        # Applica edge detection
        edges = cv2.Canny(image_gray, 50, 150)
        
        # Dilatazione per connettere i bordi
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Trova contorni
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Filtra per area
            if self.min_area <= area <= self.max_area:
                # Controlla le proporzioni (le crepe sono lunghe e strette)
                aspect_ratio = max(w, h) / (min(w, h) + 1e-5)
                if aspect_ratio > 2:  # Almeno 2:1
                    damage = Damage(
                        damage_type='crepe_fessure',
                        x=x, y=y, width=w, height=h,
                        area=int(area),
                        confidence=0.8,
                        contour=contour
                    )
                    damages.append(damage)
        
        logger.info(f"Detected {len(damages)} cracks")
        return damages
    
    def detect_detachments(self, image: np.ndarray, image_gray: np.ndarray) -> List[Damage]:
        """
        Rileva distacchi dell'intonaco
        
        Args:
            image: Immagine BGR
            image_gray: Immagine in grayscale
        
        Returns:
            Lista di danni rilevati
        """
        damages = []
        
        # Usa threshold per trovare aree scure (distacchi)
        _, thresh = cv2.threshold(image_gray, 100, 255, cv2.THRESH_BINARY_INV)
        
        # Morph operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            if self.min_area <= area <= self.max_area:
                damage = Damage(
                    damage_type='distacchi',
                    x=x, y=y, width=w, height=h,
                    area=int(area),
                    confidence=0.75,
                    contour=contour
                )
                damages.append(damage)
        
        logger.info(f"Detected {len(damages)} detachments")
        return damages
    
    def detect_humidity(self, image: np.ndarray) -> List[Damage]:
        """
        Rileva umidità e efflorescenza (aree chiare/biancastre)
        
        Args:
            image: Immagine BGR
        
        Returns:
            Lista di danni rilevati
        """
        damages = []
        
        # Converte a HSV per rilevare aree chiare
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Range per aree chiare (alta luminosità, bassa saturazione)
        lower = np.array([0, 0, 150])
        upper = np.array([180, 50, 255])
        
        mask = cv2.inRange(hsv, lower, upper)
        
        # Morph operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            if self.min_area <= area <= self.max_area:
                damage = Damage(
                    damage_type='umidita_efflorescenza',
                    x=x, y=y, width=w, height=h,
                    area=int(area),
                    confidence=0.7,
                    contour=contour
                )
                damages.append(damage)
        
        logger.info(f"Detected {len(damages)} humidity/efflorescence areas")
        return damages
    
    def detect_mold_stains(self, image: np.ndarray) -> List[Damage]:
        """
        Rileva macchie e muffa (aree scure/colorate anomale)
        
        Args:
            image: Immagine BGR
        
        Returns:
            Lista di danni rilevati
        """
        damages = []
        
        # Converte a LAB per rilevare anomalie di colore
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Usa kmeans per segmentazione del colore
        pixels = lab.reshape((-1, 3))
        pixels = np.float32(pixels)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, 4, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Trova i cluster scuri
        for cluster_idx in range(len(centers)):
            if centers[cluster_idx][0] < 100:  # Cluster scuro
                mask = (labels == cluster_idx).reshape(lab.shape[:2]).astype(np.uint8) * 255
                
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    area = cv2.contourArea(contour)
                    
                    if self.min_area <= area <= self.max_area:
                        damage = Damage(
                            damage_type='macchie_muffa',
                            x=x, y=y, width=w, height=h,
                            area=int(area),
                            confidence=0.68,
                            contour=contour
                        )
                        damages.append(damage)
        
        logger.info(f"Detected {len(damages)} mold/stain areas")
        return damages
    
    def detect_missing_plaster(self, image: np.ndarray, image_gray: np.ndarray) -> List[Damage]:
        """
        Rileva aree di intonaco mancante
        
        Args:
            image: Immagine BGR
            image_gray: Immagine in grayscale
        
        Returns:
            Lista di danni rilevati
        """
        damages = []
        
        # Usa Otsu threshold
        _, thresh = cv2.threshold(image_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morph operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)
        
        contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            if self.min_area <= area <= self.max_area:
                damage = Damage(
                    damage_type='intonaco_mancante',
                    x=x, y=y, width=w, height=h,
                    area=int(area),
                    confidence=0.72,
                    contour=contour
                )
                damages.append(damage)
        
        logger.info(f"Detected {len(damages)} missing plaster areas")
        return damages
    
    def detect_all_damages(self, image: np.ndarray) -> List[Damage]:
        """
        Rileva tutti i tipi di danni
        
        Args:
            image: Immagine BGR preprocessata
        
        Returns:
            Lista di tutti i danni rilevati
        """
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        all_damages = []
        
        # Rileva ogni tipo di danno
        all_damages.extend(self.detect_cracks(image, image_gray))
        all_damages.extend(self.detect_detachments(image, image_gray))
        all_damages.extend(self.detect_humidity(image))
        all_damages.extend(self.detect_mold_stains(image))
        all_damages.extend(self.detect_missing_plaster(image, image_gray))
        
        # Filtra per confidence
        all_damages = [d for d in all_damages if d.confidence >= self.confidence_threshold]
        
        logger.info(f"Total damages detected: {len(all_damages)}")
        return all_damages
