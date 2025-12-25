#!/usr/bin/env python3
"""
VelocityTrader Data Preparation Utility
Handles CSV import, validation, and preparation for backtesting

Supports:
- Multiple delimiters (comma, semicolon, tab)
- MT4/MT5 export formats
- Data validation and integrity checks
- Gap detection and handling
- Warmup period calculation
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import sys

class DataValidator:
    """Validates OHLCV data integrity"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_ohlcv(self, df: pd.DataFrame) -> bool:
        """Validate OHLCV data integrity"""
        self.errors = []
        self.warnings = []

        # Check required columns
        required = ['open', 'high', 'low', 'close']
        missing = [col for col in required if col not in df.columns]
        if missing:
            self.errors.append(f"Missing required columns: {missing}")
            return False

        # Check for NaN/null values
        for col in required:
            null_count = df[col].isna().sum()
            if null_count > 0:
                self.errors.append(f"Column '{col}' has {null_count} null values")

        # Check OHLC sanity
        invalid_hl = (df['high'] < df['low']).sum()
        if invalid_hl > 0:
            self.errors.append(f"{invalid_hl} rows have high < low")

        # Check for zero/negative prices
        for col in required:
            zero_count = (df[col] <= 0).sum()
            if zero_count > 0:
                self.errors.append(f"Column '{col}' has {zero_count} zero/negative values")

        # Check for duplicate timestamps
        if 'datetime' in df.columns:
            dupes = df['datetime'].duplicated().sum()
            if dupes > 0:
                self.warnings.append(f"{dupes} duplicate timestamps found")

        return len(self.errors) == 0


class GapDetector:
    """Detects price and time gaps in data"""

    def __init__(self, price_gap_atr_mult: float = 3.0, time_gap_minutes: int = 5):
        self.price_gap_mult = price_gap_atr_mult
        self.time_gap_minutes = time_gap_minutes

    def detect_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add gap detection columns to dataframe"""
        df = df.copy()

        # Calculate ATR for gap detection
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window=14).mean()

        # Price gaps
        df['price_gap'] = abs(df['open'] - df['close'].shift(1))
        df['is_price_gap'] = df['price_gap'] > (df['atr'] * self.price_gap_mult)

        # Time gaps (if datetime available)
        if 'datetime' in df.columns:
            df['time_diff'] = df['datetime'].diff()
            expected_diff = pd.Timedelta(minutes=self.time_gap_minutes)
            df['is_time_gap'] = df['time_diff'] > expected_diff * 2

        # Weekend gaps
        if 'datetime' in df.columns:
            df['day_of_week'] = df['datetime'].dt.dayofweek
            df['is_weekend_gap'] = (df['day_of_week'] == 0) & (df['day_of_week'].shift(1) == 4)

        return df


class CSVImporter:
    """Import CSV files with various formats"""

    DELIMITERS = [',', ';', '\t', '|']

    def __init__(self):
        self.detected_delimiter = None
        self.detected_format = None

    def detect_delimiter(self, filepath: Path) -> str:
        """Auto-detect CSV delimiter"""
        with open(filepath, 'r') as f:
            first_line = f.readline()

        for delim in self.DELIMITERS:
            if delim in first_line:
                self.detected_delimiter = delim
                return delim

        raise ValueError("Could not detect delimiter. Supported: comma, semicolon, tab, pipe")

    def detect_format(self, df: pd.DataFrame) -> str:
        """Detect data format (MT4, MT5, generic)"""
        cols = [c.lower() for c in df.columns]

        if 'time' in cols and 'open' in cols:
            return 'MT5'
        elif '<date>' in cols or '<time>' in cols:
            return 'MT4'
        elif 'datetime' in cols or 'date' in cols:
            return 'generic'
        else:
            return 'unknown'

    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard format"""
        # Lowercase all columns
        df.columns = [c.lower().strip() for c in df.columns]

        # Common renames
        renames = {
            '<date>': 'date',
            '<time>': 'time',
            '<open>': 'open',
            '<high>': 'high',
            '<low>': 'low',
            '<close>': 'close',
            '<vol>': 'volume',
            '<volume>': 'volume',
            '<tickvol>': 'tick_volume',
            'tick_volume': 'tick_volume',
            '<spread>': 'spread',
        }

        df = df.rename(columns=renames)

        # Combine date/time if separate
        if 'date' in df.columns and 'time' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
            df = df.drop(columns=['date', 'time'])
        elif 'time' in df.columns and 'date' not in df.columns:
            # MT5 format - 'time' is actually datetime
            df['datetime'] = pd.to_datetime(df['time'])
            df = df.drop(columns=['time'])

        return df

    def import_file(self, filepath: Path) -> pd.DataFrame:
        """Import CSV file with auto-detection and comprehensive error handling"""
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Validate file is readable
        if not filepath.is_file():
            raise ValueError(f"Path is not a file: {filepath}")

        # Check file size (warn if very large)
        file_size = filepath.stat().st_size
        if file_size == 0:
            raise ValueError(f"File is empty: {filepath}")
        if file_size > 1_000_000_000:  # 1GB
            print(f"WARNING: Large file detected ({file_size / 1_000_000:.1f} MB). Processing may be slow.")

        # Detect delimiter with error handling
        try:
            delimiter = self.detect_delimiter(filepath)
            print(f"Detected delimiter: {repr(delimiter)}")
        except ValueError as e:
            raise ValueError(f"Failed to detect delimiter in {filepath}: {e}")
        except IOError as e:
            raise IOError(f"Cannot read file {filepath}: {e}")

        # Read CSV with comprehensive error handling
        try:
            df = pd.read_csv(filepath, delimiter=delimiter)
        except pd.errors.EmptyDataError:
            raise ValueError(f"File contains no data: {filepath}")
        except pd.errors.ParserError as e:
            raise ValueError(f"Failed to parse CSV file {filepath}: {e}")
        except UnicodeDecodeError as e:
            # Try with different encoding
            print(f"WARNING: Unicode error, trying latin-1 encoding...")
            try:
                df = pd.read_csv(filepath, delimiter=delimiter, encoding='latin-1')
            except Exception as e2:
                raise ValueError(f"Failed to read file with any encoding: {e2}")
        except MemoryError:
            raise MemoryError(f"File too large to load into memory: {filepath}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error reading {filepath}: {type(e).__name__}: {e}")

        if df.empty:
            raise ValueError(f"File parsed but contains no data: {filepath}")

        print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        print(f"Original columns: {list(df.columns)}")

        # Detect format
        try:
            self.detected_format = self.detect_format(df)
            print(f"Detected format: {self.detected_format}")
        except Exception as e:
            print(f"WARNING: Could not detect format: {e}. Using 'unknown'.")
            self.detected_format = 'unknown'

        # Normalize columns with error handling
        try:
            df = self.normalize_columns(df)
            print(f"Normalized columns: {list(df.columns)}")
        except KeyError as e:
            raise ValueError(f"Missing expected column during normalization: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to normalize columns: {type(e).__name__}: {e}")

        return df


