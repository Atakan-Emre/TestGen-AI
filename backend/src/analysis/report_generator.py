import json
from pathlib import Path
from datetime import datetime

class ReportGenerator:
    def __init__(self, output_dir="data/output/analysis"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_report(self, analysis_results):
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(analysis_results),
            "details": analysis_results,
            "recommendations": self._generate_recommendations(analysis_results)
        }
        
        self._save_report(report)
        return report
        
    def _generate_summary(self, results):
        total = len(results)
        
        # JSON başarısı: Zorunlu alanlar tam olan senaryolar
        valid_json = sum(1 for r in results 
                        if r["json_validation"].get("valid", False))
        
        # Senaryo başarısı: Tüm zorunlu alanları içeren ve formatı doğru olan senaryolar
        valid_scenario = sum(1 for r in results 
                            if r["scenario_validation"].get("valid", False) and 
                            not r["scenario_validation"].get("missing_required", []))
        
        # Hata mesajı başarısı: Doğru formatta hata mesajı içeren senaryolar
        valid_errors = sum(1 for r in results 
                          if r["error_validation"].get("valid", False))
        
        return {
            "total_cases": total,
            "valid_cases": {
                "json": valid_json,
                "scenario": valid_scenario,
                "errors": valid_errors
            },
            "success_rate": {
                "json": valid_json / total if total > 0 else 0,
                "scenario": valid_scenario / total if total > 0 else 0,
                "errors": valid_errors / total if total > 0 else 0
            },
            "issues": self._get_common_issues(results)
        }
        
    def _generate_recommendations(self, results):
        """Analiz sonuçlarına göre öneriler oluştur"""
        recommendations = []
        
        # JSON yapısı önerileri
        json_issues = self._analyze_json_issues(results)
        if json_issues["missing_fields"] or json_issues["extra_fields"]:
            recommendations.append({
                "type": "json_structure",
                "issues": json_issues,
                "suggestion": "JSON yapısını düzeltmek için şu alanları kontrol edin"
            })
            
        # Senaryo önerileri
        scenario_issues = self._analyze_scenario_issues(results)
        if scenario_issues["missing_required"]:
            recommendations.append({
                "type": "test_scenario",
                "issues": scenario_issues,
                "suggestion": "Test senaryolarını iyileştirmek için şu noktalara dikkat edin"
            })
            
        # Hata mesajı önerileri
        error_patterns = self._analyze_error_patterns(results)
        if error_patterns:
            recommendations.append({
                "type": "error_messages",
                "patterns": error_patterns,
                "suggestion": "Hata mesajlarını standardize etmek için şu kalıpları kullanın"
            })
            
        return recommendations
        
    def _save_report(self, report):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"analysis_report_{timestamp}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False) 

    def _analyze_json_issues(self, results):
        """JSON yapısındaki sorunları analiz et"""
        issues = {
            "missing_fields": {},
            "extra_fields": {},
            "invalid_formats": {}
        }
        
        for result in results:
            json_validation = result.get("json_validation", {})
            
            # Eksik alanları say
            for field in json_validation.get("missing_keys", []):
                issues["missing_fields"][field] = issues["missing_fields"].get(field, 0) + 1
                
            # Fazla alanları say
            for field in json_validation.get("extra_keys", []):
                issues["extra_fields"][field] = issues["extra_fields"].get(field, 0) + 1
                
        return issues

    def _analyze_scenario_issues(self, results):
        """Test senaryosu sorunlarını analiz et"""
        issues = {
            "missing_required": {},
            "invalid_formats": {},
            "validation_errors": {}
        }
        
        for result in results:
            scenario_validation = result.get("scenario_validation", {})
            
            # Eksik zorunlu alanları say
            for field in scenario_validation.get("missing_required", []):
                issues["missing_required"][field] = issues["missing_required"].get(field, 0) + 1
                
            # Hata mesajlarını kontrol et
            error_validation = result.get("error_validation", {})
            if not error_validation.get("valid", False):
                msg = error_validation.get("message", "")
                issues["validation_errors"][msg] = issues["validation_errors"].get(msg, 0) + 1
                
        return issues

    def _analyze_error_patterns(self, results):
        """Hata mesajı kalıplarını analiz et"""
        patterns = {}
        
        for result in results:
            error_validation = result.get("error_validation", {})
            msg = error_validation.get("message", "")
            
            if msg:
                patterns[msg] = patterns.get(msg, 0) + 1
                
        return patterns

    def _get_common_issues(self, results):
        """En sık karşılaşılan sorunları belirle"""
        return {
            "json": self._analyze_json_issues(results),
            "scenario": self._analyze_scenario_issues(results),
            "errors": self._analyze_error_patterns(results)
        }