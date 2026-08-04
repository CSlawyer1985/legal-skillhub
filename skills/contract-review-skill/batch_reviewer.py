#!/usr/bin/env python3
"""
Batch Contract Review Manager - Uses SubAgent system for parallel contract processing
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import SubAgent system
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from subagent import SubAgentManager, AgentStatus

# Import our contract review engine
sys.path.insert(0, str(Path(__file__).parent))
from review_engine import ContractReviewEngine

class BatchContractReviewManager:
    def __init__(self, max_workers: int = 4):
        self.manager = SubAgentManager()
        self.max_workers = max_workers
        self.engine = ContractReviewEngine(Path(__file__).parent / "legal_patterns")
        self.results_dir = Path(__file__).parent / "batch_results"
        self.results_dir.mkdir(exist_ok=True)
    
    def review_contracts_parallel(self, contract_files: List[str], industry: str = None) -> Dict[str, Any]:
        """
        Review multiple contracts in parallel using SubAgent system
        """
        start_time = time.time()
        
        # Create SubAgents for each contract
        agent_ids = []
        for i, contract_file in enumerate(contract_files):
            if not os.path.exists(contract_file):
                continue
                
            agent_name = f"ContractReviewer_{i+1}"
            task = f"Review contract: {os.path.basename(contract_file)}"
            
            context = {
                "contract_file": contract_file,
                "industry": industry,
                "index": i
            }
            
            agent_id = self.manager.create_agent(agent_name, task, context)
            agent_ids.append(agent_id)
        
        # Process agents in batches (respecting max_workers)
        results = {}
        completed_agents = set()
        
        while len(completed_agents) < len(agent_ids):
            # Check status of running agents
            for agent_id in agent_ids:
                if agent_id in completed_agents:
                    continue
                    
                agent = self.manager.get_agent(agent_id)
                if not agent:
                    continue
                
                # If agent is not yet started, start it
                if agent.status == AgentStatus.PENDING:
                    self._process_contract_agent(agent_id)
                
                # If agent completed, collect result
                if agent.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]:
                    if agent_id not in completed_agents:
                        results[agent_id] = {
                            "agent_id": agent_id,
                            "name": agent.name,
                            "task": agent.task,
                            "status": agent.status.value,
                            "result": agent.result,
                            "error": agent.error,
                            "created_at": agent.created_at,
                            "completed_at": agent.completed_at
                        }
                        completed_agents.add(agent_id)
            
            # Small delay to prevent busy waiting
            time.sleep(0.1)
            
            # Timeout check (5 minutes max)
            if time.time() - start_time > 300:
                break
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Format final results
        batch_results = {
            "batch_info": {
                "total_contracts": len(contract_files),
                "processed_contracts": len([r for r in results.values() if r["status"] == "completed"]),
                "failed_contracts": len([r for r in results.values() if r["status"] == "failed"]),
                "processing_time_seconds": round(processing_time, 2),
                "timestamp": datetime.now().isoformat(),
                "industry": industry or "general",
                "max_workers": self.max_workers
            },
            "results": [],
            "summary": {
                "total_high_risk": 0,
                "total_medium_risk": 0,
                "total_low_risk": 0,
                "average_risk_score": 0,
                "risk_distribution": {"critical": 0, "high": 0, "medium": 0, "low": 0}
            }
        }
        
        # Process results
        risk_scores = []
        for result in results.values():
            if result["status"] == "completed" and result["result"]:
                contract_result = result["result"]
                batch_results["results"].append({
                    "contract_file": contract_result.get("metadata", {}).get("contract_file", "unknown"),
                    "contract_name": os.path.basename(contract_result.get("metadata", {}).get("contract_file", "unknown")),
                    "risk_score": contract_result.get("risk_score", 0),
                    "risk_level": self._score_to_level(contract_result.get("risk_score", 0)),
                    "findings_count": len(contract_result.get("findings", [])),
                    "high_risk_count": len([f for f in contract_result.get("findings", []) if f.get("risk_level") == "high"]),
                    "medium_risk_count": len([f for f in contract_result.get("findings", []) if f.get("risk_level") == "medium"]),
                    "low_risk_count": len([f for f in contract_result.get("findings", []) if f.get("risk_level") == "low"]),
                    "critical_risk_count": len([f for f in contract_result.get("findings", []) if f.get("risk_level") == "critical"])
                })
                
                # Accumulate for summary
                risk_scores.append(contract_result.get("risk_score", 0))
                batch_results["summary"]["total_high_risk"] += len([f for f in contract_result.get("findings", []) if f.get("risk_level") == "high"])
                batch_results["summary"]["total_medium_risk"] += len([f for f in contract_result.get("findings", []) if f.get("risk_level") == "medium"])
                batch_results["summary"]["total_low_risk"] += len([f for f in contract_result.get("findings", []) if f.get("risk_level") == "low"])
                
                # Risk distribution
                for finding in contract_result.get("findings", []):
                    risk_level = finding.get("risk_level", "low")
                    if risk_level == "critical":
                        batch_results["summary"]["risk_distribution"]["critical"] += 1
                    elif risk_level == "high":
                        batch_results["summary"]["risk_distribution"]["high"] += 1
                    elif risk_level == "medium":
                        batch_results["summary"]["risk_distribution"]["medium"] += 1
                    elif risk_level == "low":
                        batch_results["summary"]["risk_distribution"]["low"] += 1
        
        # Calculate average risk score
        if risk_scores:
            batch_results["summary"]["average_risk_score"] = round(sum(risk_scores) / len(risk_scores), 2)
        
        return batch_results
    
    def _process_contract_agent(self, agent_id: str):
        """Process a single contract review agent"""
        agent = self.manager.get_agent(agent_id)
        if not agent:
            return
        
        # Update status to running
        self.manager.update_status(agent_id, AgentStatus.RUNNING)
        
        try:
            # Get context
            contract_file = agent.context.get("contract_file")
            industry = agent.context.get("industry")
            
            if not contract_file or not os.path.exists(contract_file):
                raise FileNotFoundError(f"Contract file not found: {contract_file}")
            
            # Read contract
            contract_text = Path(contract_file).read_text(encoding='utf-8')
            
            # Review contract
            result = self.engine.review_contract(contract_text, industry)
            
            # Add file info to result
            result["metadata"]["contract_file"] = contract_file
            result["metadata"]["file_size"] = os.path.getsize(contract_file)
            
            # Update agent with result
            self.manager.update_status(agent_id, AgentStatus.COMPLETED, result=result)
            
        except Exception as e:
            # Update agent with error
            self.manager.update_status(agent_id, AgentStatus.FAILED, error=str(e))
    
    def _score_to_level(self, score: int) -> str:
        """Convert risk score to level label"""
        if score >= 80:
            return "LOW"
        elif score >= 60:
            return "MEDIUM"
        elif score >= 40:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def save_batch_report(self, batch_results: Dict[str, Any], output_file: str = None) -> str:
        """Save batch review results to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.results_dir / f"batch_review_report_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, indent=2, ensure_ascii=False)
        
        return str(output_file)
    
    def print_batch_summary(self, batch_results: Dict[str, Any]):
        """Print human-readable batch summary"""
        info = batch_results["batch_info"]
        summary = batch_results["summary"]
        
        print("=" * 70)
        print("BATCH CONTRACT REVIEW REPORT")
        print("=" * 70)
        print(f"Total Contracts: {info['total_contracts']}")
        print(f"Processed: {info['processed_contracts']}")
        print(f"Failed: {info['failed_contracts']}")
        print(f"Processing Time: {info['processing_time_seconds']} seconds")
        print(f"Timestamp: {info['timestamp']}")
        print(f"Industry Focus: {info['industry']}")
        print(f"Max Workers: {info['max_workers']}")
        print("-" * 70)
        print("SUMMARY:")
        print(f"  Average Risk Score: {summary['average_risk_score']}/100")
        print(f"  Total High Risk Findings: {summary['total_high_risk']}")
        print(f"  Total Medium Risk Findings: {summary['total_medium_risk']}")
        print(f"  Total Low Risk Findings: {summary['total_low_risk']}")
        print(f"  Risk Distribution:")
        print(f"    Critical: {summary['risk_distribution']['critical']}")
        print(f"    High: {summary['risk_distribution']['high']}")
        print(f"    Medium: {summary['risk_distribution']['medium']}")
        print(f"    Low: {summary['risk_distribution']['low']}")
        print("-" * 70)
        print("INDIVIDUAL RESULTS:")
        
        for i, result in enumerate(batch_results["results"], 1):
            print(f"{i}. {result['contract_name']}")
            print(f"   Risk Score: {result['risk_score']}/100 ({result['risk_level']})")
            print(f"   Findings: {result['findings_count']} "
                  f"(H:{result['high_risk_count']} M:{result['medium_risk_count']} "
                  f"L:{result['low_risk_count']} C:{result['critical_risk_count']})")
            print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_reviewer.py <contract_file1> [contract_file2] ... [--industry <industry>] [--workers <n>]")
        print("Example: python batch_reviewer.py contract1.txt contract2.txt --industry tech --workers 4")
        sys.exit(1)
    
    # Parse arguments
    args = sys.argv[1:]
    contract_files = []
    industry = None
    max_workers = 4
    
    i = 0
    while i < len(args):
        if args[i] == "--industry" and i + 1 < len(args):
            industry = args[i + 1]
            i += 2
        elif args[i] == "--workers" and i + 1 < len(args):
            try:
                max_workers = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        else:
            contract_files.append(args[i])
            i += 1
    
    if not contract_files:
        print("Error: No contract files specified")
        sys.exit(1)
    
    # Validate files exist
    valid_files = []
    for f in contract_files:
        if os.path.exists(f):
            valid_files.append(f)
        else:
            print(f"Warning: File not found - {f}")
    
    if not valid_files:
        print("Error: No valid contract files found")
        sys.exit(1)
    
    # Process batch
    manager = BatchContractReviewManager(max_workers=max_workers)
    print(f"Starting batch review of {len(valid_files)} contracts with {max_workers} workers...")
    results = manager.review_contracts_parallel(valid_files, industry)
    
    # Display results
    manager.print_batch_summary(results)
    
    # Save results
    output_file = manager.save_batch_report(results)
    print(f"Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()