
"""
PDF Generator - Creates PDF files from pattern instructions
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import arabic_reshaper
from bidi.algorithm import get_display

class PDFGenerator:
    """Generates PDF with crochet instructions"""
    
    def __init__(self):
        self._register_fonts()
        
    def _register_fonts(self):
        """Register Arabic-supporting fonts"""
        try:
            # Check for fonts directory
            font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'Arial.ttf')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arabic', font_path))
                self.font_name = 'Arabic'
            else:
                # Fallback to standard if no font found (Arabic will likely fail)
                print("Warning: Arial.ttf not found in fonts/ directory")
                self.font_name = 'Helvetica'
        except Exception as e:
            print(f"Font registration error: {e}")
            self.font_name = 'Helvetica'

    def _process_text(self, text):
        """Reshape Arabic text for proper display"""
        if not text:
            return ""
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text

    def generate_steps_pdf(self, steps, basic_info, output_path):
        """
        Generate PDF with steps
        
        Args:
            steps (list): List of step dictionaries
            basic_info (dict): Project info (size, colors, etc)
            output_path (str): Path to save PDF
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=50, leftMargin=50,
            topMargin=50, bottomMargin=50
        )
        
        styles = getSampleStyleSheet()
        
        # Create custom style for Arabic text
        # alignment=2 means CENTER, 1=LEFT, 0=LEFT?? No, 0=Left, 1=Center, 2=Right
        # For Arabic we want Right alignment usually, but Center for headers
        
        title_style = ParagraphStyle(
            'ArabicTitle',
            parent=styles['Heading1'],
            fontName=self.font_name,
            fontSize=24,
            alignment=1, # Center
            spaceAfter=30
        )
        
        normal_style = ParagraphStyle(
            'ArabicNormal',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=14,
            alignment=2, # Right alignment for Arabic
            leading=20
        )
        
        elements = []
        
        # Title
        title_text = self._process_text("مخطط الكروشيه")
        elements.append(Paragraph(title_text, title_style))
        
        # Basic Info
        info_text_1 = f"الحجم: {basic_info.get('width')}x{basic_info.get('height')} غرزة"
        info_text_2 = f"عدد الألوان: {basic_info.get('color_count')}"
        
        elements.append(Paragraph(self._process_text(info_text_1), normal_style))
        elements.append(Paragraph(self._process_text(info_text_2), normal_style))
        elements.append(Spacer(1, 20))
        
        # Steps
        current_row = 0
        
        for step in steps:
            # Add row header if new row
            if step['row'] != current_row:
                current_row = step['row']
                elements.append(Spacer(1, 10))
                row_text = self._process_text(f"--- السطر {current_row} ---")
                elements.append(Paragraph(row_text, ParagraphStyle(
                    'RowHeader',
                    parent=normal_style,
                    alignment=1, # Center
                    fontSize=12,
                    textColor=colors.gray
                )))
            
            # Step instruction
            # instruction_ar from step generator is like "اشتغلي 5 غرز من اللون أحمر الى اليمين"
            instruction = step['instruction_ar']
            # Prepend step number ? e.g. "1. instruction"
            full_text = f"{step['step_number']}. {instruction}"
            
            elements.append(Paragraph(self._process_text(full_text), normal_style))
            
        # Build PDF
        doc.build(elements)
        return output_path

