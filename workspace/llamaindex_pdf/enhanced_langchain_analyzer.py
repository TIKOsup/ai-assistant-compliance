# enhanced_langchain_analyzer.py
import os
import sys
import argparse
from datetime import datetime
import json
import warnings
from pathlib import Path

# PDF и OCR обработка
import pymupdf4llm
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# LangChain компоненты
from langchain.llms import Ollama
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Отключаем предупреждения
warnings.filterwarnings("ignore")
Image.MAX_IMAGE_PIXELS = None

class EnhancedContractAnalyzer:
    def __init__(self, regulations_path="./regulations", model_name="qwen2.5:3b-instruct"):
        self.regulations_path = regulations_path
        self.model_name = model_name
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.regulations_summary = ""  # Сводка всех регламентов
        
        print(f"🚀 Инициализация улучшенного анализатора")
        print(f"🤖 Модель: {model_name}")
        
        self.setup_embeddings()
        self.prepare_regulations_summary()
        self.setup_llm()
    
    def prepare_regulations_summary(self):
        """Подготавливаем сводку всех регламентов для системного промпта"""
        print("📚 Подготовка сводки регламентов...")
        
        processed_path = "./processed_regulations"
        regulations_data = []
        
        if os.path.exists(processed_path):
            txt_files = [f for f in os.listdir(processed_path) if f.endswith('.txt')]
            
            for file in txt_files:
                file_path = os.path.join(processed_path, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Очищаем служебную информацию
                    if "=" * 60 in content:
                        content = content.split("=" * 60, 1)[-1].strip()
                    
                    if len(content.strip()) > 100:
                        # Извлекаем ключевые части документа
                        key_info = self.extract_key_info(content, file)
                        regulations_data.append(key_info)
                        print(f"✅ Обработан: {file}")
                    
                except Exception as e:
                    print(f"❌ Ошибка обработки {file}: {e}")
        
        # Формируем сводку для системного промпта
        self.regulations_summary = self.create_regulations_summary(regulations_data)
        print(f"✅ Подготовлена сводка регламентов: {len(self.regulations_summary)} символов")
    
    def extract_key_info(self, content, filename):
        """Извлекаем ключевую информацию из документа"""
        key_info = {
            'filename': filename.replace('.txt', ''),
            'key_points': [],
            'sanctions': [],
            'currency_rules': [],
            'prohibited_items': [],
            'procedures': []
        }
        
        content_lower = content.lower()
        lines = content.split('\n')
        
        # Ищем ключевые разделы
        for line in lines:
            line_clean = line.strip()
            if len(line_clean) < 10:
                continue
                
            line_lower = line_clean.lower()
            
            # Санкционные списки и ограничения
            if any(word in line_lower for word in ['санкци', 'запрет', 'ограничен', 'блокир', 'заморож']):
                key_info['sanctions'].append(line_clean)
            
            # Валютное регулирование
            elif any(word in line_lower for word in ['валют', 'курс', 'экспорт', 'импорт', 'девиз']):
                key_info['currency_rules'].append(line_clean)
            
            # Запрещенные товары
            elif any(word in line_lower for word in ['двойного назначения', 'оружи', 'военн', 'технологи']):
                key_info['prohibited_items'].append(line_clean)
            
            # Процедуры и требования
            elif any(word in line_lower for word in ['требуется', 'необходимо', 'обязан', 'должен']):
                key_info['procedures'].append(line_clean)
            
            # Статьи и пункты
            elif any(pattern in line_lower for pattern in ['статья', 'пункт', 'часть', 'подпункт']):
                key_info['key_points'].append(line_clean)
        
        # Ограничиваем количество элементов
        for key in key_info:
            if isinstance(key_info[key], list):
                key_info[key] = key_info[key][:5]  # Максимум 5 элементов каждого типа
        
        return key_info
    
    def create_regulations_summary(self, regulations_data):
        """Создаем структурированную сводку регламентов"""
        summary_parts = []
        
        summary_parts.append("=== НОРМАТИВНАЯ БАЗА ===")
        
        # Санкционные списки
        sanctions_info = []
        for reg in regulations_data:
            if reg['sanctions']:
                sanctions_info.extend(reg['sanctions'])
        
        if sanctions_info:
            summary_parts.append("\n🚨 САНКЦИОННЫЕ ОГРАНИЧЕНИЯ:")
            for item in sanctions_info[:10]:  # Топ-10 самых важных
                summary_parts.append(f"• {item}")
        
        # Валютное регулирование
        currency_info = []
        for reg in regulations_data:
            if reg['currency_rules']:
                currency_info.extend(reg['currency_rules'])
        
        if currency_info:
            summary_parts.append("\n💰 ВАЛЮТНОЕ РЕГУЛИРОВАНИЕ:")
            for item in currency_info[:10]:
                summary_parts.append(f"• {item}")
        
        # Запрещенные товары
        prohibited_info = []
        for reg in regulations_data:
            if reg['prohibited_items']:
                prohibited_info.extend(reg['prohibited_items'])
        
        if prohibited_info:
            summary_parts.append("\n⚗️ ТОВАРЫ ДВОЙНОГО НАЗНАЧЕНИЯ:")
            for item in prohibited_info[:8]:
                summary_parts.append(f"• {item}")
        
        # Процедуры
        procedures_info = []
        for reg in regulations_data:
            if reg['procedures']:
                procedures_info.extend(reg['procedures'])
        
        if procedures_info:
            summary_parts.append("\n📋 ОБЯЗАТЕЛЬНЫЕ ПРОЦЕДУРЫ:")
            for item in procedures_info[:8]:
                summary_parts.append(f"• {item}")
        
        # Источники
        summary_parts.append("\n📚 ИСТОЧНИКИ:")
        for reg in regulations_data:
            summary_parts.append(f"• {reg['filename']}")
        
        return "\n".join(summary_parts)
    
    def setup_embeddings(self):
        """Настройка многоязычных эмбеддингов"""
        print("🔧 Настройка эмбеддингов...")
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            print("✅ Многоязычные эмбеддинги настроены")
        except Exception as e:
            print(f"⚠️ Ошибка эмбеддингов: {e}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
    
    def setup_llm(self):
        """Настройка LLM с полной нормативной базой в системном промпте"""
        print(f"🔧 Настройка {self.model_name} с встроенными регламентами...")
        
        try:
            # Создаем системный промпт с полной информацией о регламентах
            system_prompt = f"""Ты - ведущий эксперт по корпоративному праву и санкционному законодательству РФ.

{self.regulations_summary}

ТВОЯ ЗАДАЧА:
Анализируй договоры на основе ВЫШЕУКАЗАННОЙ нормативной базы. 
Всегда ссылайся на конкретные пункты и статьи из загруженных документов.

СТРУКТУРА АНАЛИЗА:
🎯 РЕШЕНИЕ: [ПРИНЯТЬ/ОТКАЗАТЬ/ТРЕБУЕТ_ПРОВЕРКИ]
📋 ОБОСНОВАНИЕ: [ссылки на конкретные нормы из базы]
⚠️ РИСКИ: [риски согласно регламентам]
💡 РЕКОМЕНДАЦИИ: [действия согласно процедурам]
📚 ИСТОЧНИКИ: [конкретные документы из базы]

ВАЖНО: Используй ТОЛЬКО информацию из приведенной нормативной базы."""
            
            callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
            
            self.llm = Ollama(
                model=self.model_name,
                callback_manager=callback_manager,
                temperature=0.1,
                num_ctx=8192,  # Увеличиваем контекст для регламентов
                num_predict=1024,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1,
                system=system_prompt  # Встраиваем регламенты в систему
            )
            
            print("✅ LLM настроен с встроенными регламентами")
            
        except Exception as e:
            print(f"❌ Ошибка настройки LLM: {e}")
            sys.exit(1)
    
    def extract_text_with_ocr(self, pdf_path):
        """OCR извлечение текста"""
        print(f"🔍 OCR обработка: {os.path.basename(pdf_path)}")
        
        try:
            images = convert_from_path(pdf_path, dpi=200, thread_count=4)
            all_text = []
            
            for i, image in enumerate(images):
                print(f"🔤 OCR страница {i+1}/{len(images)}...")
                custom_config = r'--oem 3 --psm 6 -l rus+eng'
                text = pytesseract.image_to_string(image, config=custom_config)
                
                if text.strip():
                    all_text.append(f"=== Страница {i+1} ===\n{text}")
                del image
            
            combined_text = "\n\n".join(all_text)
            print(f"✅ OCR завершен: {len(combined_text)} символов")
            return combined_text
            
        except Exception as e:
            print(f"❌ Ошибка OCR: {e}")
            return None
    
    def smart_extract_text(self, pdf_path):
        """Умное извлечение текста"""
        try:
            text = pymupdf4llm.to_markdown(pdf_path)
            if len(text.strip()) > 100:
                print(f"✅ Стандартное извлечение: {len(text)} символов")
                return text
            else:
                print("⚠️ Мало текста, используем OCR...")
        except Exception as e:
            print(f"⚠️ Ошибка стандартного извлечения: {e}")
        
        return self.extract_text_with_ocr(pdf_path)
    
    def analyze_contract_direct(self, contract_text):
        """Прямой анализ договора LLM с встроенными регламентами"""
        print("🤖 Запуск анализа с встроенными регламентами...")
        
        # Подготавливаем промпт для анализа
        analysis_prompt = f"""
Проанализируй следующий договор на соответствие нормативной базе:

ТЕКСТ ДОГОВОРА:
{contract_text[:6000]}  # Первые 6000 символов

ОСОБОЕ ВНИМАНИЕ:
1. Проверь стороны договора по санкционным спискам
2. Оцени валютные операции согласно валютному законодательству  
3. Проверь товары/услуги на предмет ограничений
4. Определи необходимые процедуры согласно регламентам

Дай структурированный анализ согласно твоей системной инструкции.
"""
        
        try:
            response = self.llm(analysis_prompt)
            return response
        except Exception as e:
            print(f"❌ Ошибка LLM анализа: {e}")
            return f"Ошибка анализа: {str(e)}"
    
    def analyze_contract(self, contract_path):
        """Полный анализ договора"""
        print(f"\n{'='*80}")
        print(f"⚖️  АНАЛИЗ ДОГОВОРА С ВСТРОЕННЫМИ РЕГЛАМЕНТАМИ")
        print(f"📄 Файл: {os.path.basename(contract_path)}")
        print(f"🤖 Модель: {self.model_name}")
        print(f"📚 Регламентов в системе: {len(self.regulations_summary)} символов")
        print(f"{'='*80}")
        
        # 1. Извлекаем текст договора
        contract_text = self.smart_extract_text(contract_path)
        if not contract_text:
            print("❌ Не удалось извлечь текст договора")
            return None
        
        # 2. Сохраняем извлеченный текст
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        contract_name = Path(contract_path).stem
        
        text_file = f"contract_text_{contract_name}_{timestamp}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"ИЗВЛЕЧЕННЫЙ ТЕКСТ ДОГОВОРА\n")
            f.write(f"{'='*60}\n")
            f.write(f"Исходный файл: {os.path.basename(contract_path)}\n")
            f.write(f"Дата извлечения: {datetime.now().isoformat()}\n")
            f.write(f"Размер текста: {len(contract_text)} символов\n")
            f.write(f"Анализатор: Enhanced LangChain + {self.model_name}\n")
            f.write(f"Регламентов в системе: {len(self.regulations_summary)} символов\n")
            f.write(f"{'='*60}\n\n")
            f.write(contract_text)
        
        print(f"💾 Текст договора сохранен: {text_file}")
        
        # Превью
        print(f"\n📄 ПРЕВЬЮ ДОГОВОРА:")
        print("-" * 60)
        preview = contract_text[:800]
        print(preview)
        if len(contract_text) > 800:
            print("...")
            print(f"[Показано 800 из {len(contract_text)} символов]")
        print("-" * 60)
        
        # 3. Прямой анализ с встроенными регламентами
        print("\n🤖 ЗАПУСК АНАЛИЗА С ВСТРОЕННОЙ НОРМАТИВНОЙ БАЗОЙ...")
        print("=" * 60)
        
        llm_response = self.analyze_contract_direct(contract_text)
        
        # 4. Формируем отчет
        report = {
            'contract_file': os.path.basename(contract_path),
            'contract_text_file': text_file,
            'analysis_date': timestamp,
            'text_length': len(contract_text),
            'analyzer': f"Enhanced LangChain + {self.model_name}",
            'model_name': self.model_name,
            'regulations_embedded': True,
            'regulations_size': len(self.regulations_summary),
            'llm_analysis': llm_response,
            'extraction_method': 'OCR' if '=== Страница' in contract_text else 'Standard'
        }
        
        # 5. Выводим результаты
        self.print_results(report)
        
        # 6. Сохраняем отчеты
        report_file = f"enhanced_analysis_{contract_name}_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        summary_file = f"enhanced_summary_{contract_name}_{timestamp}.txt"
        self.create_summary_report(report, summary_file)
        
        print(f"\n📄 JSON отчет: {report_file}")
        print(f"📋 Сводный отчет: {summary_file}")
        
        return report
    
    def print_results(self, report):
        """Вывод результатов"""
        print(f"\n⚖️  РЕЗУЛЬТАТЫ АНАЛИЗА С ВСТРОЕННЫМИ РЕГЛАМЕНТАМИ:")
        print("=" * 70)
        
        print(f"🤖 Анализатор: {report['analyzer']}")
        print(f"📊 Модель: {report['model_name']}")
        print(f"📏 Размер текста: {report['text_length']:,} символов")
        print(f"🔍 Метод извлечения: {report['extraction_method']}")
        print(f"📚 Регламенты встроены: {'Да' if report['regulations_embedded'] else 'Нет'}")
        print(f"📋 Размер нормативной базы: {report['regulations_size']:,} символов")
        
        print(f"\n📝 ЗАКЛЮЧЕНИЕ ЭКСПЕРТА:")
        print("=" * 50)
        print(report['llm_analysis'])
        print("=" * 50)
    
    def create_summary_report(self, report, summary_file):
        """Создание сводного отчета"""
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("СВОДНЫЙ ОТЧЕТ АНАЛИЗА ДОГОВОРА С ВСТРОЕННЫМИ РЕГЛАМЕНТАМИ\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("ОБЩАЯ ИНФОРМАЦИЯ\n")
            f.write("-" * 30 + "\n")
            f.write(f"Файл договора: {report['contract_file']}\n")
            f.write(f"Дата анализа: {report['analysis_date']}\n")
            f.write(f"Размер текста: {report['text_length']:,} символов\n")
            f.write(f"Анализатор: {report['analyzer']}\n")
            f.write(f"Модель: {report['model_name']}\n")
            f.write(f"Метод извлечения: {report['extraction_method']}\n")
            f.write(f"Файл с текстом: {report['contract_text_file']}\n")
            f.write(f"Регламенты встроены: {'Да' if report['regulations_embedded'] else 'Нет'}\n")
            f.write(f"Размер нормативной базы: {report['regulations_size']:,} символов\n\n")
            
            f.write("ЗАКЛЮЧЕНИЕ ЭКСПЕРТА\n")
            f.write("-" * 30 + "\n")
            f.write(f"{report['llm_analysis']}\n\n")
            
            f.write("ТЕХНИЧЕСКАЯ ИНФОРМАЦИЯ\n")
            f.write("-" * 30 + "\n")
            f.write(f"Время анализа: {report['analysis_date']}\n")
            f.write(f"Регламенты интегрированы в системный промпт: Да\n")
            f.write("\n" + "=" * 70 + "\n")
            f.write("Конец отчета\n")

def main():
    parser = argparse.ArgumentParser(description="Enhanced Contract Analyzer с встроенными регламентами")
    parser.add_argument("pdf_file", help="PDF файл договора")
    parser.add_argument("--model", default="qwen2.5:3b-instruct", help="Модель Ollama")
    parser.add_argument("--regulations", default="./regulations", help="Папка с регламентами")
    
    args = parser.parse_args()
    
    print("🚀 Запуск улучшенного анализатора с встроенными регламентами")
    print(f"📁 Файл: {args.pdf_file}")
    print(f"🤖 Модель: {args.model}")
    
    analyzer = EnhancedContractAnalyzer(
        regulations_path=args.regulations,
        model_name=args.model
    )
    
    result = analyzer.analyze_contract(args.pdf_file)
    
    if result:
        print(f"\n✅ Анализ завершен успешно!")
        print(f"📋 Регламенты интегрированы в системный промпт модели")
    else:
        print(f"\n❌ Анализ завершился с ошибками")

if __name__ == "__main__":
    main()