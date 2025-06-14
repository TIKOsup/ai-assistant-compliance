# fixed_analyzer.py
import pymupdf4llm
import sys
import os
import argparse
from datetime import datetime
import json

# Принудительно отключаем OpenAI и используем локальные модели
os.environ['OPENAI_API_KEY'] = ''

try:
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.llms.ollama import Ollama
    
    # Настройка локальных моделей
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
    
    print("✅ Локальные модели настроены")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Установите: pip install llama-index sentence-transformers")
    sys.exit(1)

def simple_contract_analysis(pdf_path, regulations_path="./regulations"):
    """Упрощенный анализ договора"""
    print(f"🚀 Анализ договора: {os.path.basename(pdf_path)}")
    
    # 1. Читаем PDF договора
    print("📄 Извлечение текста из PDF...")
    try:
        contract_text = pymupdf4llm.to_markdown(pdf_path)
        print(f"✅ Извлечено {len(contract_text)} символов")
    except Exception as e:
        print(f"❌ Ошибка чтения PDF: {e}")
        return
    
    # 2. Читаем регламенты
    print("📚 Загрузка регламентов...")
    try:
        if not os.path.exists(regulations_path):
            print(f"❌ Папка {regulations_path} не найдена")
            return
        
        # Читаем все PDF файлы из папки регламентов
        regulation_texts = []
        for file in os.listdir(regulations_path):
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(regulations_path, file)
                try:
                    text = pymupdf4llm.to_markdown(file_path)
                    regulation_texts.append(f"=== {file} ===\n{text}")
                    print(f"✅ Загружен: {file}")
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки {file}: {e}")
        
        all_regulations = "\n\n".join(regulation_texts)
        print(f"✅ Загружено {len(regulation_texts)} регламентов")
        
    except Exception as e:
        print(f"❌ Ошибка загрузки регламентов: {e}")
        return
    
    # 3. Создаем простой анализ
    print("🔍 Анализ договора...")
    
    # Объединяем все в один документ для анализа
    combined_text = f"""
РЕГЛАМЕНТЫ И ПРАВИЛА:
{all_regulations[:10000]}  # Ограничиваем размер

АНАЛИЗИРУЕМЫЙ ДОГОВОР:
{contract_text}

ЗАДАЧА:
Проанализируй договор на соответствие регламентам и определи:
1. РЕШЕНИЕ: ПРИНЯТЬ или ОТКАЗАТЬ
2. ПРИЧИНА: подробное обоснование со ссылкой на конкретный регламент
3. РЕКОМЕНДАЦИИ: дополнительные действия если нужны

Обрати внимание на:
- Санкционные списки
- Валютное регулирование
- Соответствие нормативам
- Ограничения и лимиты
"""
    
    try:
        # Создаем документ и индекс
        doc = Document(text=combined_text)
        index = VectorStoreIndex.from_documents([doc])
        
        # Делаем запрос
        query_engine = index.as_query_engine()
        response = query_engine.query("Проанализируй договор и дай заключение")
        
        # Выводим результат
        print("\n" + "="*60)
        print("📋 РЕЗУЛЬТАТ АНАЛИЗА:")
        print("="*60)
        print(str(response))
        print("="*60)
        
        # Сохраняем в файл
        with open("analysis_result.txt", "w", encoding="utf-8") as f:
            f.write(f"Анализ файла: {pdf_path}\n")
            f.write(f"Дата: {datetime.now().isoformat()}\n")
            f.write("="*60 + "\n")
            f.write(str(response))
        
        print("💾 Результат сохранен в analysis_result.txt")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python fixed_analyzer.py contract.pdf")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    simple_contract_analysis(pdf_file)