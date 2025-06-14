# langchain_ollama_analyzer.py
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

class LangChainOllamaAnalyzer:
    def __init__(self, regulations_path="./regulations", model_name="saiga:7b-instruct"):
        self.regulations_path = regulations_path
        self.model_name = model_name
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        
        print(f"🚀 Инициализация LangChain + Ollama анализатора")
        print(f"🤖 Instruct модель: {model_name}")
        
        self.setup_embeddings()
        self.setup_llm()
    
    def setup_embeddings(self):
        """Настройка многоязычных эмбеддингов"""
        print("🔧 Настройка многоязычных эмбеддингов...")
        try:
            # Русскоязычные эмбеддинги
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            print("✅ Многоязычные эмбеддинги настроены")
        except Exception as e:
            print(f"⚠️ Ошибка многоязычных эмбеддингов: {e}")
            # Fallback
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            print("✅ Стандартные эмбеддинги настроены")
    
    def setup_llm(self):
        """Настройка Ollama LLM"""
        print(f"🔧 Настройка Ollama модели: {self.model_name}")
        
        try:
            # Проверяем доступность Ollama
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code != 200:
                print("❌ Ollama не запущен. Запустите: ollama serve")
                sys.exit(1)
            
            # Проверяем наличие модели
            models = [m['name'] for m in response.json().get('models', [])]
            if self.model_name not in models:
                print(f"⚠️ Модель {self.model_name} не найдена")
                print(f"📥 Загружаем модель...")
                os.system(f"ollama pull {self.model_name}")
            
            # Создаем LLM
            callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
            
            self.llm = Ollama(
                model=self.model_name,
                callback_manager=callback_manager,
                temperature=0.1,
                num_ctx=4096,
                num_predict=1024,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1
            )
            
            print("✅ Ollama LLM настроен")
            
        except Exception as e:
            print(f"❌ Ошибка настройки Ollama: {e}")
            print("💡 Убедитесь что Ollama запущен: ollama serve")
            sys.exit(1)
    
    def extract_text_with_ocr(self, pdf_path):
        """OCR извлечение текста (оптимизированное)"""
        print(f"🔍 OCR обработка: {os.path.basename(pdf_path)}")
        
        try:
            # Конвертируем с меньшим DPI для скорости
            images = convert_from_path(pdf_path, dpi=200, thread_count=4)
            all_text = []
            
            for i, image in enumerate(images):
                print(f"🔤 OCR страница {i+1}/{len(images)}...")
                
                # Оптимизированные настройки OCR
                custom_config = r'--oem 3 --psm 6 -l rus+eng'
                text = pytesseract.image_to_string(image, config=custom_config)
                
                if text.strip():
                    all_text.append(f"=== Страница {i+1} ===\n{text}")
                
                # Освобождаем память
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
    
    def load_regulations(self):
        """Загрузка регламентов в векторную базу"""
        print("📚 Загрузка регламентов...")
        
        # Проверяем существующую базу
        if os.path.exists("./chroma_db"):
            try:
                self.vectorstore = Chroma(
                    persist_directory="./chroma_db",
                    embedding_function=self.embeddings
                )
                print("✅ Загружена существующая векторная база")
                return True
            except Exception as e:
                print(f"⚠️ Ошибка загрузки существующей базы: {e}")
                print("🔄 Создаем новую базу...")
        
        documents = []
        processed_path = "./processed_regulations"
        
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
                    
                    if len(content.strip()) > 100:  # Только содержательные документы
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": file.replace('.txt', ''),
                                "type": "regulation",
                                "length": len(content)
                            }
                        )
                        documents.append(doc)
                        print(f"✅ Загружен: {file} ({len(content)} символов)")
                    
                except Exception as e:
                    print(f"❌ Ошибка загрузки {file}: {e}")
        
        if not documents:
            print("⚠️ Регламенты не найдены")
            return False
        
        # Разбиваем документы на чанки
        print("🔪 Разбивка документов на фрагменты...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Увеличиваем размер чанка
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        splits = text_splitter.split_documents(documents)
        print(f"📝 Создано {len(splits)} фрагментов")
        
        # Создаем векторную базу
        print("🗄️ Создание векторной базы...")
        try:
            self.vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                persist_directory="./chroma_db"
            )
            self.vectorstore.persist()
            print("✅ Векторная база создана и сохранена")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания векторной базы: {e}")
            return False
    
    def create_analysis_chain(self):
        """Создание цепочки анализа с исправленным retriever"""
        if not self.vectorstore:
            print("❌ Векторная база не готова")
            return None
        
        # Специальный промпт для Instruct модели
        prompt_template = """Ты - ведущий эксперт по корпоративному праву и санкционному законодательству Российской Федерации.

КОНТЕКСТ ИЗ НОРМАТИВНЫХ ДОКУМЕНТОВ:
{context}

АНАЛИЗИРУЕМЫЙ ДОГОВОР:
{question}

ТВОЯ ЗАДАЧА:
Проведи детальный правовой анализ договора на соответствие российскому и международному законодательству.

ОБЯЗАТЕЛЬНЫЕ ПРОВЕРКИ:
1. Санкционные списки: США (OFAC), ЕС, Великобритания, ООН
2. Валютное законодательство: ФЗ-173 "О валютном регулировании"
3. Товары двойного назначения: постановления Правительства РФ
4. Экспортный контроль: ФЗ-171 "Об экспортном контроле"
5. Противодействие отмыванию денег: ФЗ-115

СТРУКТУРА ОТВЕТА:
🎯 ИТОГОВОЕ РЕШЕНИЕ: [ПРИНЯТЬ/ОТКАЗАТЬ/ТРЕБУЕТ_ДОПОЛНИТЕЛЬНОЙ_ПРОВЕРКИ]

📋 ПРАВОВОЕ ОБОСНОВАНИЕ:
[Подробное объяснение со ссылками на конкретные статьи законов и пункты регламентов]

⚠️ ВЫЯВЛЕННЫЕ РИСКИ:
[Конкретные риски с указанием степени критичности]

💡 РЕКОМЕНДАЦИИ:
[Пошаговые действия для снижения рисков]

📚 ИСПОЛЬЗОВАННЫЕ ИСТОЧНИКИ:
[Ссылки на конкретные нормативные документы]

ВАЖНО: Отвечай исключительно на русском языке. Будь максимально конкретным и ссылайся на точные пункты нормативных актов.
"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        try:
            # Создаем retriever с базовыми параметрами
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}  # Только базовые параметры
            )
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={"prompt": prompt},
                return_source_documents=True
            )
            
            print("✅ Цепочка правового анализа создана")
            return qa_chain
            
        except Exception as e:
            print(f"❌ Ошибка создания цепочки: {e}")
            print("🔄 Попытка создания упрощенной цепочки...")
            
            # Fallback - создаем более простую цепочку
            try:
                retriever = self.vectorstore.as_retriever()
                qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=retriever,
                    return_source_documents=True
                )
                print("✅ Упрощенная цепочка создана")
                return qa_chain
            except Exception as e2:
                print(f"❌ Критическая ошибка: {e2}")
                return None
    
    def analyze_contract(self, contract_path):
        """Полный анализ договора"""
        print(f"\n{'='*80}")
        print(f"⚖️  LANGCHAIN + OLLAMA ПРАВОВОЙ АНАЛИЗ ДОГОВОРА")
        print(f"📄 Файл: {os.path.basename(contract_path)}")
        print(f"🤖 Модель: {self.model_name}")
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
            f.write(f"Анализатор: LangChain + Ollama ({self.model_name})\n")
            f.write(f"{'='*60}\n\n")
            f.write(contract_text)
        
        print(f"💾 Текст договора сохранен: {text_file}")
        
        # Показываем превью
        print(f"\n📄 ПРЕВЬЮ ДОГОВОРА:")
        print("-" * 60)
        preview = contract_text[:800]
        print(preview)
        if len(contract_text) > 800:
            print("...")
            print(f"[Показано 800 из {len(contract_text)} символов]")
        print("-" * 60)
        
        # 3. Загружаем регламенты в векторную базу
        if not self.load_regulations():
            print("⚠️ Продолжаем без регламентов - анализ будет ограниченным")
        
        # 4. Создаем цепочку анализа
        qa_chain = self.create_analysis_chain()
        if not qa_chain:
            print("❌ Не удалось создать цепочку анализа")
            return None
        
        # 5. Запускаем LLM анализ
        print("\n🤖 ЗАПУСК ПРАВОВОГО АНАЛИЗА С ИСПОЛЬЗОВАНИЕМ LLM...")
        print("=" * 60)
        
        try:
            # Подготавливаем запрос
            query = f"""
