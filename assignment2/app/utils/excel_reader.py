import pandas as pd
from typing import List, Dict, Any, Optional
import os


class ExcelReader:
    """Utility class for reading Excel data"""

    @staticmethod
    def read_excel_data(file_path: str) -> List[Dict[str, Any]]:
        """Read Excel file and return data as list of dictionaries"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        # Read Excel file
        df = pd.read_excel(file_path)

        # Convert to list of dictionaries
        data = df.to_dict('records')

        return data

    @staticmethod
    def get_excel_columns(file_path: str) -> List[str]:
        """Get column names from Excel file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        df = pd.read_excel(file_path)
        return df.columns.tolist()

    @staticmethod
    def get_sample_data(file_path: str, sample_size: int = 5) -> List[Dict[str, Any]]:
        """Get sample data from Excel file"""
        data = ExcelReader.read_excel_data(file_path)
        return data[:sample_size]

    @staticmethod
    def get_wine_ids(file_path: str) -> List[str]:
        """Get all wine IDs from Excel file"""
        data = ExcelReader.read_excel_data(file_path)
        return [item.get('wine_id', '') for item in data if 'wine_id' in item]

    @staticmethod
    def filter_by_wine_type(file_path: str, wine_type: str) -> List[Dict[str, Any]]:
        """Filter data by wine type"""
        data = ExcelReader.read_excel_data(file_path)
        return [item for item in data if item.get('wine_type', '').lower() == wine_type.lower()]

    @staticmethod
    def filter_by_region(file_path: str, region: str) -> List[Dict[str, Any]]:
        """Filter data by region"""
        data = ExcelReader.read_excel_data(file_path)
        return [item for item in data if item.get('region', '').lower() == region.lower()]

    @staticmethod
    def get_statistics(file_path: str) -> Dict[str, Any]:
        """Get basic statistics from Excel data"""
        data = ExcelReader.read_excel_data(file_path)

        if not data:
            return {}

        stats = {
            "total_records": len(data),
            "columns": ExcelReader.get_excel_columns(file_path),
            "wine_types": {},
            "regions": {},
            "vintage_range": {},
            "price_range": {}
        }

        # Analyze wine types
        for item in data:
            wine_type = item.get('wine_type', 'Unknown')
            stats["wine_types"][wine_type] = stats["wine_types"].get(wine_type, 0) + 1

        # Analyze regions
        for item in data:
            region = item.get('region', 'Unknown')
            stats["regions"][region] = stats["regions"].get(region, 0) + 1

        # Analyze vintage range
        vintages = [item.get('vintage') for item in data if item.get('vintage') is not None]
        if vintages:
            stats["vintage_range"] = {
                "min": min(vintages),
                "max": max(vintages)
            }

        # Analyze price range
        prices = [item.get('price_ref') for item in data if item.get('price_ref') is not None]
        if prices:
            stats["price_range"] = {
                "min": min(prices),
                "max": max(prices),
                "average": sum(prices) / len(prices)
            }

        return stats

    @staticmethod
    def validate_required_columns(file_path: str, required_columns: List[str]) -> Dict[str, Any]:
        """Validate that required columns exist in Excel file"""
        available_columns = ExcelReader.get_excel_columns(file_path)

        missing_columns = [col for col in required_columns if col not in available_columns]

        return {
            "is_valid": len(missing_columns) == 0,
            "missing_columns": missing_columns,
            "available_columns": available_columns
        }