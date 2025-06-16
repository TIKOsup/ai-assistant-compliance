# full_ocr_analyzer.py
import pymupdf4llm
import pymupdf
import pytesseract
from pdf2image import convert_from_path
import sys
import os
import argparse
from datetime import datetime
from PIL import Image
import tempfile
import json
import warnings

# Отключаем предупреждения о размере изображений
warnings.filterwarnings("ignore", category=UserWarning)
Image.MAX_IMAGE_PIXELS = None

# Настройки для локальных моделей
os.environ['OPENAI_API_KEY'] = ''

try:
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.llms.ollama import Ollama
    
    # Настройка локальных моделей
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    Settings.llm = Ollama(model="lowl/t-lite", request_timeout=360.0)
    
    LLAMA_INDEX_AVAILABLE = True
    print("✅ LlamaIndex настроен с локальными моделями")
    
except ImportError as e:
    print(f"⚠️ LlamaIndex не доступен: {e}")
    LLAMA_INDEX_AVAILABLE = False

class OCRContractAnalyzer:
    def __init__(self, regulations_path="./regulations", model_name="owl/t-lite"):
        self.regulations_path = regulations_path
        self.regulations_texts = {}
        self.model_name = model_name
        
    def extract_text_with_ocr(self, pdf_path):
        """Извлекаем текст с помощью OCR для отсканированных документов"""
        print(f"🔍 OCR обработка файла: {os.path.basename(pdf_path)}")
        
        try:
            # Конвертируем PDF в изображения
            print("📷 Конвертация PDF в изображения...")
            images = convert_from_path(pdf_path, dpi=300, thread_count=4)
            
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

    def smart_extract_text(self, pdf_path):
        """Умное извлечение текста - сначала пробуем обычный способ, потом OCR"""
        print(f"📄 Извлечение текста из: {os.path.basename(pdf_path)}")
        
        # Сначала пробуем обычное извлечение
        try:
            text = pymupdf4llm.to_markdown(pdf_path)
            if len(text.strip()) > 100:  # Если извлекли достаточно текста
                print(f"✅ Обычное извлечение: {len(text)} символов")
                return text
            else:
                print("⚠️ Мало текста при обычном извлечении, используем OCR...")
        except Exception as e:
            print(f"⚠️ Ошибка обычного извлечения: {e}")
            print("🔄 Переходим к OCR...")
        
        # Используем OCR
        return self.extract_text_with_ocr(pdf_path)

    def load_regulations(self):
        """Загружаем регламенты - сначала пробуем обработанные, потом исходные"""
        processed_path = "./processed_regulations"
        
        # Пробуем загрузить уже обработанные тексты
        if os.path.exists(processed_path):
            print("🔄 Загрузка обработанных регламентов...")
            txt_files = [f for f in os.listdir(processed_path) if f.endswith('.txt')]
            
            if txt_files:
                print(f"📚 Найдено обработанных файлов: {len(txt_files)}")
                
                for file in txt_files:
                    file_path = os.path.join(processed_path, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                        
                        # Убираем служебную информацию из начала файла
                        if "=" * 60 in text:
                            text = text.split("=" * 60, 1)[-1].strip()
                        
                        original_name = file.replace('.txt', '')
                        self.regulations_texts[original_name] = text
                        print(f"✅ Загружен: {original_name} ({len(text)} символов)")
                        
                    except Exception as e:
                        print(f"❌ Ошибка загрузки {file}: {e}")
                
                if self.regulations_texts:
                    print(f"✅ Загружено {len(self.regulations_texts)} обработанных регламентов")
                    return True
        
        # Если нет обработанных файлов, обрабатываем исходные
        if not os.path.exists(self.regulations_path):
            print(f"❌ Папка {self.regulations_path} не найдена!")
            print("💡 Сначала запустите: python universal_processor.py")
            return False
        
        print("🔄 Обработка исходных регламентов...")
        print("💡 Рекомендуем сначала запустить: python universal_processor.py")
        
        files = [f for f in os.listdir(self.regulations_path) 
                if f.lower().endswith(('.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xml'))]
        
        if not files:
            print("❌ Нет файлов регламентов в папке!")
            return False
        
        print(f"📚 Найдено файлов: {len(files)}")
        
        for file in files:
            file_path = os.path.join(self.regulations_path, file)
            print(f"📄 Обработка: {file}")
            
            try:
                if file.lower().endswith('.pdf'):
                    text = self.smart_extract_text(file_path)
                elif file.lower().endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                else:
                    text = f"[Файл {file} требует предварительной обработки через universal_processor.py]"
                
                if text and len(text) > 50:
                    self.regulations_texts[file] = text
                    print(f"✅ Загружен: {file} ({len(text)} символов)")
                else:
                    print(f"⚠️ Мало данных в файле: {file}")
                    
            except Exception as e:
                print(f"❌ Ошибка загрузки {file}: {e}")
        
        print(f"✅ Загружено {len(self.regulations_texts)} регламентов")
        return len(self.regulations_texts) > 0

    def analyze_with_keywords(self, contract_text):
        """Простой анализ на основе ключевых слов"""
        print("🔍 Анализ на основе ключевых слов...")
        
        # Ключевые слова для поиска проблем
        sanctions_keywords = [
            'санкци', 'запрет', 'ограничен', 'блокир', 'заморож',
            'черный список', 'персона нон грата', 'эмбарго'
        ]
        
        currency_keywords = [
            'доллар', 'евро', 'фунт', 'юань', 'валют', 'девиз',
            'курс валют', 'валютн', 'экспорт', 'импорт'
        ]
        
        contract_keywords = [
            'договор', 'контракт', 'соглашен', 'сторон', 'покупател',
            'продавец', 'поставщик', 'заказчик', 'подрядчик'
        ]
        
        risk_keywords = [
            'оружие', 'военн', 'двойного назначения', 'технологи',
            'программное обеспечение', 'криптограф', 'ядерн'
        ]
        
        text_lower = contract_text.lower()
        
        # Поиск ключевых слов
        found_sanctions = [kw for kw in sanctions_keywords if kw in text_lower]
        found_currency = [kw for kw in currency_keywords if kw in text_lower]
        found_contract = [kw for kw in contract_keywords if kw in text_lower]
        found_risks = [kw for kw in risk_keywords if kw in text_lower]
        
        # Анализ результатов
        analysis = {
            'is_contract': len(found_contract) > 0,
            'has_sanctions_mentions': len(found_sanctions) > 0,
            'has_currency_operations': len(found_currency) > 0,
            'has_risk_items': len(found_risks) > 0,
            'found_keywords': {
                'sanctions': found_sanctions,
                'currency': found_currency,
                'contract': found_contract,
                'risks': found_risks
            }
        }
        
        return analysis

    def analyze_with_llama(self, contract_text):
        """Анализ с использованием LlamaIndex"""
        if not LLAMA_INDEX_AVAILABLE:
            print("⚠️ LlamaIndex не доступен, используем упрощенный анализ")
            return None
        
        print(f"🤖 Анализ с использованием {self.model_name}...")
        
        try:
            # Настройка более легкой модели
            Settings.llm = Ollama(
                model=self.model_name, 
                request_timeout=180.0,
                temperature=0.1,
                num_ctx=4096,  # Уменьшаем контекст для экономии памяти
                num_predict=512  # Ограничиваем длину ответа
            )
            
            # Подготавливаем сокращенный контекст с регламентами
            regulations_context = "\n\n".join([
                f"=== {filename} ===\n{text[:2000]}"  # Сильно ограничиваем размер каждого регламента
                for filename, text in list(self.regulations_texts.items())[:5]  # Только первые 5 регламентов
            ])
            
            # Создаем короткий документ для анализа
            analysis_prompt = f"""
РЕГЛАМЕНТЫ (краткий обзор):
{regulations_context[:3000]}

ДОГОВОР:
{contract_text[:]}

ЗАДАЧА: Быстро проанализируй договор:
1. РЕШЕНИЕ: ПРИНЯТЬ/ОТКАЗАТЬ
2. ПРИЧИНА: главная причина решения
3. РИСКИ: основные риски

Ответ должен быть коротким и конкретным.
"""
            
            # Создаем индекс
            doc = Document(text=analysis_prompt)
            index = VectorStoreIndex.from_documents([doc])
            
            # Запрашиваем анализ
            query_engine = index.as_query_engine(
                similarity_top_k=2,  # Уменьшаем количество источников
                response_mode="compact"  # Компактный режим
            )
            
            response = query_engine.query(
                "Дай краткое заключение о договоре"
            )
            
            return str(response)
            
        except Exception as e:
            print(f"❌ Ошибка LLM анализа: {e}")
            print("💡 Попробуйте использовать более легкую модель: ollama pull llama3.2:3b")
            return None

    def generate_report(self, contract_path, contract_text, keyword_analysis, llm_analysis=None):
        """Создаем итоговый отчет"""
        report = {
            'contract_file': os.path.basename(contract_path),
            'analysis_date': datetime.now().isoformat(),
            'text_length': len(contract_text),
            'extraction_method': 'OCR' if 'OCR' in contract_text else 'Standard',
            'keyword_analysis': keyword_analysis,
            'llm_analysis': llm_analysis,
            'recommendation': 'ТРЕБУЕТ_ПРОВЕРКИ'  # По умолчанию
        }
        
        # Определяем рекомендацию на основе анализа
        if keyword_analysis['has_sanctions_mentions'] or keyword_analysis['has_risk_items']:
            report['recommendation'] = 'ОТКАЗАТЬ'
            report['reason'] = 'Обнаружены упоминания санкций или товаров повышенного риска'
        elif keyword_analysis['is_contract'] and keyword_analysis['has_currency_operations']:
            report['recommendation'] = 'ТРЕБУЕТ_ДОПОЛНИТЕЛЬНОЙ_ПРОВЕРКИ'
            report['reason'] = 'Договор содержит валютные операции - требуется детальная проверка'
        elif keyword_analysis['is_contract']:
            report['recommendation'] = 'МОЖНО_РАССМОТРЕТЬ'
            report['reason'] = 'Базовые проверки пройдены, но требуется экспертная оценка'
    def create_summary_report(self, report, summary_file):
        """Создает читаемый сводный отчет"""
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("СВОДНЫЙ ОТЧЕТ АНАЛИЗА ДОГОВОРА\n")
            f.write("=" * 50 + "\n\n")
            
            # Основная информация
            f.write(f"Файл договора: {report['contract_file']}\n")
            f.write(f"Дата анализа: {report['analysis_date']}\n")
            f.write(f"Размер текста: {report['text_length']} символов\n")
            f.write(f"Метод извлечения: {report['extraction_method']}\n")
            f.write(f"Файл с текстом: {report.get('contract_text_file', 'Не указан')}\n\n")
            
            # Решение
            f.write("РЕШЕНИЕ И РЕКОМЕНДАЦИЯ\n")
            f.write("-" * 30 + "\n")
            f.write(f"Рекомендация: {report['recommendation']}\n")
            f.write(f"Причина: {report.get('reason', 'Не указана')}\n\n")
            
            # Анализ ключевых слов
            kw = report['keyword_analysis']
            f.write("АНАЛИЗ КЛЮЧЕВЫХ СЛОВ\n")
            f.write("-" * 30 + "\n")
            f.write(f"Является договором: {'Да' if kw['is_contract'] else 'Нет'}\n")
            f.write(f"Упоминания санкций: {'Да' if kw['has_sanctions_mentions'] else 'Нет'}\n")
            f.write(f"Валютные операции: {'Да' if kw['has_currency_operations'] else 'Нет'}\n")
            f.write(f"Товары риска: {'Да' if kw['has_risk_items'] else 'Нет'}\n\n")
            
            # Найденные ключевые слова
            found = kw['found_keywords']
            if any(found.values()):
                f.write("НАЙДЕННЫЕ КЛЮЧЕВЫЕ СЛОВА\n")
                f.write("-" * 30 + "\n")
                for category, words in found.items():
                    if words:
                        f.write(f"{category.upper()}: {', '.join(words)}\n")
                f.write("\n")
            
            # LLM анализ
            if report.get('llm_analysis'):
                f.write("АНАЛИЗ ИСКУССТВЕННОГО ИНТЕЛЛЕКТА\n")
                f.write("-" * 30 + "\n")
                f.write(f"{report['llm_analysis']}\n\n")
            
            # Превью текста
            if report.get('contract_preview'):
                f.write("ПРЕВЬЮ ТЕКСТА ДОГОВОРА\n")
                f.write("-" * 30 + "\n")
                f.write(f"{report['contract_preview']}\n")
                if report['text_length'] > 1000:
                    f.write(f"\n[Показано 1000 из {report['text_length']} символов]\n")
                f.write("\n")
            
            f.write("=" * 50 + "\n")
            f.write("Конец отчета\n")

    def analyze_contract(self, contract_path):
        """Полный анализ договора"""
        print(f"\n{'='*60}")
        print(f"📋 АНАЛИЗ ДОГОВОРА: {os.path.basename(contract_path)}")
        print(f"{'='*60}")
        
        # 1. Извлекаем текст
        contract_text = self.smart_extract_text(contract_path)
        if not contract_text:
            print("❌ Не удалось извлечь текст из договора")
            return None
        
        # Сохраняем извлеченный текст договора
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        contract_name = os.path.splitext(os.path.basename(contract_path))[0]
        
        # Сохраняем полный текст договора
        contract_text_file = f"contract_text_{contract_name}_{timestamp}.txt"
        with open(contract_text_file, 'w', encoding='utf-8') as f:
            f.write(f"ИЗВЛЕЧЕННЫЙ ТЕКСТ ДОГОВОРА\n")
            f.write(f"{'='*50}\n")
            f.write(f"Исходный файл: {os.path.basename(contract_path)}\n")
            f.write(f"Дата извлечения: {datetime.now().isoformat()}\n")
            f.write(f"Размер текста: {len(contract_text)} символов\n")
            f.write(f"Метод извлечения: {'OCR' if 'Страница' in contract_text else 'Стандартный'}\n")
            f.write(f"{'='*50}\n\n")
            f.write(contract_text)
        
        print(f"💾 Текст договора сохранен в: {contract_text_file}")
        
        # Показываем превью текста (первые 1000 символов)
        print(f"\n📄 ПРЕВЬЮ ТЕКСТА ДОГОВОРА:")
        print("-" * 50)
        preview_text = contract_text[:1000]
        print(preview_text)
        if len(contract_text) > 1000:
            print("...")
            print(f"[Показано {len(preview_text)} из {len(contract_text)} символов]")
        print("-" * 50)
        
        # 2. Анализ ключевых слов
        keyword_analysis = self.analyze_with_keywords(contract_text)
        
        # 3. LLM анализ (если доступен)
        llm_analysis = None
        if LLAMA_INDEX_AVAILABLE and self.regulations_texts:
            try:
                llm_analysis = self.analyze_with_llama(contract_text)
            except Exception as e:
                print(f"⚠️ LLM анализ недоступен: {e}")
                llm_analysis = f"Ошибка LLM: {str(e)}"
        
        # 4. Генерируем отчет (с защитой от ошибок)
        try:
            report = self.generate_report(contract_path, contract_text, keyword_analysis, llm_analysis)
        except Exception as e:
            print(f"⚠️ Ошибка создания отчета: {e}")
            # Создаем минимальный отчет
            report = {
                'contract_file': os.path.basename(contract_path),
                'analysis_date': timestamp,
                'text_length': len(contract_text),
                'extraction_method': 'OCR' if 'Страница' in contract_text else 'Стандартный',
                'keyword_analysis': keyword_analysis,
                'llm_analysis': llm_analysis,
                'recommendation': 'ТРЕБУЕТ_ПРОВЕРКИ',
                'reason': 'Ошибка в процессе анализа'
            }
        
        # Убеждаемся что report не None
        if report is None:
            report = {
                'contract_file': os.path.basename(contract_path),
                'analysis_date': timestamp,
                'text_length': len(contract_text),
                'extraction_method': 'OCR' if 'Страница' in contract_text else 'Стандартный',
                'keyword_analysis': keyword_analysis,
                'llm_analysis': llm_analysis,
                'recommendation': 'ОШИБКА_АНАЛИЗА',
                'reason': 'Не удалось создать отчет'
            }
        
        # Добавляем информацию о сохраненном файле в отчет
        report['contract_text_file'] = contract_text_file
        report['contract_preview'] = preview_text
        
        # 5. Выводим результаты
        try:
            self.print_analysis_results(report)
        except Exception as e:
            print(f"⚠️ Ошибка вывода результатов: {e}")
            # Простой вывод
            print(f"✅ Анализ завершен")
            print(f"📄 Файл: {report['contract_file']}")
            print(f"💡 Рекомендация: {report.get('recommendation', 'НЕ_ОПРЕДЕЛЕНО')}")
        
        # 6. Сохраняем отчет
        try:
            report_file = f"contract_analysis_{contract_name}_{timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"📄 Отчет сохранен в: {report_file}")
        except Exception as e:
            print(f"⚠️ Ошибка сохранения отчета: {e}")
        
        # 7. Создаем сводный отчет
        try:
            summary_file = f"contract_summary_{contract_name}_{timestamp}.txt"
            self.create_summary_report(report, summary_file)
            print(f"📋 Сводный отчет: {summary_file}")
        except Exception as e:
            print(f"⚠️ Ошибка создания сводного отчета: {e}")
        
        return report

    def print_analysis_results(self, report):
        """Красивый вывод результатов анализа"""
        print(f"\n🎯 РЕЗУЛЬТАТЫ АНАЛИЗА:")
        print("=" * 50)
        
        # Рекомендация
        rec = report['recommendation']
        if rec == 'ОТКАЗАТЬ':
            print(f"❌ РЕКОМЕНДАЦИЯ: {rec}")
        elif rec == 'МОЖНО_РАССМОТРЕТЬ':
            print(f"✅ РЕКОМЕНДАЦИЯ: {rec}")
        else:
            print(f"⚠️ РЕКОМЕНДАЦИЯ: {rec}")
        
        print(f"📝 ОБОСНОВАНИЕ: {report.get('reason', 'Не указано')}")
        
        # Ключевые слова
        kw = report['keyword_analysis']
        print(f"\n📊 АНАЛИЗ КЛЮЧЕВЫХ СЛОВ:")
        print(f"  Договор: {'✅' if kw['is_contract'] else '❌'}")
        print(f"  Санкции: {'⚠️' if kw['has_sanctions_mentions'] else '✅'}")
        print(f"  Валютные операции: {'⚠️' if kw['has_currency_operations'] else '✅'}")
        print(f"  Товары риска: {'❌' if kw['has_risk_items'] else '✅'}")
        
        # Найденные ключевые слова
        found = kw['found_keywords']
        if any(found.values()):
            print(f"\n🔍 НАЙДЕННЫЕ КЛЮЧЕВЫЕ СЛОВА:")
            for category, words in found.items():
                if words:
                    print(f"  {category}: {words}")
        
        # LLM анализ
        if report.get('llm_analysis'):
            print(f"\n🤖 АНАЛИЗ ИСКУССТВЕННОГО ИНТЕЛЛЕКТА:")
            print("-" * 30)
            print(report['llm_analysis'])

def main(pdf_file):
    parser = argparse.ArgumentParser(description="Анализатор договоров с OCR поддержкой")
    parser.add_argument("pdf_file", help="Путь к PDF файлу договора")
    parser.add_argument("--regulations", default="./regulations", help="Папка с регламентами")
    
    args = parser.parse_args()
    args.pdf_file = os.path.abspath(pdf_file)
    print("🚀 Запуск анализатора договоров с OCR")
    print(f"📁 Файл: {args.pdf_file}")
    print(f"📚 Регламенты: {args.regulations}")
    
    # Создаем анализатор
    analyzer = OCRContractAnalyzer(regulations_path=args.regulations)
    
    # Загружаем регламенты
    print("\n🔄 Загрузка регламентов...")
    if not analyzer.load_regulations():
        print("⚠️ Не удалось загрузить регламенты, анализ будет упрощенным")
    
    # Анализируем договор
    result = analyzer.analyze_contract(args.pdf_file)
    
    if result:
        print(f"\n✅ Анализ завершен успешно!")
        print(f"💡 Рекомендация: {result['recommendation']}")
        return result['recommendation']
    else:
        print(f"\n❌ Анализ завершен с ошибками")
        sys.exit(1)

if __name__ == "__main__":
    main()

__all__ = ['main']  