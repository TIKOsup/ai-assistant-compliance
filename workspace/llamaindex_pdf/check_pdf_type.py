# check_pdf_type.py
import pymupdf  # PyMuPDF
import sys
import os

def check_pdf_content(pdf_path):
    """Проверяем содержит ли PDF текст или только изображения"""
    print(f"🔍 Анализ файла: {os.path.basename(pdf_path)}")
    
    try:
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        text_pages = 0
        image_pages = 0
        
        print(f"📄 Всего страниц: {total_pages}")
        
        for page_num in range(total_pages):
            page = doc[page_num]
            
            # Проверяем текст
            text = page.get_text()
            text_length = len(text.strip())
            
            # Проверяем изображения
            images = page.get_images()
            
            if text_length > 50:  # Если есть значимый текст
                text_pages += 1
                print(f"  📝 Страница {page_num + 1}: ТЕКСТ ({text_length} символов)")
            elif images:
                image_pages += 1
                print(f"  🖼️ Страница {page_num + 1}: ИЗОБРАЖЕНИЕ ({len(images)} изображений)")
            else:
                print(f"  ❓ Страница {page_num + 1}: ПУСТАЯ")
            
            # Показываем первые 100 символов текста для примера
            if text_length > 0:
                print(f"     Превью: {text[:100]}...")
        
        doc.close()
        
        print(f"\n📊 ИТОГ:")
        print(f"  Страниц с текстом: {text_pages}")
        print(f"  Страниц с изображениями: {image_pages}")
        
        if text_pages == 0 and image_pages > 0:
            print("  🎯 РЕЗУЛЬТАТ: Отсканированный документ - нужен OCR!")
            return "scanned"
        elif text_pages > 0:
            print("  🎯 РЕЗУЛЬТАТ: Текстовый PDF - можно использовать обычное извлечение")
            return "text"
        else:
            print("  🎯 РЕЗУЛЬТАТ: Неопределенный тип")
            return "unknown"
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return "error"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python check_pdf_type.py file.pdf")
        sys.exit(1)
    
    result = check_pdf_content(sys.argv[1])
    print(f"\nТип документа: {result}")