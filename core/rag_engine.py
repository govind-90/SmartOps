"""RAG engine for policy compliance checking using ChromaDB."""

import json
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from config.settings import settings
from config.prompts import COMPLIANCE_PROMPT
from core.models import ComplianceResult, ComplianceIssue
from utils.logger import get_logger

logger = get_logger(__name__)


class RAGEngine:
    """RAG engine for policy compliance checking."""

    def __init__(self) -> None:
        """Initialize RAG engine with ChromaDB and policy documents."""
        try:
            # Initialize embeddings
            self.embeddings = SentenceTransformerEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )

            # Initialize LLM for compliance checking
            self.llm = ChatGroq(
                model=settings.LLM_MODEL,
                api_key=settings.GROQ_API_KEY,
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=1500,
            )

            # Text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
                separators=["\n\n", "\n", ". ", " ", ""],
            )

            # Initialize vector stores for each policy
            self.vector_stores: Dict[str, Chroma] = {}
            self._initialize_vector_stores()

            logger.info("RAG Engine initialized with LangChain Chroma")
        except Exception as e:
            logger.error(f"Failed to initialize RAG Engine: {e}")
            raise

    def _initialize_vector_stores(self) -> None:
        """Initialize Chroma vector stores with policy documents."""
        policy_files = [
            ("change_management", settings.POLICY_CHANGE_MANAGEMENT),
            ("security", settings.POLICY_SECURITY),
            ("deployment", settings.POLICY_DEPLOYMENT),
        ]

        for collection_name, policy_path in policy_files:
            try:
                persist_dir = Path(settings.CHROMA_DB_PATH) / collection_name

                # Check if vector store already exists
                if persist_dir.exists() and any(persist_dir.iterdir()):
                    logger.info(f"Vector store '{collection_name}' already exists, loading")
                    self.vector_stores[collection_name] = Chroma(
                        persist_directory=str(persist_dir),
                        embedding_function=self.embeddings,
                    )
                    continue

                # Load policy document
                if not os.path.exists(policy_path):
                    logger.warning(f"Policy file not found: {policy_path}, skipping")
                    continue

                with open(policy_path, "r", encoding="utf-8") as f:
                    policy_text = f.read()

                # Split into chunks
                chunks = self.text_splitter.split_text(policy_text)
                logger.info(f"Split policy into {len(chunks)} chunks")

                # Create metadata for each chunk
                metadatas = [{"source": collection_name, "chunk": i} for i in range(len(chunks))]

                # Create vector store
                self.vector_stores[collection_name] = Chroma.from_texts(
                    texts=chunks,
                    embedding=self.embeddings,
                    metadatas=metadatas,
                    persist_directory=str(persist_dir),
                )

                logger.info(f"Created vector store '{collection_name}' with {len(chunks)} chunks")

            except Exception as e:
                logger.error(f"Failed to initialize vector store '{collection_name}': {e}")
                raise

    def get_relevant_policies(
        self,
        change_summary: str,
        collection_name: str,
        n_results: int = 5,
    ) -> List[str]:
        """
        Retrieve relevant policy sections for a change.

        Args:
            change_summary: Summary of the change
            collection_name: Collection to search (change_management, security, deployment)
            n_results: Number of policy sections to retrieve

        Returns:
            List of relevant policy sections
        """
        try:
            if collection_name not in self.vector_stores:
                logger.warning(f"Vector store '{collection_name}' not found")
                return []

            vector_store = self.vector_stores[collection_name]
            docs = vector_store.similarity_search(
                query=change_summary,
                k=min(n_results, 5),
            )

            policies = [doc.page_content for doc in docs]
            return policies
        except Exception as e:
            logger.warning(f"Failed to retrieve policies from {collection_name}: {e}")
            return []

    def check_compliance(
        self,
        change_summary: str,
    ) -> ComplianceResult:
        """
        Check compliance of a change against all policies.
        
        Args:
            change_summary: Summary of the change to check
            
        Returns:
            ComplianceResult: Compliance check result
        """
        try:
            all_violations = []
            all_compliant_aspects = []
            all_improvements = []
            policies_reviewed = []

            # Check against each policy collection
            for collection_name in ["change_management", "security", "deployment"]:
                try:
                    # Get relevant policies
                    policy_sections = self.get_relevant_policies(
                        change_summary,
                        collection_name,
                        n_results=5,
                    )

                    if not policy_sections:
                        logger.warning(f"No policy sections found for {collection_name}")
                        continue

                    policies_reviewed.append(collection_name)

                    # Create compliance check prompt
                    policy_text = "\n\n---\n\n".join(policy_sections)
                    prompt_text = COMPLIANCE_PROMPT.format(
                        change_summary=change_summary,
                        policy_sections=policy_text,
                    )

                    # Call LLM for compliance check
                    logger.info(f"Checking compliance against {collection_name} policies")
                    response = self.llm.invoke([
                        {
                            "role": "user",
                            "content": prompt_text
                        }
                    ])

                    # Parse response
                    response_text = response.content
                    compliance_data = self._parse_compliance_response(response_text)

                    # Aggregate results
                    all_violations.extend(compliance_data.get("violations", []))
                    all_compliant_aspects.extend(compliance_data.get("compliant_aspects", []))
                    all_improvements.extend(compliance_data.get("improvement_suggestions", []))

                except Exception as e:
                    logger.error(f"Error checking {collection_name} compliance: {e}")
                    continue

            # Determine overall compliance
            compliant = len(all_violations) == 0
            compliance_score = max(0, 100 - (len(all_violations) * 10))  # -10 per violation

            result = ComplianceResult(
                compliant=compliant,
                compliance_score=min(100, max(0, compliance_score)),
                violations=[
                    ComplianceIssue(**v) for v in all_violations if isinstance(v, dict)
                ],
                compliant_aspects=all_compliant_aspects,
                improvement_suggestions=all_improvements,
                policies_reviewed=policies_reviewed,
            )

            logger.info(
                f"Compliance check complete: Compliant={result.compliant}, "
                f"Score={result.compliance_score}, Violations={len(result.violations)}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to check compliance: {e}")
            # Return default non-compliant result on error
            return ComplianceResult(
                compliant=False,
                compliance_score=0,
                violations=[],
                compliant_aspects=[],
                improvement_suggestions=["Unable to check compliance due to system error"],
                policies_reviewed=[],
            )

    @staticmethod
    def _parse_compliance_response(response_text: str) -> dict:
        """
        Parse compliance check response.
        
        Args:
            response_text: Response from LLM
            
        Returns:
            dict: Parsed compliance data
        """
        try:
            # Extract JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start == -1:
                logger.warning("No JSON found in compliance response")
                return {
                    "compliant": False,
                    "violations": [],
                    "compliant_aspects": [],
                    "improvement_suggestions": [],
                }

            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse compliance response JSON: {e}")
            return {
                "compliant": False,
                "violations": [],
                "compliant_aspects": [],
                "improvement_suggestions": [],
            }
