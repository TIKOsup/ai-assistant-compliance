# ocr_analyzer.py
import pymupdf4llm
import pymupdf
import pytesseract
from pdf2image import convert_from_path
import sys
import os
from datetime import datetime
from PIL import Image
import tempfile

def extract_text_with_ocr(pdf_path):
    """Извлекаем текст с помощью OCR для отсканированных документов"""
    print(f"🔍 OCR обработка файла: {os.path.basename(pdf_path)}")
    
    try:
        # Конвертируем PDF в изображения
        print("📷 Конвертация PDF в изображения...")
        images = convert_from_path(pdf_path, dpi=300)  # Высокое разрешение для лучшего OCR
        
        all_text = []
        
        for i, image in enumerate(images):
            print(f"🔤 OCR обработка страницы {i+1}/{len(images)}...")
            
            # Настройки для русского и английского языков
            custom_config = r'--oem 3 --psm 6 -l rus+eng'
            
            # Извлекаем текст
            text = pytesseract.image_to_string(image, config=custom_config)
            
            if text.strip():
                all_text.append(f"=== Страница {i+1} ===\n{text}")
                print(f"✅ Страница {i+1}: извлечено {len(text)} символов")
            else:
                print(f"⚠️ Страница {i+1}: текст не найден")
        
        combined_text = "\n\n".join(all_text)
        print(f"✅ OCR завершен. Всего извлечено: {len(combined_text)} символов")
        
        return combined_text
        
    except Exception as e:
        print(f"❌ Ошибка OCR: {e}")
        return None

def smart_extract_text(pdf_path):
    """Умное извлечение текста - сначала пробуем обычный способ, потом OCR"""
    print(f"📄 Извлечение текста из: {os.path.basename(pdf_path)}")
    
    # Сначала пробуем обычное извлечение
    try:
        text = pymupdf4llm.to_markdown(pdf_path)
        if len(text.strip()) > 100:  # Если извлекли достаточно текста
            print(f"✅ Обычное извлечение: {len(text)} символов")
            return text
        else:
            print("⚠️ Мало текста при обычном извлечении, пробуем OCR...")
    except Exception as e:
        print(f"⚠️ Ошибка обычного извлечения: {e}")
        print("🔄 Переходим к OCR...")
    
    # Если обычное не сработало, используем OCR
    return extract_text_with_ocr(pdf_path)

def analyze_contract_with_ocr(pdf_path, regulations_path="./regulations"):
    """Анализ договора с поддержкой OCR"""
    print(f"🚀 Анализ договора с OCR поддержкой")
    print(f"📁 Файл: {pdf_path}")
    
    # Извлекаем текст из договора
    contract_text = smart_extract_text(pdf_path)
    
    if not contract_text:
        print("❌ Не удалось извлечь текст из договора")
        return
    
    # Сохраняем извлеченный текст
    text_file = f"extracted_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(f"Извлеченный текст из: {pdf_path}\n")
        f.write("="*60 + "\n")
        f.write(contract_text)
    
    print(f"💾 Извлеченный текст сохранен в: {text_file}")
    
    # Показываем превью
    print(f"\n📋 ПРЕВЬЮ ИЗВЛЕЧЕННОГО ТЕКСТА:")
    print("-" * 50)
    print(contract_text[:1000])
    print("..." if len(contract_text) > 1000 else "")
    print("-" * 50)
    
    # Простой анализ на основе ключевых слов
    print(f"\n🔍 БЫСТРЫЙ АНАЛИЗ:")
    
    keywords_sanctions = ['санкци', 'запрет', 'ограничен', 'блокир']
    keywords_currency = ['валют', 'доллар', 'евро', 'рубл', 'курс']
    keywords_contract = ['договор', 'контракт', 'соглашен', 'сторон']
    
    text_lower = contract_text.lower()
    
    found_sanctions = [kw for kw in keywords_sanctions if kw in text_lower]
    found_currency = [kw for kw in keywords_currency if kw in text_lower]
    found_contract = [kw for kw in keywords_contract if kw in text_lower]
    
    print(f"📋 Найденные ключевые слова:")
    print(f"  Санкции: {found_sanctions}")
    print(f"  Валюта: {found_currency}")
    print(f"  Договор: {found_contract}")
    
    if found_contract:
        print("✅ Документ похож на договор")
    else:
        print("⚠️ Не уверен что это договор")
    
    return contract_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python ocr_analyzer.py contract.pdf")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    analyze_contract_with_ocr(pdf_file)

