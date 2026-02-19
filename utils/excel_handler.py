"""Excel file handling utilities."""

from typing import Tuple, List
import pandas as pd
from pathlib import Path
import openpyxl

from core.models import ChangeRequest, ParseError
from utils.validators import validate_change_requests_batch
from utils.logger import get_logger

logger = get_logger(__name__)


class ExcelHandler:
    """Handler for reading and processing Excel files."""

    # Expected column mapping
    EXPECTED_COLUMNS = {
        "Short Description": "short_description",
        "Long Description": "long_description",
        "Change Type": "change_type",
        "Change Category": "change_category",
        "Implementation Steps": "implementation_steps",
        "Validation Steps": "validation_steps",
        "Rollback Plan": "rollback_plan",
        "Planned Window": "planned_window",
        "Impacted Services": "impacted_services",
        "Complexity": "complexity",
    }

    @staticmethod
    def read_excel(
        file_path: str,
    ) -> Tuple[List[ChangeRequest], List[ParseError], int]:
        """
        Read and parse Excel file containing change requests.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            tuple: (Valid change requests, Parse errors, Total rows read)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        if not file_path.suffix.lower() in [".xlsx", ".xls"]:
            raise ValueError(f"Invalid file format: {file_path.suffix}")

        try:
            # Read Excel file
            logger.info(f"Reading Excel file: {file_path}")
            df = pd.read_excel(file_path, sheet_name=0)

            logger.info(f"Read {len(df)} rows from Excel")

            # Validate columns
            missing_columns = ExcelHandler._validate_columns(df)
            if missing_columns:
                error_msg = f"Missing columns: {', '.join(missing_columns)}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Map columns
            data_list = ExcelHandler._map_columns(df)

            # Validate data
            valid_requests, errors = validate_change_requests_batch(data_list)

            logger.info(
                f"Excel processing complete: {len(valid_requests)} valid, "
                f"{len(errors)} errors out of {len(df)} total rows"
            )

            return valid_requests, errors, len(df)

        except Exception as e:
            logger.error(f"Failed to read Excel file: {e}")
            raise

    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> List[str]:
        """
        Validate that all expected columns are present.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of missing column names
        """
        missing = []
        for expected_col in ExcelHandler.EXPECTED_COLUMNS.keys():
            if expected_col not in df.columns:
                missing.append(expected_col)
        return missing

    @staticmethod
    def _map_columns(df: pd.DataFrame) -> List[dict]:
        """
        Map Excel columns to model fields.
        
        Args:
            df: DataFrame to map
            
        Returns:
            List of dictionaries with mapped field names
        """
        mapped_data = []
        for _, row in df.iterrows():
            mapped_row = {}
            for excel_col, model_field in ExcelHandler.EXPECTED_COLUMNS.items():
                value = row.get(excel_col, "")
                # Convert NaN to empty string
                if pd.isna(value):
                    value = ""
                else:
                    value = str(value).strip()
                mapped_row[model_field] = value
            mapped_data.append(mapped_row)
        return mapped_data

    @staticmethod
    def write_results_to_excel(
        file_path: str,
        analyses: List[dict],
    ) -> str:
        """
        Write analysis results to Excel file.
        
        Args:
            file_path: Path to output Excel file
            analyses: List of analysis result dictionaries
            
        Returns:
            str: Path to created file
        """
        try:
            # Create DataFrame
            data = []
            for analysis in analyses:
                data.append({
                    "Description": analysis.get("short_description", "")[:100],
                    "Decision": analysis.get("final_decision", ""),
                    "Risk Score": analysis.get("risk_score", 0),
                    "Confidence": analysis.get("confidence", 0),
                    "Compliant": analysis.get("compliance_compliant", False),
                    "Created": analysis.get("created_at", ""),
                })

            df = pd.DataFrame(data)

            # Write to Excel
            logger.info(f"Writing {len(analyses)} analyses to {file_path}")
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Results", index=False)

                # Format cells
                workbook = writer.book
                worksheet = writer.sheets["Results"]

                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except Exception:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            logger.info(f"Excel file created: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to write results to Excel: {e}")
            raise
