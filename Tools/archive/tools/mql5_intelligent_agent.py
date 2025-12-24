#!/usr/bin/env python3
"""
MQL5 Intelligent Code Analysis Agent
Builds persistent knowledge database of MQL5 functions, signatures, and usage patterns
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Set

class MQL5IntelligentAgent:
    def __init__(self):
        self.db_path = "/home/renier/ProjectQuantum-Full/mql5_knowledge.db"
        self.project_root = Path("/mnt/c/DevCenter/MT5-Unified/MQL5-Development")
        self.initialize_database()
        
    def initialize_database(self):
        """Initialize SQLite database for persistent knowledge"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create tables for different types of knowledge
        self.cursor.executescript("""
            -- Built-in MQL5 functions
            CREATE TABLE IF NOT EXISTS mql5_builtin_functions (
                id INTEGER PRIMARY KEY,
                function_name TEXT UNIQUE,
                signature TEXT,
                return_type TEXT,
                parameters TEXT,
                description TEXT,
                category TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            );
            
            -- Project-specific functions
            CREATE TABLE IF NOT EXISTS project_functions (
                id INTEGER PRIMARY KEY,
                function_name TEXT,
                file_path TEXT,
                class_name TEXT,
                signature TEXT,
                return_type TEXT,
                parameters TEXT,
                line_number INTEGER,
                is_public BOOLEAN,
                is_static BOOLEAN,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Function call patterns
            CREATE TABLE IF NOT EXISTS function_calls (
                id INTEGER PRIMARY KEY,
                caller_file TEXT,
                caller_function TEXT,
                called_function TEXT,
                parameters_used TEXT,
                line_number INTEGER,
                context TEXT,
                is_correct BOOLEAN DEFAULT NULL,
                error_message TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Class structures
            CREATE TABLE IF NOT EXISTS class_definitions (
                id INTEGER PRIMARY KEY,
                class_name TEXT,
                file_path TEXT,
                parent_class TEXT,
                namespace_name TEXT,
                member_count INTEGER,
                public_methods INTEGER,
                private_methods INTEGER,
                includes TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Compilation errors and fixes
            CREATE TABLE IF NOT EXISTS compilation_fixes (
                id INTEGER PRIMARY KEY,
                error_type TEXT,
                error_message TEXT,
                original_code TEXT,
                fixed_code TEXT,
                file_path TEXT,
                line_number INTEGER,
                fix_applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_function_name ON mql5_builtin_functions(function_name);
            CREATE INDEX IF NOT EXISTS idx_project_functions ON project_functions(function_name, file_path);
            CREATE INDEX IF NOT EXISTS idx_function_calls ON function_calls(called_function);
            CREATE INDEX IF NOT EXISTS idx_class_name ON class_definitions(class_name);
        """)
        
        self.conn.commit()
        print(f"✅ Knowledge database initialized: {self.db_path}")
    
    def load_mql5_builtin_functions(self):
        """Load comprehensive MQL5 built-in function database"""
        builtin_functions = {
            # Array functions
            "ArrayResize": {
                "signature": "int ArrayResize(array[], int new_size, int reserve_size=0)",
                "return_type": "int",
                "parameters": "array[], int, int",
                "category": "Array",
                "description": "Changes array size"
            },
            "ArraySize": {
                "signature": "int ArraySize(const void& array[])",
                "return_type": "int", 
                "parameters": "const void&[]",
                "category": "Array",
                "description": "Returns array size"
            },
            "ArrayCopy": {
                "signature": "int ArrayCopy(void& dst_array[], const void& src_array[], int dst_start=0, int src_start=0, int count=WHOLE_ARRAY)",
                "return_type": "int",
                "parameters": "void&[], const void&[], int, int, int",
                "category": "Array",
                "description": "Copies array elements"
            },
            
            # String functions
            "StringFormat": {
                "signature": "string StringFormat(string format, ...)",
                "return_type": "string",
                "parameters": "string, ...",
                "category": "String",
                "description": "Formats string like printf"
            },
            "StringLen": {
                "signature": "int StringLen(string text)",
                "return_type": "int",
                "parameters": "string",
                "category": "String", 
                "description": "Returns string length"
            },
            "StringSubstr": {
                "signature": "string StringSubstr(string text, int start, int length=-1)",
                "return_type": "string",
                "parameters": "string, int, int",
                "category": "String",
                "description": "Extracts substring"
            },
            "StringCompare": {
                "signature": "int StringCompare(const string& str1, const string& str2, bool case_sensitive=true)",
                "return_type": "int",
                "parameters": "const string&, const string&, bool",
                "category": "String",
                "description": "Compares two strings"
            },
            
            # Math functions
            "MathMax": {
                "signature": "double MathMax(double value1, double value2)",
                "return_type": "double",
                "parameters": "double, double", 
                "category": "Math",
                "description": "Returns maximum value"
            },
            "MathMin": {
                "signature": "double MathMin(double value1, double value2)",
                "return_type": "double",
                "parameters": "double, double",
                "category": "Math", 
                "description": "Returns minimum value"
            },
            "MathAbs": {
                "signature": "double MathAbs(double value)",
                "return_type": "double",
                "parameters": "double",
                "category": "Math",
                "description": "Returns absolute value"
            },
            "MathIsValidNumber": {
                "signature": "bool MathIsValidNumber(double number)",
                "return_type": "bool",
                "parameters": "double",
                "category": "Math",
                "description": "Checks if number is finite and valid"
            },
            
            # Memory functions
            "GetPointer": {
                "signature": "void* GetPointer(class_object)",
                "return_type": "void*",
                "parameters": "class_object",
                "category": "Memory",
                "description": "Returns pointer to class object (NOT structs)"
            },
            
            # Crypto functions
            "CryptEncode": {
                "signature": "int CryptEncode(ENUM_CRYPT_METHOD method, const uchar& data[], const uchar& key[], uchar& result[])",
                "return_type": "int",
                "parameters": "ENUM_CRYPT_METHOD, const uchar&[], const uchar&[], uchar&[]",
                "category": "Crypto",
                "description": "Encrypts data with specified method and key"
            },
            
            # File functions
            "FileOpen": {
                "signature": "int FileOpen(string filename, int flags, short delimiter=';')",
                "return_type": "int",
                "parameters": "string, int, short",
                "category": "File",
                "description": "Opens file"
            },
            "FileClose": {
                "signature": "void FileClose(int handle)",
                "return_type": "void",
                "parameters": "int",
                "category": "File",
                "description": "Closes file"
            },
            "FileWrite": {
                "signature": "uint FileWrite(int handle, ...)",
                "return_type": "uint",
                "parameters": "int, ...",
                "category": "File",
                "description": "Writes data to file"
            },
            
            # Time functions
            "TimeCurrent": {
                "signature": "datetime TimeCurrent()",
                "return_type": "datetime",
                "parameters": "",
                "category": "Time",
                "description": "Returns current time"
            },
            "TimeToStr": {
                "signature": "string TimeToStr(datetime value, int mode=TIME_DATE|TIME_MINUTES)",
                "return_type": "string", 
                "parameters": "datetime, int",
                "category": "Time",
                "description": "Converts time to string"
            },
            
            # Print/Debug functions
            "Print": {
                "signature": "void Print(...)",
                "return_type": "void",
                "parameters": "...",
                "category": "Debug",
                "description": "Prints to Experts tab"
            },
            "Comment": {
                "signature": "void Comment(...)",
                "return_type": "void",
                "parameters": "...",
                "category": "Debug", 
                "description": "Displays comment on chart"
            }
        }
        
        # Insert built-in functions into database
        for func_name, info in builtin_functions.items():
            self.cursor.execute("""
                INSERT OR REPLACE INTO mql5_builtin_functions 
                (function_name, signature, return_type, parameters, description, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                func_name,
                info["signature"],
                info["return_type"], 
                info["parameters"],
                info["description"],
                info["category"]
            ))
        
        self.conn.commit()
        print(f"✅ Loaded {len(builtin_functions)} MQL5 built-in functions")
    
    def scan_project_files(self):
        """Scan all project .mqh and .mq5 files to build function database"""
        print("🔍 Scanning project files for function definitions...")
        
        include_dir = self.project_root / "Include/ProjectQuantum"
        scripts_dir = self.project_root / "Scripts/ProjectQuantum"
        
        total_functions = 0
        total_classes = 0
        
        # Scan include files
        for mqh_file in include_dir.rglob("*.mqh"):
            functions, classes = self._analyze_file(mqh_file)
            total_functions += len(functions)
            total_classes += len(classes)
            self._store_functions(functions)
            self._store_classes(classes)
        
        # Scan script files
        for mq5_file in scripts_dir.rglob("*.mq5"):
            functions, classes = self._analyze_file(mq5_file)
            total_functions += len(functions)
            total_classes += len(classes) 
            self._store_functions(functions)
            self._store_classes(classes)
        
        print(f"✅ Scanned project: {total_functions} functions, {total_classes} classes")
    
    def _analyze_file(self, file_path: Path) -> Tuple[List[Dict], List[Dict]]:
        """Analyze a single MQL5 file for functions and classes"""
        functions = []
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find class definitions
            class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*public\s+([A-Za-z_][A-Za-z0-9_]*))?\s*{'
            for match in re.finditer(class_pattern, content, re.MULTILINE):
                classes.append({
                    'class_name': match.group(1),
                    'parent_class': match.group(2) or '',
                    'file_path': str(file_path),
                    'line_number': content[:match.start()].count('\n') + 1
                })
            
            # Find function definitions
            func_pattern = r'(public|private|protected|static)?\s*([A-Za-z_][A-Za-z0-9_\*]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*[{;]'
            for match in re.finditer(func_pattern, content, re.MULTILINE):
                visibility = match.group(1) or 'public'
                return_type = match.group(2).strip()
                func_name = match.group(3)
                line_num = content[:match.start()].count('\n') + 1
                
                # Extract full function signature
                signature = match.group(0).rstrip('{;')
                
                functions.append({
                    'function_name': func_name,
                    'file_path': str(file_path),
                    'signature': signature,
                    'return_type': return_type,
                    'line_number': line_num,
                    'is_public': visibility == 'public',
                    'is_static': 'static' in signature
                })
        
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
        
        return functions, classes
    
    def _store_functions(self, functions: List[Dict]):
        """Store functions in database"""
        for func in functions:
            self.cursor.execute("""
                INSERT OR REPLACE INTO project_functions 
                (function_name, file_path, signature, return_type, line_number, is_public, is_static)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                func['function_name'],
                func['file_path'], 
                func['signature'],
                func['return_type'],
                func['line_number'],
                func['is_public'],
                func['is_static']
            ))
        self.conn.commit()
    
    def _store_classes(self, classes: List[Dict]):
        """Store classes in database"""
        for cls in classes:
            self.cursor.execute("""
                INSERT OR REPLACE INTO class_definitions 
                (class_name, file_path, parent_class)
                VALUES (?, ?, ?)
            """, (
                cls['class_name'],
                cls['file_path'],
                cls['parent_class']
            ))
        self.conn.commit()
    
    def get_function_signature(self, function_name: str) -> str:
        """Get correct function signature for intelligent code generation"""
        # Check built-in functions first
        self.cursor.execute("""
            SELECT signature, category FROM mql5_builtin_functions 
            WHERE function_name = ?
        """, (function_name,))
        
        result = self.cursor.fetchone()
        if result:
            return f"Built-in {result[1]}: {result[0]}"
        
        # Check project functions
        self.cursor.execute("""
            SELECT signature, file_path FROM project_functions 
            WHERE function_name = ? 
            ORDER BY last_modified DESC LIMIT 1
        """, (function_name,))
        
        result = self.cursor.fetchone()
        if result:
            return f"Project: {result[0]} (from {result[1]})"
        
        return f"Unknown function: {function_name}"
    
    def suggest_correct_usage(self, function_name: str) -> Dict:
        """Suggest correct usage based on learned patterns"""
        self.cursor.execute("""
            SELECT fc.parameters_used, fc.context, cf.fixed_code
            FROM function_calls fc
            LEFT JOIN compilation_fixes cf ON fc.called_function = cf.original_code
            WHERE fc.called_function = ? AND fc.is_correct = 1
            ORDER BY fc.recorded_at DESC LIMIT 5
        """, (function_name,))
        
        examples = self.cursor.fetchall()
        
        return {
            'function_name': function_name,
            'signature': self.get_function_signature(function_name),
            'examples': [{'params': ex[0], 'context': ex[1], 'fixed_code': ex[2]} for ex in examples]
        }
    
    def record_compilation_error(self, error_type: str, error_msg: str, file_path: str, 
                               original_code: str, fixed_code: str, line_num: int):
        """Record compilation error and its fix for learning"""
        self.cursor.execute("""
            INSERT INTO compilation_fixes 
            (error_type, error_message, original_code, fixed_code, file_path, line_number)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (error_type, error_msg, original_code, fixed_code, file_path, line_num))
        self.conn.commit()
    
    def generate_intelligent_report(self):
        """Generate comprehensive report of learned knowledge"""
        print("📊 MQL5 Intelligent Agent Knowledge Report")
        print("=" * 80)
        
        # Built-in functions count
        self.cursor.execute("SELECT COUNT(*), category FROM mql5_builtin_functions GROUP BY category")
        builtin_stats = self.cursor.fetchall()
        
        print("\n🔧 MQL5 Built-in Functions by Category:")
        for count, category in builtin_stats:
            print(f"   {category}: {count} functions")
        
        # Project functions count
        self.cursor.execute("SELECT COUNT(DISTINCT function_name) FROM project_functions")
        project_func_count = self.cursor.fetchone()[0]
        print(f"\n📁 Project Functions: {project_func_count}")
        
        # Class definitions
        self.cursor.execute("SELECT COUNT(DISTINCT class_name) FROM class_definitions") 
        class_count = self.cursor.fetchone()[0]
        print(f"\n🏗️  Project Classes: {class_count}")
        
        # Most used functions
        self.cursor.execute("""
            SELECT function_name, usage_count FROM mql5_builtin_functions 
            WHERE usage_count > 0 ORDER BY usage_count DESC LIMIT 10
        """)
        popular_functions = self.cursor.fetchall()
        
        if popular_functions:
            print(f"\n🔥 Most Used Functions:")
            for func, count in popular_functions:
                print(f"   {func}: {count} uses")
        
        # Recent compilation fixes
        self.cursor.execute("""
            SELECT error_type, COUNT(*) FROM compilation_fixes 
            GROUP BY error_type ORDER BY COUNT(*) DESC LIMIT 5
        """)
        error_patterns = self.cursor.fetchall()
        
        if error_patterns:
            print(f"\n🔧 Common Error Patterns:")
            for error_type, count in error_patterns:
                print(f"   {error_type}: {count} occurrences")
        
        return {
            'builtin_functions': sum(count for count, _ in builtin_stats),
            'project_functions': project_func_count,
            'classes': class_count,
            'knowledge_db_path': self.db_path
        }
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    print("🤖 Initializing MQL5 Intelligent Agent...")
    agent = MQL5IntelligentAgent()
    
    try:
        # Load built-in functions
        agent.load_mql5_builtin_functions()
        
        # Scan project files
        agent.scan_project_files()
        
        # Generate report
        report = agent.generate_intelligent_report()
        
        print(f"\n✅ Intelligence database ready at: {agent.db_path}")
        print("💡 Use agent.get_function_signature('function_name') for smart suggestions")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        agent.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)