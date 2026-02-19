"""LLM analysis engine using Groq and LangChain."""

import json
import time
from typing import Any
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from config.settings import settings
from config.prompts import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_PROMPT
from core.models import ChangeRequest, RiskAssessment, Decision, RiskLevel
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMEngine:
    """LLM analysis engine for change request evaluation."""

    def __init__(self) -> None:
        """Initialize the LLM engine with Groq."""
        try:
            self.llm = ChatGroq(
                model=settings.LLM_MODEL,
                api_key=settings.GROQ_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            logger.info(f"LLM Engine initialized with model: {settings.LLM_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM Engine: {e}")
            raise

    def analyze_change(
        self,
        change_request: ChangeRequest,
        retry_count: int = 3,
        retry_delay: float = 2.0,
    ) -> RiskAssessment:
        """
        Analyze a change request using LLM.
        
        Args:
            change_request: The change request to analyze
            retry_count: Number of retries on API failure
            retry_delay: Delay between retries in seconds
            
        Returns:
            RiskAssessment: The analysis result
            
        Raises:
            ValueError: If JSON parsing fails or API call fails after retries
            RuntimeError: If LLM response is invalid
        """
        # Format the user prompt
        user_prompt_text = ANALYSIS_USER_PROMPT.format(
            short_description=change_request.short_description,
            long_description=change_request.long_description,
            change_type=change_request.change_type.value,
            change_category=change_request.change_category.value,
            implementation_steps=change_request.implementation_steps,
            validation_steps=change_request.validation_steps,
            rollback_plan=change_request.rollback_plan,
            planned_window=change_request.planned_window,
            impacted_services=change_request.impacted_services,
            complexity=change_request.complexity.value,
        )

        # Create prompt template
        prompt = PromptTemplate(
            input_variables=[],
            template=f"{ANALYSIS_SYSTEM_PROMPT}\n\n{user_prompt_text}"
        )

        last_exception = None
        for attempt in range(retry_count):
            try:
                logger.info(
                    f"Analyzing change request (attempt {attempt + 1}/{retry_count}): "
                    f"{change_request.short_description[:50]}..."
                )

                # Call LLM
                response = self.llm.invoke([
                    {
                        "role": "system",
                        "content": ANALYSIS_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_prompt_text
                    }
                ])

                # Parse response
                response_text = response.content
                logger.debug(f"LLM Response (first 500 chars): {response_text[:500]}")

                # Extract JSON from response
                risk_assessment = self._parse_response(response_text)
                logger.info(
                    f"Analysis complete: Decision={risk_assessment.decision}, "
                    f"Risk={risk_assessment.risk_score}, Confidence={risk_assessment.confidence}"
                )
                return risk_assessment

            except json.JSONDecodeError as e:
                last_exception = e
                logger.warning(
                    f"Failed to parse JSON response (attempt {attempt + 1}/{retry_count}): {e}"
                )
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"LLM API call failed (attempt {attempt + 1}/{retry_count}): {e}"
                )
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)

        # All retries failed
        logger.error(f"LLM analysis failed after {retry_count} attempts")
        raise RuntimeError(
            f"Failed to analyze change request after {retry_count} attempts: {last_exception}"
        )

    @staticmethod
    def _parse_response(response_text: str) -> RiskAssessment:
        """
        Parse LLM response and extract JSON.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            RiskAssessment: Parsed assessment
            
        Raises:
            json.JSONDecodeError: If JSON parsing fails
            ValueError: If required fields are missing
        """
        # Try to extract JSON from response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise json.JSONDecodeError(
                "No JSON found in response",
                response_text,
                0
            )

        json_str = response_text[json_start:json_end]
        data = json.loads(json_str)

        # Validate and convert decision string to enum
        decision_str = data.get("decision", "REVIEW_REQUIRED").upper()
        try:
            decision = Decision(decision_str)
        except ValueError:
            logger.warning(f"Invalid decision value: {decision_str}, defaulting to REVIEW_REQUIRED")
            decision = Decision.REVIEW_REQUIRED

        # Validate and convert risk level
        risk_level_str = data.get("risk_level", "MEDIUM").upper()
        try:
            risk_level = RiskLevel(risk_level_str)
        except ValueError:
            logger.warning(f"Invalid risk_level value: {risk_level_str}, defaulting to MEDIUM")
            risk_level = RiskLevel.MEDIUM

        # Extract and validate scores
        risk_score = data.get("risk_score", 50)
        if not (0 <= risk_score <= 100):
            logger.warning(f"Risk score out of range: {risk_score}, clamping to 0-100")
            risk_score = max(0, min(100, risk_score))

        confidence = data.get("confidence", 60)
        if not (0 <= confidence <= 100):
            logger.warning(f"Confidence out of range: {confidence}, clamping to 0-100")
            confidence = max(0, min(100, confidence))

        return RiskAssessment(
            decision=decision,
            risk_score=int(risk_score),
            confidence=int(confidence),
            risk_level=risk_level,
            reasoning=data.get("reasoning", "No reasoning provided"),
            risk_factors=data.get("risk_factors", []),
            red_flags=data.get("red_flags", []),
            missing_information=data.get("missing_information", []),
            recommendations=data.get("recommendations", []),
            validation_suggestions=data.get("validation_suggestions", []),
            critical_concerns=data.get("critical_concerns", []),
            positive_aspects=data.get("positive_aspects", []),
        )
