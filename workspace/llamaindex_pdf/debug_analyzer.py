# debug_analyzer.py
import os
import sys

def check_dependencies():
    """Проверяем все зависимости"""
    print("🔍 Проверка зависимостей...")
    
    try:
        import llama_index
        print("✅ llama_index установлен")
    except ImportError:
        print("❌ llama_index НЕ установлен")
        return False
    
    try:
        from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
        print("✅ llama_index.core доступен")
    except ImportError:
        print("❌ llama_index.core НЕ доступен")
        return False
    
    try:
        import pymupdf4llm
        print("✅ pymupdf4llm установлен")
    except ImportError:
        print("❌ pymupdf4llm НЕ установлен")
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ sentence_transformers установлен")
    except ImportError:
        print("❌ sentence_transformers НЕ установлен")
        return False
    
    return True

def test_file_loading():
    """Тестируем загрузку файлов"""
    regulations_path = "./regulations"
    
    if not os.path.exists(regulations_path):
        print(f"❌ Папка {regulations_path} не существует")
        return False
    
    files = os.listdir(regulations_path)
    pdf_files = [f for f in files if f.lower().endswith('.pdf')]
    
    print(f"📁 Найдено PDF файлов: {len(pdf_files)}")
    
    # Тестируем один файл
    if pdf_files:
        test_file = os.path.join(regulations_path, pdf_files[0])
        print(f"🧪 Тестируем файл: {pdf_files[0]}")
        
        try:
            import pymupdf4llm
            text = pymupdf4llm.to_markdown(test_file)
            print(f"✅ Файл прочитан, длина: {len(text)} символов")
            return True
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {str(e)}")
            return False
    
    return False

def test_simple_index():
    """Тестируем создание простого индекса"""
    print("🧪 Тестируем создание индекса...")
    
    try:
        from llama_index.core import VectorStoreIndex, Document
        
        # Создаем простой документ
        doc = Document(text="Тестовый документ для проверки индексации")
        
        # Пробуем создать индекс
        index = VectorStoreIndex.from_documents([doc])
        print("✅ Простой индекс создан успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания индекса: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Диагностика системы")
    print("=" * 50)
    
    # Проверяем зависимости
    if not check_dependencies():
        print("\n❌ Установите недостающие зависимости:")
        print("pip install llama-index llama-index-core pymupdf4llm sentence-transformers")
        sys.exit(1)
    
    # Проверяем файлы
    if not test_file_loading():
        print("\n❌ Проблемы с загрузкой файлов")
        sys.exit(1)
    
    # Проверяем индексацию
    if not test_simple_index():
        print("\n❌ Проблемы с созданием индекса")
        sys.exit(1)
    
    print("\n✅ Все тесты пройдены успешно!")