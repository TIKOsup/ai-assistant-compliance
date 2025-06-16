# simple_analyzer.py
import pymupdf4llm
import sys
import os
import argparse
from datetime import datetime
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
import json

class ContractAnalyzer:
    def __init__(self, regulations_path="./regulations", model_name="llama3.1:8b"):
        self.regulations_path = regulations_path
        self.model_name = model_name
        self.regulations_index = None
        
        # Настройка LLM и embeddings
        Settings.llm = Ollama(model=model_name, request_timeout=120.0)
        Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        print(f"🔧 Инициализация анализатора с моделью: {model_name}")
    
    def load_regulations(self):
        """Загружаем все регламенты и создаем индекс"""
        if not os.path.exists(self.regulations_path):
            print(f"❌ Папка {self.regulations_path} не найдена!")
            print(f"📁 Создайте папку и поместите туда регламенты:")
            print(f"   mkdir {self.regulations_path}")
            return False
        
        print("🔄 Загрузка регламентов...")
        
        # Получаем список файлов
        files = []
        for file in os.listdir(self.regulations_path):
            if file.lower().endswith(('.pdf', '.docx', '.doc', '.txt')):
                files.append(file)
        
        if not files:
            print("❌ Нет файлов регламентов в папке!")
            return False
        
        print(f"📚 Найдено файлов: {len(files)}")
        for file in files:
            print(f"   📄 {file}")
        
        try:
            # Загружаем документы
            documents = SimpleDirectoryReader(self.regulations_path).load_data()
            
            # Создаем индекс
            self.regulations_index = VectorStoreIndex.from_documents(documents)
            
            print("✅ Регламенты успешно загружены и проиндексированы")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке регламентов: {str(e)}")
            return False
    
    def extract_text_from_pdf(self, pdf_path):
        """Извлекаем текст из PDF"""
        if not os.path.exists(pdf_path):
            print(f"❌ Файл не найден: {pdf_path}")
            return None
        
        print(f"📄 Извлечение текста из: {os.path.basename(pdf_path)}")
        
        try:
            # Извлекаем текст с помощью pymupdf4llm
            contract_text = pymupdf4llm.to_markdown(pdf_path)
            
            if not contract_text.strip():
                print("⚠️ Файл пустой или текст не извлечен")
                return None
            
            print(f"✅ Извлечено {len(contract_text)} символов текста")
            return contract_text
            
        except Exception as e:
            print(f"❌ Ошибка при извлечении текста: {str(e)}")
            return None
    
    def analyze_contract(self, contract_text):
        """Анализируем договор на основе регламентов"""
        if not self.regulations_index:
            print("❌ Регламенты не загружены!")
            return None
        
        print("🔍 Анализ договора...")
        
        # Формируем промпт для анализа
        analysis_prompt = f"""
Ты - эксперт по анализу договоров и соблюдению санкционного законодательства.

Проанализируй следующий договор и определи:
1. Можно ли его ПРИНЯТЬ или нужно ОТКАЗАТЬ
2. Укажи КОНКРЕТНУЮ причину решения со ссылкой на соответствующий регламент или документ

ДОГОВОР ДЛЯ АНАЛИЗА:
{contract_text[:4000]}  # Ограничиваем размер для лучшей обработки

КРИТЕРИИ ПРОВЕРКИ:
- Санкционные списки США, ЕС, UK
- Валютное регулирование и валютный контроль
- Соответствие нормативным документам
- Лимиты и ограничения по операциям
- Проверка контрагентов и товаров

ФОРМАТ ОТВЕТА:
РЕШЕНИЕ: [ПРИНЯТЬ/ОТКАЗАТЬ]
ПРИЧИНА: [подробное объяснение с указанием конкретного документа/регламента]
РЕКОМЕНДАЦИИ: [дополнительные действия при необходимости]
"""
        
        try:
            # Получаем ответ от системы
            query_engine = self.regulations_index.as_query_engine(
                similarity_top_k=5,
                response_mode="compact"
            )
            
            response = query_engine.query(analysis_prompt)
            return str(response)
            
        except Exception as e:
            print(f"❌ Ошибка при анализе: {str(e)}")
            return None
    
    def parse_analysis_result(self, analysis_text):
        """Парсим результат анализа"""
        decision = "НЕ ОПРЕДЕЛЕНО"
        reason = "Не удалось определить причину"
        recommendations = ""
        
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('РЕШЕНИЕ:'):
                decision = line.split(':', 1)[1].strip()
            elif line.upper().startswith('ПРИЧИНА:'):
                reason = line.split(':', 1)[1].strip()
            elif line.upper().startswith('РЕКОМЕНДАЦИИ:'):
                recommendations = line.split(':', 1)[1].strip()
        
        return decision, reason, recommendations
    
    def save_analysis_log(self, filename, decision, reason, recommendations=""):
        """Сохраняем лог анализа"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "decision": decision,
            "reason": reason,
            "recommendations": recommendations
        }
        
        log_file = "contract_analysis_log.json"
        
        # Читаем существующий лог
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Добавляем новую запись
        logs.append(log_entry)
        
        # Сохраняем
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        print(f"📝 Результат сохранен в {log_file}")
    
    def analyze_pdf_contract(self, pdf_path, save_log=True):
        """Полный цикл анализа PDF договора"""
        filename = os.path.basename(pdf_path)
        print(f"\n{'='*60}")
        print(f"📋 АНАЛИЗ ДОГОВОРА: {filename}")
        print(f"{'='*60}")
        
        # Извлекаем текст из PDF
        contract_text = self.extract_text_from_pdf(pdf_path)
        if not contract_text:
            return None
        
        # Показываем превью текста
        print(f"\n📄 ПРЕВЬЮ ДОГОВОРА (первые 500 символов):")
        print("-" * 50)
        print(contract_text[:500] + "..." if len(contract_text) > 500 else contract_text)
        print("-" * 50)
        
        # Анализируем договор
        analysis_result = self.analyze_contract(contract_text)
        if not analysis_result:
            return None
        
        # Парсим результат
        decision, reason, recommendations = self.parse_analysis_result(analysis_result)
        
        # Выводим результат
        print(f"\n🎯 РЕЗУЛЬТАТ АНАЛИЗА:")
        print("=" * 50)
        
        # Решение с цветовым кодированием
        if "ПРИНЯТЬ" in decision.upper():
            print(f"✅ РЕШЕНИЕ: {decision}")
        else:
            print(f"❌ РЕШЕНИЕ: {decision}")
        
        print(f"\n📝 ПРИЧИНА:")
        print(reason)
        
        if recommendations:
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            print(recommendations)
        
        print(f"\n📋 ПОЛНЫЙ АНАЛИЗ:")
        print("-" * 30)
        print(analysis_result)
        
        # Сохраняем лог
        if save_log:
            self.save_analysis_log(filename, decision, reason, recommendations)
        
        return {
            "decision": decision,
            "reason": reason, 
            "recommendations": recommendations,
            "full_analysis": analysis_result
        }

def main():
    parser = argparse.ArgumentParser(description="Анализатор PDF договоров")
    parser.add_argument("pdf_file", help="Путь к PDF файлу договора")
    parser.add_argument("--model", default="llama3.1:8b", help="Модель Ollama (по умолчанию: llama3.1:8b)")
    parser.add_argument("--regulations", default="./regulations", help="Папка с регламентами")
    parser.add_argument("--no-log", action="store_true", help="Не сохранять лог анализа")
    
    args = parser.parse_args()
    
    print("🚀 Запуск анализатора договоров")
    print(f"📁 Папка регламентов: {args.regulations}")
    print(f"🤖 Модель: {args.model}")
    
    # Создаем анализатор
    analyzer = ContractAnalyzer(
        regulations_path=args.regulations,
        model_name=args.model
    )
    
    # Загружаем регламенты
    if not analyzer.load_regulations():
        print("\n❌ Не удалось загрузить регламенты. Завершение работы.")
        sys.exit(1)
    
    # Анализируем договор
    result = analyzer.analyze_pdf_contract(
        args.pdf_file, 
        save_log=not args.no_log
    )
    
    if result:
        print(f"\n✅ Анализ завершен успешно!")
    else:
        print(f"\n❌ Анализ завершен с ошибками")
        sys.exit(1)

if __name__ == "__main__":
    main()