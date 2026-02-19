"""Sanity check script for judges.

This script runs a minimal end-to-end flow and generates
artifacts/sanity_output.json for evaluation.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import ComplianceAgent
from src.memory import MemoryManager, MemoryType
from src.rag import DocumentIngestion, DocumentStore


def run_sanity_check():
    """Run the sanity check and generate output file."""
    
    print("=" * 60)
    print("CODEX SANITY CHECK")
    print("=" * 60)
    
    # Ensure artifacts directory exists
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "test_name": "Codex Operational Risk & Compliance Agent",
        "checks": {},
        "status": "UNKNOWN",
    }
    
    try:
        # Check 1: Environment
        print("\n[1] Check 1: Environment setup...")
        if not os.getenv('NVIDIA_API_KEY'):
            results["checks"]["environment"] = {
                "status": "SKIP",
                "message": "NVIDIA_API_KEY not set - skipping full tests",
            }
            results["status"] = "PARTIAL"
        else:
            results["checks"]["environment"] = {
                "status": "PASS",
                "message": "Environment configured",
            }
        
        # Check 2: Document ingestion
        print("[2] Check 2: Document ingestion...")
        try:
            ingestion = DocumentIngestion()
            
            # Create a test document
            test_doc_path = Path("sample_docs/test_safety_rules.txt")
            if test_doc_path.exists():
                chunks = ingestion.ingest_document(
                    str(test_doc_path),
                    document_type="safety_manual",
                )
                results["checks"]["ingestion"] = {
                    "status": "PASS",
                    "chunks_created": len(chunks),
                }
            else:
                results["checks"]["ingestion"] = {
                    "status": "SKIP",
                    "message": "Test document not found",
                }
        except Exception as e:
            results["checks"]["ingestion"] = {
                "status": "FAIL",
                "error": str(e),
            }
        
        # Check 3: Vector store
        print("[3] Check 3: Vector store...")
        try:
            store = DocumentStore()
            stats = store.get_collection_stats()
            results["checks"]["vector_store"] = {
                "status": "PASS",
                "collection": stats["collection_name"],
                "documents": stats["document_count"],
            }
        except Exception as e:
            results["checks"]["vector_store"] = {
                "status": "FAIL",
                "error": str(e),
            }
        
        # Check 4: Memory system
        print("[4] Check 4: Memory system...")
        try:
            memory = MemoryManager()
            
            # Write test memory
            from src.memory.models import MemoryEntry
            test_entry = MemoryEntry(
                content="Test memory entry for sanity check",
                category="test",
                source="sanity_check",
            )
            memory.write_memory(test_entry, MemoryType.COMPANY)
            
            # Read back
            memories = memory.read_memories(memory_type=MemoryType.COMPANY)
            
            results["checks"]["memory"] = {
                "status": "PASS",
                "memories_count": len(memories),
            }
        except Exception as e:
            results["checks"]["memory"] = {
                "status": "FAIL",
                "error": str(e),
            }
        
        # Check 5: Full agent workflow (if API key available)
        if os.getenv('NVIDIA_API_KEY'):
            print("[5] Check 5: Full agent workflow...")
            try:
                agent = ComplianceAgent()
                
                # Ingest sample documents
                sample_docs = list(Path("sample_docs").glob("*.txt"))
                if sample_docs:
                    agent.ingest_documents([str(d) for d in sample_docs])
                
                # Run a safety check
                decision = agent.check_site_safety(
                    site_location="Boston",
                    operation_type="crane operation",
                )
                
                results["checks"]["agent_workflow"] = {
                    "status": "PASS",
                    "can_proceed": decision.can_proceed,
                    "has_citations": len(decision.citations) > 0,
                    "has_weather": decision.weather_compliance is not None,
                }
            except Exception as e:
                results["checks"]["agent_workflow"] = {
                    "status": "FAIL",
                    "error": str(e),
                }
        
        # Determine overall status
        statuses = [c.get("status", "UNKNOWN") for c in results["checks"].values()]
        
        if all(s == "PASS" for s in statuses):
            results["status"] = "PASS"
        elif any(s == "FAIL" for s in statuses):
            results["status"] = "FAIL"
        elif any(s == "PASS" for s in statuses):
            results["status"] = "PARTIAL"
        else:
            results["status"] = "SKIP"
        
    except Exception as e:
        results["status"] = "ERROR"
        results["error"] = str(e)
    
    # Write output file
    output_path = artifacts_dir / "sanity_output.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Results written to: {output_path}")
    print(f"Overall Status: {results['status']}")
    print(f"{'=' * 60}")
    
    # Print summary
    print("\nDetailed Results:")
    for check_name, check_result in results["checks"].items():
        status = check_result.get("status", "UNKNOWN")
        icon = "[OK]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[SKIP]"
        print(f"  {icon} {check_name}: {status}")
    
    return results


if __name__ == "__main__":
    results = run_sanity_check()
    
    # Exit with appropriate code
    if results["status"] == "PASS":
        sys.exit(0)
    elif results["status"] in ["PARTIAL", "SKIP"]:
        sys.exit(0)  # Still acceptable
    else:
        sys.exit(1)
