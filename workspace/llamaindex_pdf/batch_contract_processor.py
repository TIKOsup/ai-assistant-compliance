# batch_contract_processor.py
import os
import sys
import argparse
from datetime import datetime
import json
from keyword_only_analyzer import KeywordOnlyAnalyzer

class BatchContractProcessor:
    def __init__(self, contracts_folder, cache_folder="./processed_contracts", regulations_folder="./regulations"):
        self.contracts_folder = contracts_folder
        self.cache_folder = cache_folder
        self.regulations_folder = regulations_folder
        self.analyzer = KeywordOnlyAnalyzer(regulations_folder, cache_folder)
        self.results = []
        
    def find_contract_files(self):
        """Находит все PDF файлы договоров"""
        if not os.path.exists(self.contracts_folder):
            print(f"❌ Папка {self.contracts_folder} не найдена!")
            return []
        
        pdf_files = []
        for root, dirs, files in os.walk(self.contracts_folder):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        return pdf_files
    
    def process_all_contracts(self, force_reprocess=False):
        """Обрабатывает все договоры в папке"""
        contracts = self.find_contract_files()
        
        if not contracts:
            print("❌ Не найдено PDF файлов для обработки")
            return []
        
        print(f"🚀 Найдено {len(contracts)} договоров для обработки")
        print("=" * 60)
        
        for i, contract_path in enumerate(contracts, 1):
            print(f"\n📄 [{i}/{len(contracts)}] {os.path.basename(contract_path)}")
            
            try:
                # Проверяем есть ли уже результат анализа
                if not force_reprocess and self.has_recent_analysis(contract_path):
                    print("✅ Уже обработан недавно, пропускаем...")
                    continue
                
                # Анализируем договор
                result = self.analyzer.analyze_contract(contract_path)
                
                if result:
                    self.results.append(result)
                    print(f"✅ Обработан: {result['recommendation']['decision']}")
                else:
                    print("❌ Ошибка обработки")
                    
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        # Создаем сводный отчет
        self.create_summary_report()
        
        return self.results
    
    def has_recent_analysis(self, contract_path):
        """Проверяет есть ли недавний анализ договора"""
        contract_name = os.path.splitext(os.path.basename(contract_path))[0]
        
        # Ищем файлы анализа
        for file in os.listdir('.'):
            if file.startswith(f"analysis_{contract_name}_") and file.endswith('.json'):
                # Проверяем дату анализа
                try:
                    file_time = os.path.getmtime(file)
                    contract_time = os.path.getmtime(contract_path)
                    
                    if file_time > contract_time:  # Анализ новее исходного файла
                        return True
                except:
                    pass
        
        return False
    
    def create_summary_report(self):
        """Создает сводный отчет по всем договорам"""
        if not self.results:
            print("📄 Нет результатов для сводного отчета")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = f"batch_analysis_summary_{timestamp}.json"
        
        # Подготавливаем статистику
        decisions = {}
        risk_levels = {}
        total_contracts = len(self.results)
        
        for result in self.results:
            decision = result['recommendation']['decision']
            risk_level = result['recommendation']['risk_level']
            
            decisions[decision] = decisions.get(decision, 0) + 1
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
        
        # Создаем сводный отчет
        summary = {
            'processing_date': timestamp,
            'total_contracts': total_contracts,
            'contracts_folder': self.contracts_folder,
            'statistics': {
                'decisions': decisions,
                'risk_levels': risk_levels
            },
            'detailed_results': self.results
        }
        
        # Сохраняем JSON отчет
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # Создаем текстовый отчет
        text_report_file = f"batch_analysis_report_{timestamp}.txt"
        self.create_text_report(summary, text_report_file)
        
        print(f"\n📊 СВОДНЫЙ ОТЧЕТ:")
        print("=" * 60)
        print(f"📄 Обработано договоров: {total_contracts}")
        print(f"\n📋 Решения:")
        for decision, count in decisions.items():
            percentage = (count / total_contracts) * 100
            print(f"   {decision}: {count} ({percentage:.1f}%)")
        
        print(f"\n⚡ Уровни рисков:")
        for risk_level, count in risk_levels.items():
            percentage = (count / total_contracts) * 100
            print(f"   {risk_level}: {count} ({percentage:.1f}%)")
        
        print(f"\n💾 Отчеты сохранены:")
        print(f"   📊 JSON: {summary_file}")
        print(f"   📄 Текстовый: {text_report_file}")
    
    def create_text_report(self, summary, filename):
        """Создает читаемый текстовый отчет"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("СВОДНЫЙ ОТЧЕТ ПО АНАЛИЗУ ДОГОВОРОВ\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Дата обработки: {summary['processing_date']}\n")
            f.write(f"Папка договоров: {summary['contracts_folder']}\n")
            f.write(f"Всего обработано: {summary['total_contracts']} договоров\n\n")
            
            # Статистика решений
            f.write("СТАТИСТИКА РЕШЕНИЙ:\n")
            f.write("-" * 30 + "\n")
            for decision, count in summary['statistics']['decisions'].items():
                percentage = (count / summary['total_contracts']) * 100
                f.write(f"{decision}: {count} ({percentage:.1f}%)\n")
            
            f.write("\nСТАТИСТИКА РИСКОВ:\n")
            f.write("-" * 30 + "\n")
            for risk_level, count in summary['statistics']['risk_levels'].items():
                percentage = (count / summary['total_contracts']) * 100
                f.write(f"{risk_level}: {count} ({percentage:.1f}%)\n")
            
            # Детальные результаты
            f.write("\n\nДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:\n")
            f.write("=" * 50 + "\n")
            
            for i, result in enumerate(summary['detailed_results'], 1):
                f.write(f"\n{i}. {result['contract_file']}\n")
                f.write(f"   Решение: {result['recommendation']['decision']}\n")
                f.write(f"   Риск: {result['recommendation']['risk_level']}\n")
                f.write(f"   Причина: {result['recommendation']['reason']}\n")
                
                if result['recommendation']['critical_risks']:
                    f.write(f"   Критические риски:\n")
                    for risk in result['recommendation']['critical_risks']:
                        f.write(f"     • {risk}\n")
                
                if result['recommendation']['recommendations']:
                    f.write(f"   Рекомендации:\n")
                    for rec in result['recommendation']['recommendations'][:3]:  # Первые 3
                        f.write(f"     • {rec}\n")
    
    def generate_dashboard_data(self):
        """Генерирует данные для дашборда"""
        if not self.results:
            return None
        
        dashboard_data = {
            'summary': {
                'total': len(self.results),
                'high_risk': sum(1 for r in self.results if r['recommendation']['risk_level'] in ['КРИТИЧЕСКИЙ', 'ВЫСОКИЙ']),
                'rejected': sum(1 for r in self.results if 'ОТКАЗАТЬ' in r['recommendation']['decision']),
                'approved': sum(1 for r in self.results if 'МОЖНО_РАССМОТРЕТЬ' in r['recommendation']['decision'])
            },
            'risk_distribution': {},
            'decision_distribution': {},
            'problem_contracts': []
        }
        
        # Заполняем распределения
        for result in self.results:
            risk = result['recommendation']['risk_level']
            decision = result['recommendation']['decision']
            
            dashboard_data['risk_distribution'][risk] = dashboard_data['risk_distribution'].get(risk, 0) + 1
            dashboard_data['decision_distribution'][decision] = dashboard_data['decision_distribution'].get(decision, 0) + 1
            
            # Проблемные договоры
            if result['recommendation']['risk_score'] >= 3:
                dashboard_data['problem_contracts'].append({
                    'file': result['contract_file'],
                    'decision': result['recommendation']['decision'],
                    'risk_score': result['recommendation']['risk_score'],
                    'critical_risks': result['recommendation']['critical_risks']
                })
        
        # Сохраняем данные для дашборда
        dashboard_file = f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
        
        print(f"📊 Данные дашборда: {dashboard_file}")
        return dashboard_data

def main():
    parser = argparse.ArgumentParser(description="Пакетная обработка договоров")
    parser.add_argument("contracts_folder", help="Папка с PDF договорами")
    parser.add_argument("--cache", default="./processed_contracts", help="Папка для кэша")
    parser.add_argument("--regulations", default="./regulations", help="Папка с регламентами")
    parser.add_argument("--force", action="store_true", help="Принудительно переобработать все файлы")
    parser.add_argument("--dashboard", action="store_true", help="Создать данные для дашборда")
    
    args = parser.parse_args()
    
    print("🚀 Пакетная обработка договоров")
    print(f"📁 Папка договоров: {args.contracts_folder}")
    print(f"💾 Кэш: {args.cache}")
    print(f"📚 Регламенты: {args.regulations}")
    
    processor = BatchContractProcessor(
        contracts_folder=args.contracts_folder,
        cache_folder=args.cache,
        regulations_folder=args.regulations
    )
    
    # Обрабатываем все договоры
    results = processor.process_all_contracts(force_reprocess=args.force)
    
    if results:
        print(f"\n✅ Обработка завершена: {len(results)} договоров")
        
        # Создаем дашборд если нужно
        if args.dashboard:
            processor.generate_dashboard_data()
    else:
        print("\n❌ Нет результатов обработки")

if __name__ == "__main__":
    main()