"""
Image Processor module
Gestisce il preprocessing delle immagini
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Classe per il preprocessing delle immagini"""
    
    def __init__(self, config):
        """
        Inizializza l'ImageProcessor
        
        Args:
            config: Oggetto ConfigLoader con i parametri
        """
        self.config = config
        self.resize_width = config.get('image_processing.resize_width', 1024)
        self.resize_height = config.get('image_processing.resize_height', 768)
        self.contrast_enhancement = config.get('image_processing.preprocessing.contrast_enhancement', True)
        self.histogram_equalization = config.get('image_processing.preprocessing.histogram_equalization', True)
        self.noise_reduction = config.get('image_processing.preprocessing.noise_reduction', True)
        self.blur_kernel = config.get('image_processing.preprocessing.blur_kernel', 5)
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Carica un'immagine da file
        
        Args:
            image_path: Percorso dell'immagine
        
        Returns:
            Array numpy con l'immagine caricata (BGR)
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            logger.info(f"Loaded image: {image_path} (shape: {image.shape})")
            return image
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {str(e)}")
            return None
    
    def resize_image(self, image: np.ndarray, width: Optional[int] = None, 
                    height: Optional[int] = None) -> np.ndarray:
        """
        Ridimensiona un'immagine
        
        Args:
            image: Immagine di input
            width: Larghezza desiderata (usa default se None)
            height: Altezza desiderata (usa default se None)
        
        Returns:
            Immagine ridimensionata
        """
        w = width or self.resize_width
        h = height or self.resize_height
        
        resized = cv2.resize(image, (w, h), interpolation=cv2.INTER_AREA)
        logger.debug(f"Resized image to {w}x{h}")
        return resized
    
    def enhance_contrast(self, image: np.ndarray, clip_limit: float = 2.0, 
                        tile_size: int = 8) -> np.ndarray:
        """
        Migliora il contrasto usando CLAHE (Contrast Limited Adaptive Histogram Equalization)
        
        Args:
            image: Immagine di input (BGR)
            clip_limit: Limite di contrasto
            tile_size: Dimensione della tile
        
        Returns:
            Immagine con contrasto migliorato
        """
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
        l = clahe.apply(l)
        
        lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        logger.debug("Applied contrast enhancement")
        return enhanced
    
    def reduce_noise(self, image: np.ndarray, h: int = 10, template_window_size: int = 7,
                    search_window_size: int = 21) -> np.ndarray:
        """
        Riduce il rumore usando Non-Local Means Denoising
        
        Args:
            image: Immagine di input
            h: Forza del filtro
            template_window_size: Dimensione della finestra template
            search_window_size: Dimensione della finestra di ricerca
        
        Returns:
            Immagine con rumore ridotto
        """
        denoised = cv2.fastNlMeansDenoisingColored(
            image,
            None,
            h=h,
            hForColorComponents=h,
            templateWindowSize=template_window_size,
            searchWindowSize=search_window_size
        )
        logger.debug("Applied noise reduction")
        return denoised
    
    def apply_histogram_equalization(self, image: np.ndarray) -> np.ndarray:
        """
        Applica l'equalizzazione dell'istogramma
        
        Args:
            image: Immagine di input (BGR)
        
        Returns:
            Immagine con istogramma equalizzato
        """
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        l = cv2.equalizeHist(l)
        
        lab = cv2.merge([l, a, b])
        equalized = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        logger.debug("Applied histogram equalization")
        return equalized
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Applica il preprocessing completo all'immagine
        
        Args:
            image: Immagine di input
        
        Returns:
            Immagine preprocessata
        """
        # Ridimensiona
        image = self.resize_image(image)
        
        # Riduzione rumore
        if self.noise_reduction:
            image = self.reduce_noise(image)
        
        # Miglioramento contrasto
        if self.contrast_enhancement:
            image = self.enhance_contrast(image)
        
        # Equalizzazione istogramma
        if self.histogram_equalization:
            image = self.apply_histogram_equalization(image)
        
        logger.info("Image preprocessing completed")
        return image
    
    def save_image(self, image: np.ndarray, output_path: str) -> bool:
        """
        Salva un'immagine su file
        
        Args:
            image: Immagine da salvare
            output_path: Percorso di output
        
        Returns:
            True se salvato con successo, False altrimenti
        """
        try:
            cv2.imwrite(output_path, image)
            logger.info(f"Saved image to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving image to {output_path}: {str(e)}")
            return False
    
    def convert_to_hsv(self, image: np.ndarray) -> np.ndarray:
        """Converte da BGR a HSV"""
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    def convert_to_gray(self, image: np.ndarray) -> np.ndarray:
        """Converte da BGR a grayscale"""
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