class WarmupCalculator:
    """Calculate required warmup period for RL features"""

    # Feature lookback requirements
    FEATURE_REQUIREMENTS = {
        'sma_20': 20,
        'sma_50': 50,
        'sma_200': 200,
        'atr_14': 14,
        'rsi_14': 14,
        'macd': 26,  # 26-period EMA
        'bollinger': 20,
        'momentum': 10,
        'regime_detection': 100,  # Statistical significance
        'correlation': 50,  # Correlation window
    }

    def calculate_warmup(self, features: list = None) -> int:
        """Calculate minimum warmup period for given features"""
        if features is None:
            features = list(self.FEATURE_REQUIREMENTS.keys())

        max_lookback = 0
        for feat in features:
            if feat in self.FEATURE_REQUIREMENTS:
                max_lookback = max(max_lookback, self.FEATURE_REQUIREMENTS[feat])

        # Add safety margin (20%)
        warmup = int(max_lookback * 1.2)

        return warmup


def prepare_data(filepath: str, output_path: str = None, validate: bool = True):
    """Main data preparation function"""

    print("=" * 60)
    print("VelocityTrader Data Preparation")
    print("=" * 60)

    # Import
    importer = CSVImporter()
    df = importer.import_file(Path(filepath))

    # Validate
    if validate:
        print("\nValidating data...")
        validator = DataValidator()
        is_valid = validator.validate_ohlcv(df)

        if validator.errors:
            print("ERRORS:")
            for err in validator.errors:
                print(f"  ❌ {err}")

        if validator.warnings:
            print("WARNINGS:")
            for warn in validator.warnings:
                print(f"  ⚠️ {warn}")

        if not is_valid:
            print("\n❌ Data validation FAILED")
            return None
        else:
            print("✅ Data validation PASSED")

    # Detect gaps
    print("\nDetecting gaps...")
    gap_detector = GapDetector()
    df = gap_detector.detect_gaps(df)

    price_gaps = df['is_price_gap'].sum() if 'is_price_gap' in df.columns else 0
    time_gaps = df['is_time_gap'].sum() if 'is_time_gap' in df.columns else 0
    weekend_gaps = df['is_weekend_gap'].sum() if 'is_weekend_gap' in df.columns else 0

    print(f"  Price gaps (>3 ATR): {price_gaps}")
    print(f"  Time gaps: {time_gaps}")
    print(f"  Weekend gaps: {weekend_gaps}")

    # Calculate warmup
    print("\nCalculating warmup period...")
    warmup_calc = WarmupCalculator()
    warmup_bars = warmup_calc.calculate_warmup()
    print(f"  Recommended warmup: {warmup_bars} bars")
    print(f"  Current InpCalibrationTicks: 100 (should be >= {warmup_bars})")

    # Summary
    print("\n" + "=" * 60)
    print("DATA SUMMARY")
    print("=" * 60)
    print(f"Total bars: {len(df)}")
    print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}" if 'datetime' in df.columns else "")
    print(f"OHLC range: {df['low'].min():.5f} - {df['high'].max():.5f}")
    print(f"Usable bars (after warmup): {len(df) - warmup_bars}")

    # Output
    if output_path:
        output_path = Path(output_path)
        df.to_csv(output_path, index=False)
        print(f"\n✅ Cleaned data saved to: {output_path}")

    return df


def main():
    parser = argparse.ArgumentParser(description='VelocityTrader Data Preparation')
    parser.add_argument('input', help='Input CSV file path')
    parser.add_argument('-o', '--output', help='Output CSV file path')
    parser.add_argument('--no-validate', action='store_true', help='Skip validation')

    args = parser.parse_args()

    try:
        df = prepare_data(args.input, args.output, validate=not args.no_validate)
        if df is not None:
            print("\n✅ Data preparation complete!")
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
