"""
Report Generator module
Genera report dei danni in vari formati
"""

import csv
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from .damage_detector import Damage

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Classe per la generazione di report"""
    
    def __init__(self, config):
        """
        Inizializza il ReportGenerator
        
        Args:
            config: Oggetto ConfigLoader
        """
        self.config = config
        self.damage_types = config.get_damage_types()
    
    def _get_damage_description(self, damage_type: str) -> str:
        """Ottiene la descrizione di un tipo di danno"""
        if damage_type in self.damage_types:
            return self.damage_types[damage_type]['description']
        return damage_type
    
    def generate_csv_report(self, damages: List[Damage], image_name: str, 
                          output_path: str) -> bool:
        """
        Genera un report CSV dei danni
        
        Args:
            damages: Lista dei danni rilevati
            image_name: Nome dell'immagine analizzata
            output_path: Percorso del file CSV di output
        
        Returns:
            True se creato con successo
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Image', 'Damage_Type', 'Description', 'X', 'Y', 
                            'Width', 'Height', 'Area_px', 'Center_X', 'Center_Y', 
                            'Confidence', 'Timestamp']
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for damage in damages:
                    writer.writerow({
                        'Image': image_name,
                        'Damage_Type': damage.damage_type,
                        'Description': self._get_damage_description(damage.damage_type),
                        'X': damage.x,
                        'Y': damage.y,
                        'Width': damage.width,
                        'Height': damage.height,
                        'Area_px': damage.area,
                        'Center_X': damage.x + damage.width // 2,
                        'Center_Y': damage.y + damage.height // 2,
                        'Confidence': f"{damage.confidence:.2f}",
                        'Timestamp': datetime.now().isoformat()
                    })
            
            logger.info(f"CSV report saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error generating CSV report: {str(e)}")
            return False
    
    def generate_json_report(self, damages: List[Damage], image_name: str,
                           output_path: str) -> bool:
        """
        Genera un report JSON dei danni
        
        Args:
            damages: Lista dei danni rilevati
            image_name: Nome dell'immagine analizzata
            output_path: Percorso del file JSON di output
        
        Returns:
            True se creato con successo
        """
        try:
            report = {
                'metadata': {
                    'image_name': image_name,
                    'timestamp': datetime.now().isoformat(),
                    'total_damages': len(damages),
                    'analysis_version': '1.0.0'
                },
                'statistics': self._calculate_statistics(damages),
                'damages': [damage.to_dict() for damage in damages]
            }
            
            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(report, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON report saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}")
            return False
    
    def _calculate_statistics(self, damages: List[Damage]) -> Dict[str, Any]:
        """
        Calcola statistiche sui danni
        
        Args:
            damages: Lista dei danni
        
        Returns:
            Dizionario con statistiche
        """
        if not damages:
            return {
                'total_affected_area': 0,
                'average_area': 0,
                'average_confidence': 0,
                'damages_by_type': {},
                'severity_score': 0
            }
        
        total_area = sum(d.area for d in damages)
        avg_area = total_area / len(damages)
        avg_confidence = sum(d.confidence for d in damages) / len(damages)
        
        # Conta per tipo
        by_type = {}
        for damage in damages:
            dtype = damage.damage_type
            if dtype not in by_type:
                by_type[dtype] = {'count': 0, 'total_area': 0, 'avg_confidence': 0}
            by_type[dtype]['count'] += 1
            by_type[dtype]['total_area'] += damage.area
        
        for dtype in by_type:
            by_type[dtype]['avg_confidence'] = sum(
                d.confidence for d in damages if d.damage_type == dtype
            ) / by_type[dtype]['count']
        
        # Calcola severity score (0-100)
        severity = min(100, (total_area / 1000000) * (avg_confidence * 100))
        
        return {
            'total_affected_area': int(total_area),
            'average_area': float(avg_area),
            'average_confidence': float(avg_confidence),
            'damages_by_type': by_type,
            'severity_score': float(severity)
        }
    
    def generate_text_report(self, damages: List[Damage], image_name: str,
                           output_path: str) -> bool:
        """
        Genera un report testuale leggibile
        
        Args:
            damages: Lista dei danni rilevati
            image_name: Nome dell'immagine analizzata
            output_path: Percorso del file TXT di output
        
        Returns:
            True se creato con successo
        """
        try:
            stats = self._calculate_statistics(damages)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("WALL DAMAGE ANALYSIS REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Image: {image_name}\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Damages Detected: {len(damages)}\n\n")
                
                f.write("-" * 80 + "\n")
                f.write("SUMMARY STATISTICS\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total Affected Area: {stats['total_affected_area']} pixels\n")
                f.write(f"Average Damage Area: {stats['average_area']:.2f} pixels\n")
                f.write(f"Average Confidence: {stats['average_confidence']:.2%}\n")
                f.write(f"Severity Score: {stats['severity_score']:.1f}/100\n\n")
                
                f.write("-" * 80 + "\n")
                f.write("DAMAGES BY TYPE\n")
                f.write("-" * 80 + "\n")
                for dtype, data in stats['damages_by_type'].items():
                    f.write(f"\n{self._get_damage_description(dtype)}:\n")
                    f.write(f"  Count: {data['count']}\n")
                    f.write(f"  Total Area: {data['total_area']} pixels\n")
                    f.write(f"  Avg Confidence: {data['avg_confidence']:.2%}\n")
                
                f.write("\n" + "-" * 80 + "\n")
                f.write("DETAILED DAMAGES LIST\n")
                f.write("-" * 80 + "\n\n")
                
                for i, damage in enumerate(damages, 1):
                    f.write(f"Damage #{i}\n")
                    f.write(f"  Type: {self._get_damage_description(damage.damage_type)}\n")
                    f.write(f"  Position: X={damage.x}, Y={damage.y}\n")
                    f.write(f"  Size: {damage.width}x{damage.height} pixels\n")
                    f.write(f"  Area: {damage.area} pixels\n")
                    f.write(f"  Center: ({damage.x + damage.width // 2}, "
                           f"{damage.y + damage.height // 2})\n")
                    f.write(f"  Confidence: {damage.confidence:.2%}\n\n")
                
                f.write("=" * 80 + "\n")
                f.write("END OF REPORT\n")
                f.write("=" * 80 + "\n")
            
            logger.info(f"Text report saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error generating text report: {str(e)}")
            return False