Проанализируй следующий договор на соответствие российскому и международному законодательству:

ТЕКСТ ДОГОВОРА:
{contract_text[:5000]}  # Первые 5000 символов

Особое внимание обрати на:
- Стороны договора и их статус
- Предмет договора и товары/услуги
- Валютные операции
- Географию операций
- Потенциальные санкционные риски
"""
            
            print("📡 Отправляем запрос к LLM...")
            result = qa_chain({"query": query})
            
            llm_response = result["result"]
            source_docs = result.get("source_documents", [])
            
            print("\n✅ LLM АНАЛИЗ ЗАВЕРШЕН")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ОШИБКА LLM АНАЛИЗА: {e}")
            llm_response = f"Ошибка анализа: {str(e)}"
            source_docs = []
        
        # 6. Формируем отчет
        report = {
            'contract_file': os.path.basename(contract_path),
            'contract_text_file': text_file,
            'analysis_date': timestamp,
            'text_length': len(contract_text),
            'analyzer': f"LangChain + Ollama",
            'model_name': self.model_name,
            'llm_analysis': llm_response,
            'source_documents': [
                {
                    'source': doc.metadata.get("source", "Unknown"),
                    'type': doc.metadata.get("type", "Unknown"),
                    'content_preview': doc.page_content[:200] + "..."
                }
                for doc in source_docs
            ],
            'regulations_used': len(source_docs),
            'extraction_method': 'OCR' if '=== Страница' in contract_text else 'Standard'
        }
        
        # 7. Выводим результаты
        self.print_results(report)
        
        # 8. Сохраняем отчеты
        # JSON отчет
        report_file = f"langchain_analysis_{contract_name}_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Читаемый отчет
        summary_file = f"legal_summary_{contract_name}_{timestamp}.txt"
        self.create_summary_report(report, summary_file)
        
        print(f"\n📄 JSON отчет: {report_file}")
        print(f"📋 Сводный отчет: {summary_file}")
        
        return summary_file
    
    def print_results(self, report):
        """Красивый вывод результатов"""
        print(f"\n⚖️  РЕЗУЛЬТАТЫ ПРАВОВОГО АНАЛИЗА:")
        print("=" * 70)
        
        print(f"🤖 Анализатор: {report['analyzer']}")
        print(f"📊 Модель: {report['model_name']}")
        print(f"📏 Размер текста: {report['text_length']:,} символов")
        print(f"🔍 Метод извлечения: {report['extraction_method']}")
        print(f"📚 Использовано источников: {report['regulations_used']}")
        
        if report['source_documents']:
            print(f"\n📋 ОСНОВНЫЕ ИСТОЧНИКИ:")
            for i, doc in enumerate(report['source_documents'][:3], 1):
                print(f"   {i}. {doc['source']}")
        
        print(f"\n📝 ЗАКЛЮЧЕНИЕ ЭКСПЕРТА:")
        print("=" * 40)
        print(report['llm_analysis'])
        print("=" * 40)
    
    def create_summary_report(self, report, summary_file):
        """Создание читаемого сводного отчета"""
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("СВОДНЫЙ ОТЧЕТ ПРАВОВОГО АНАЛИЗА ДОГОВОРА\n")
            f.write("=" * 60 + "\n\n")
            
            # Основная информация
            f.write("ОБЩАЯ ИНФОРМАЦИЯ\n")
            f.write("-" * 30 + "\n")
            f.write(f"Файл договора: {report['contract_file']}\n")
            f.write(f"Дата анализа: {report['analysis_date']}\n")
            f.write(f"Размер текста: {report['text_length']:,} символов\n")
            f.write(f"Анализатор: {report['analyzer']}\n")
            f.write(f"Модель: {report['model_name']}\n")
            f.write(f"Метод извлечения: {report['extraction_method']}\n")
            f.write(f"Файл с текстом: {report['contract_text_file']}\n\n")
            
            # Использованные источники
            if report['source_documents']:
                f.write("ИСПОЛЬЗОВАННЫЕ НОРМАТИВНЫЕ ИСТОЧНИКИ\n")
                f.write("-" * 40 + "\n")
                for i, doc in enumerate(report['source_documents'], 1):
                    f.write(f"{i}. {doc['source']}\n")
                f.write("\n")
            
            # Анализ LLM
            f.write("ЗАКЛЮЧЕНИЕ ЭКСПЕРТА\n")
            f.write("-" * 30 + "\n")
            f.write(f"{report['llm_analysis']}\n\n")
            
            # Техническая информация
            f.write("ТЕХНИЧЕСКАЯ ИНФОРМАЦИЯ\n")
            f.write("-" * 30 + "\n")
            f.write(f"Количество использованных источников: {report['regulations_used']}\n")
            f.write(f"Время анализа: {report['analysis_date']}\n")
            f.write("\n" + "=" * 60 + "\n")
            f.write("Конец отчета\n")

def mainLangChain(pdf_file):
    # parser = argparse.ArgumentParser(description="LangChain + Ollama правовой анализатор договоров")
    # parser.add_argument("pdf_file", help="PDF файл договора")
    # parser.add_argument("--model", default="saiga:7b", help="Модель Ollama")
    # parser.add_argument("--regulations", default="./regulations", help="Папка с регламентами")
    
    # args = parser.parse_args()
    
    print("🚀 Запуск LangChain + Ollama анализатора")
    print(f"📁 Файл: {pdf_file}")
    # print(f"🤖 Модель: {model}")
    
    analyzer = LangChainOllamaAnalyzer(
        # regulations_path=args.regulations,
        model_name='qwen2.5:3b-instruct'
    )
    
    result = analyzer.analyze_contract(pdf_file)
    
    if result:
        print(f"\n✅ Правовой анализ завершен успешно!")
        print(f"📋 Результаты сохранены в файлах отчетов"+result)
        return result
    else:
        print(f"\n❌ Анализ завершился с ошибками")

if __name__ == "__main__":
    mainLangChain()

__all__ = ['mainLangChain', 'LangChainOllamaAnalyzer']