#!/usr/bin/env python3
"""
MQL5 Code Impact Analyzer
=========================
Measures cascading impact across files to determine severity of issues.

Standard Metrics Calculated:
- Fan-In: Number of modules that call this module (afferent coupling)
- Fan-Out: Number of modules this module calls (efferent coupling)
- Instability: Fan-Out / (Fan-In + Fan-Out) - how likely to change
- Impact Score: Weighted measure of how changes cascade
- Criticality: Financial risk multiplier based on function type

Usage:
  python3 mql5_impact_analyzer.py --project .
  python3 mql5_impact_analyzer.py --project . --output impact_report.json

Author: VelocityTrader Team
Version: 1.0.0
"""

import re
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class CriticalityLevel(Enum):
    """Criticality levels for functions/variables"""
    CRITICAL = 10    # Order execution, position management
    HIGH = 5         # Risk calculations, money management
    MEDIUM = 3       # Signal generation, analysis
    LOW = 1          # Display, logging, utilities
    MINIMAL = 0.5    # Constants, helpers


# Patterns that indicate high criticality
CRITICAL_PATTERNS = {
    CriticalityLevel.CRITICAL: [
        r'OrderSend', r'PositionOpen', r'PositionClose', r'PositionModify',
        r'trade\.', r'CTrade', r'OrderSelect', r'OrderDelete',
        r'AccountInfo', r'SymbolInfo.*Volume', r'NormalizeLot',
    ],
    CriticalityLevel.HIGH: [
        r'Risk', r'Drawdown', r'Equity', r'Balance', r'Margin',
        r'StopLoss', r'TakeProfit', r'CircuitBreaker', r'Halt',
        r'capitalAlloc', r'lotSize', r'volume',
    ],
    CriticalityLevel.MEDIUM: [
        r'Signal', r'Predict', r'Calculate', r'Analyze',
        r'Regime', r'QValue', r'Reward', r'Update.*Stats',
    ],
    CriticalityLevel.LOW: [
        r'Print', r'Log', r'HUD', r'Display', r'Draw', r'Comment',
    ]
}


@dataclass
class Symbol:
    """Represents a code symbol (function, variable, struct, etc.)"""
    name: str
    symbol_type: str  # 'function', 'variable', 'struct', 'include'
    file: str
    line: int
    criticality: CriticalityLevel = CriticalityLevel.LOW
    fan_in: int = 0           # How many things use this
    fan_out: int = 0          # How many things this uses
    impact_score: float = 0.0  # Cascading impact score
    dependents: Set[str] = field(default_factory=set)  # Symbols that depend on this
    dependencies: Set[str] = field(default_factory=set)  # Symbols this depends on


@dataclass
class FileMetrics:
    """Metrics for a single file"""
    path: str
    functions: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    afferent_coupling: int = 0    # Files that depend on this
    efferent_coupling: int = 0    # Files this depends on
    instability: float = 0.0      # I = Ce / (Ca + Ce)
    impact_score: float = 0.0     # Weighted cascading impact
    lines_of_code: int = 0


