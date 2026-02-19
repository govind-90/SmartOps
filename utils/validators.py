"""Input validation utilities."""

from typing import Tuple, List
from pydantic import ValidationError
from core.models import ChangeRequest, ParseError
from utils.logger import get_logger

logger = get_logger(__name__)


def validate_change_request(data: dict) -> Tuple[bool, ChangeRequest | None, List[str]]:
    """
    Validate change request data.
    
    Args:
        data: Dictionary containing change request fields
        
    Returns:
        tuple: (Is valid, ChangeRequest object or None, List of error messages)
    """
    try:
        change_request = ChangeRequest(**data)
        return True, change_request, []
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            message = error["msg"]
            errors.append(f"{field}: {message}")
            logger.warning(f"Validation error in {field}: {message}")
        return False, None, errors


def validate_change_requests_batch(
    data_list: List[dict],
) -> Tuple[List[ChangeRequest], List[ParseError]]:
    """
    Validate a batch of change requests.
    
    Args:
        data_list: List of change request dictionaries
        
    Returns:
        tuple: (Valid requests, Parse errors)
    """
    valid_requests = []
    errors = []

    for row_idx, data in enumerate(data_list, start=1):
        try:
            change_request = ChangeRequest(**data)
            valid_requests.append(change_request)
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                errors.append(
                    ParseError(
                        row_number=row_idx,
                        column=field,
                        error=error["msg"],
                    )
                )
                logger.warning(f"Row {row_idx}, {field}: {error['msg']}")

    logger.info(
        f"Batch validation: {len(valid_requests)} valid, {len(errors)} errors"
    )
    return valid_requests, errors