class MQL5ImpactAnalyzer:
    """
    Analyzes MQL5 codebase for dependency impact and cascading effects
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.symbols: Dict[str, Symbol] = {}
        self.file_metrics: Dict[str, FileMetrics] = {}
        self.include_graph: Dict[str, Set[str]] = defaultdict(set)  # file -> included files
        self.call_graph: Dict[str, Set[str]] = defaultdict(set)     # function -> called functions
        self.usage_graph: Dict[str, Set[str]] = defaultdict(set)    # variable -> users

    def analyze(self) -> Dict:
        """Run full impact analysis"""
        logger.info(f"Analyzing impact for {self.project_root}")

        # Find all MQL5 files
        mql5_dir = self.project_root / "MQL5"
        files = list(mql5_dir.rglob("*.mqh")) + list(mql5_dir.rglob("*.mq5"))
        files = [f for f in files if '.backup' not in str(f)]

        logger.info(f"Found {len(files)} files to analyze")

        # Phase 1: Extract symbols and build initial graph
        for file_path in files:
            self._extract_symbols(file_path)

        # Phase 2: Build dependency relationships
        for file_path in files:
            self._build_dependencies(file_path)

        # Phase 3: Calculate metrics
        self._calculate_metrics()

        # Phase 4: Calculate cascading impact
        self._calculate_cascading_impact()

        return self._generate_report()

    def _extract_symbols(self, file_path: Path):
        """Extract all symbols from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return

        rel_path = str(file_path.relative_to(self.project_root))
        self.file_metrics[rel_path] = FileMetrics(path=rel_path, lines_of_code=len(lines))

        # Extract includes
        for match in re.finditer(r'#include\s*[<"]([^>"]+)[>"]', content):
            include_name = match.group(1)
            self.file_metrics[rel_path].includes.append(include_name)
            self.include_graph[rel_path].add(include_name)

        # Extract function definitions
        func_pattern = r'(?:^|\n)\s*(?:static\s+)?(?:virtual\s+)?(?:inline\s+)?(void|int|double|bool|string|datetime|color|long|ulong|uint|float)\s+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{'
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            func_name = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            self.file_metrics[rel_path].functions.append(func_name)
            self.symbols[func_name] = Symbol(
                name=func_name,
                symbol_type='function',
                file=rel_path,
                line=line_num,
                criticality=self._get_criticality(func_name)
            )

        # Extract struct/class definitions
        struct_pattern = r'(?:struct|class)\s+(\w+)'
        for match in re.finditer(struct_pattern, content):
            struct_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            self.symbols[struct_name] = Symbol(
                name=struct_name,
                symbol_type='struct',
                file=rel_path,
                line=line_num,
                criticality=self._get_criticality(struct_name)
            )

        # Extract global variables
        global_pattern = r'^(?:extern\s+|input\s+)?(?:static\s+)?(?:const\s+)?(int|double|bool|string|datetime|color|long|ulong|uint|float)\s+(g_\w+|InpO\w+)'
        for match in re.finditer(global_pattern, content, re.MULTILINE):
            var_name = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            self.file_metrics[rel_path].variables.append(var_name)
            self.symbols[var_name] = Symbol(
                name=var_name,
                symbol_type='variable',
                file=rel_path,
                line=line_num,
                criticality=self._get_criticality(var_name)
            )

    def _build_dependencies(self, file_path: Path):
        """Build dependency relationships from function calls and variable usage"""
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except Exception:
            return

        rel_path = str(file_path.relative_to(self.project_root))

        # Find function calls
        for symbol_name in self.symbols:
            if self.symbols[symbol_name].symbol_type == 'function':
                # Look for calls to this function (not its definition)
                call_pattern = rf'\b{symbol_name}\s*\('
                for match in re.finditer(call_pattern, content):
                    # Find which function contains this call
                    caller = self._find_enclosing_function(content, match.start())
                    if caller and caller != symbol_name:
                        self.call_graph[caller].add(symbol_name)
                        self.symbols[symbol_name].dependents.add(caller)
                        if caller in self.symbols:
                            self.symbols[caller].dependencies.add(symbol_name)

            elif self.symbols[symbol_name].symbol_type == 'variable':
                # Look for usage of this variable
                usage_pattern = rf'\b{symbol_name}\b'
                for match in re.finditer(usage_pattern, content):
                    user = self._find_enclosing_function(content, match.start())
                    if user:
                        self.usage_graph[symbol_name].add(user)
                        self.symbols[symbol_name].dependents.add(user)

    def _find_enclosing_function(self, content: str, position: int) -> str:
        """Find the function that contains a given position"""
        # Look backwards for function definition
        before = content[:position]
        func_pattern = r'(?:void|int|double|bool|string|datetime|color|long|ulong|uint|float)\s+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{'

        matches = list(re.finditer(func_pattern, before))
        if matches:
            # Return the last (most recent) function
            return matches[-1].group(1)
        return None

    def _get_criticality(self, name: str) -> CriticalityLevel:
        """Determine criticality level based on naming patterns"""
        for level, patterns in CRITICAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name, re.IGNORECASE):
                    return level
        return CriticalityLevel.MINIMAL

    def _calculate_metrics(self):
        """Calculate fan-in, fan-out, and instability for each symbol"""
        for name, symbol in self.symbols.items():
            symbol.fan_in = len(symbol.dependents)
            symbol.fan_out = len(symbol.dependencies)

        # Calculate file-level metrics
        for path, metrics in self.file_metrics.items():
            # Afferent coupling: files that include this one
            for other_path, includes in self.include_graph.items():
                for inc in includes:
                    if inc in path or path.endswith(inc):
                        metrics.afferent_coupling += 1

            # Efferent coupling: files this includes
            metrics.efferent_coupling = len(metrics.includes)

            # Instability: I = Ce / (Ca + Ce)
            total_coupling = metrics.afferent_coupling + metrics.efferent_coupling
            if total_coupling > 0:
                metrics.instability = metrics.efferent_coupling / total_coupling

    def _calculate_cascading_impact(self):
        """Calculate cascading impact scores using BFS from each symbol"""
        for name, symbol in self.symbols.items():
            # Impact = fan_in * criticality * depth_factor
            base_impact = symbol.fan_in * symbol.criticality.value

            # Add transitive impact (symbols that depend on our dependents)
            visited = set()
            queue = [(name, 1)]  # (symbol, depth)
            transitive_impact = 0

            while queue:
                current, depth = queue.pop(0)

                if current in visited:
                    continue
                visited.add(current)

                if current in self.symbols:
                    curr_symbol = self.symbols[current]
                    # Decay impact with depth
                    depth_factor = 1.0 / (1 + depth * 0.5)
                    transitive_impact += curr_symbol.criticality.value * depth_factor

                    # Add dependents to queue
                    for dep in curr_symbol.dependents:
                        if dep not in visited:
                            queue.append((dep, depth + 1))

            # Store total impact
            symbol.impact_score = base_impact + transitive_impact

        # Calculate file-level impact scores
        for path, metrics in self.file_metrics.items():
            file_impact = 0
            for func in metrics.functions:
                if func in self.symbols:
                    file_impact += self.symbols[func].impact_score
            metrics.impact_score = file_impact

    def _generate_report(self) -> Dict:
        """Generate comprehensive impact report"""
        # Top impactful symbols
        sorted_symbols = sorted(
            self.symbols.values(),
            key=lambda s: s.impact_score,
            reverse=True
        )

        # Top impactful files
        sorted_files = sorted(
            self.file_metrics.values(),
            key=lambda f: f.impact_score,
            reverse=True
        )

        # Critical hotspots (high fan-in + high criticality)
        hotspots = [
            s for s in sorted_symbols
            if s.fan_in >= 5 and s.criticality.value >= CriticalityLevel.MEDIUM.value
        ]

        # Unstable components (high instability + high impact)
        unstable = [
            f for f in sorted_files
            if f.instability > 0.7 and f.impact_score > 10
        ]

        return {
            'summary': {
                'total_files': len(self.file_metrics),
                'total_symbols': len(self.symbols),
                'total_functions': sum(len(m.functions) for m in self.file_metrics.values()),
                'total_includes': sum(len(m.includes) for m in self.file_metrics.values()),
                'hotspot_count': len(hotspots),
                'unstable_count': len(unstable),
            },
            'top_impact_symbols': [
                {
                    'name': s.name,
                    'type': s.symbol_type,
                    'file': s.file,
                    'line': s.line,
                    'criticality': s.criticality.name,
                    'fan_in': s.fan_in,
                    'fan_out': s.fan_out,
                    'impact_score': round(s.impact_score, 2),
                }
                for s in sorted_symbols[:20]
            ],
            'top_impact_files': [
                {
                    'path': f.path,
                    'functions': len(f.functions),
                    'lines': f.lines_of_code,
                    'afferent_coupling': f.afferent_coupling,
                    'efferent_coupling': f.efferent_coupling,
                    'instability': round(f.instability, 3),
                    'impact_score': round(f.impact_score, 2),
                }
                for f in sorted_files[:10]
            ],
            'critical_hotspots': [
                {
                    'name': s.name,
                    'file': s.file,
                    'criticality': s.criticality.name,
                    'fan_in': s.fan_in,
                    'dependents': list(s.dependents)[:10],
                }
                for s in hotspots[:10]
            ],
            'unstable_components': [
                {
                    'path': f.path,
                    'instability': round(f.instability, 3),
                    'impact_score': round(f.impact_score, 2),
                    'efferent_coupling': f.efferent_coupling,
                }
                for f in unstable[:5]
            ],
            'metrics_legend': {
                'fan_in': 'Number of other symbols that depend on this one',
                'fan_out': 'Number of symbols this one depends on',
                'instability': 'Ce/(Ca+Ce) - values near 1.0 are more likely to change',
                'impact_score': 'Weighted measure of cascading impact if this changes',
                'criticality': 'CRITICAL(10), HIGH(5), MEDIUM(3), LOW(1), MINIMAL(0.5)',
            }
        }

    def print_report(self):
        """Print human-readable impact report"""
        report = self._generate_report()

        print("\n" + "=" * 70)
        print("CODE IMPACT ANALYSIS REPORT")
        print("=" * 70)
        print(f"Files Analyzed: {report['summary']['total_files']}")
        print(f"Total Symbols: {report['summary']['total_symbols']}")
        print(f"Functions: {report['summary']['total_functions']}")
        print(f"Critical Hotspots: {report['summary']['hotspot_count']}")
        print(f"Unstable Components: {report['summary']['unstable_count']}")
        print("-" * 70)

        print("\n=== TOP IMPACT SYMBOLS ===")
        print(f"{'Symbol':<30} {'Type':<10} {'Crit':<8} {'Fan-In':<7} {'Impact':<8}")
        print("-" * 70)
        for s in report['top_impact_symbols'][:15]:
            print(f"{s['name']:<30} {s['type']:<10} {s['criticality']:<8} {s['fan_in']:<7} {s['impact_score']:<8.1f}")

        print("\n=== TOP IMPACT FILES ===")
        print(f"{'File':<45} {'Funcs':<6} {'Ca':<4} {'Ce':<4} {'I':<6} {'Impact':<8}")
        print("-" * 70)
        for f in report['top_impact_files'][:10]:
            name = Path(f['path']).name
            print(f"{name:<45} {f['functions']:<6} {f['afferent_coupling']:<4} {f['efferent_coupling']:<4} {f['instability']:<6.2f} {f['impact_score']:<8.1f}")

        if report['critical_hotspots']:
            print("\n=== CRITICAL HOTSPOTS ===")
            print("(High fan-in + High criticality = Maximum change risk)")
            print("-" * 70)
            for h in report['critical_hotspots'][:5]:
                print(f"  {h['name']} ({h['criticality']})")
                print(f"    File: {h['file']}, Fan-In: {h['fan_in']}")
                if h['dependents']:
                    print(f"    Used by: {', '.join(h['dependents'][:5])}...")

        if report['unstable_components']:
            print("\n=== UNSTABLE COMPONENTS ===")
            print("(High instability + High impact = Fragile code)")
            print("-" * 70)
            for u in report['unstable_components']:
                print(f"  {u['path']}")
                print(f"    Instability: {u['instability']:.2f}, Impact: {u['impact_score']:.1f}")

        print("\n" + "=" * 70)
        print("LEGEND:")
        print("  Ca = Afferent Coupling (files that depend on this)")
        print("  Ce = Efferent Coupling (files this depends on)")
        print("  I  = Instability = Ce/(Ca+Ce), higher = more likely to change")
        print("  Impact = Cascading change impact score")
        print("=" * 70 + "\n")

    def get_symbol_severity_multiplier(self, symbol_name: str) -> float:
        """
        Get severity multiplier for a symbol based on its impact.
        Used by the auditor to amplify severity of issues in high-impact code.
        """
        if symbol_name not in self.symbols:
            return 1.0

        symbol = self.symbols[symbol_name]

        # Base multiplier from criticality
        base = symbol.criticality.value / 3  # Normalize to ~1-3 range

        # Amplify based on fan-in (more dependents = more critical)
        fan_in_factor = 1.0 + (symbol.fan_in * 0.1)

        # Cap at 5x
        return min(5.0, base * fan_in_factor)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='MQL5 Code Impact Analyzer')
    parser.add_argument('--project', type=Path, default=Path('.'))
    parser.add_argument('--output', type=Path, help='Save report to JSON')

    args = parser.parse_args()

    analyzer = MQL5ImpactAnalyzer(args.project.resolve())
    report = analyzer.analyze()
    analyzer.print_report()

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
