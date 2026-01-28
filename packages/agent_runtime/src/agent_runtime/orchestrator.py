"""
Agent Orchestrator - SOTA 2026 Plan-and-Execute Runtime.
"""

import json
import structlog
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from tools.registry import ToolRegistry
from tools.types import ToolResult
from llm.providers.base import LLMProvider
from llm.reasoning.planning import Plan, PROMPT_PLANNING

logger = structlog.get_logger()

@dataclass
class AgentResult:
    answer: str
    metadata: Dict[str, Any]
    success: bool = True

class Orchestrator:
    """
    SOTA Agent Orchestrator.
    Core Loop: Plan -> Execute -> Review
    """
    
    def __init__(
        self, 
        llm: LLMProvider, 
        tools: ToolRegistry,
        max_iterations: int = 5
    ):
        self.llm = llm
        self.tools = tools
        self.max_iterations = max_iterations
        
    async def run(self, query: str, context: Optional[Dict] = None) -> AgentResult:
        """
        Execute the agent loop for a query.
        """
        logger.info("orchestrator_start", query=query)
        scratchpad = []
        
        # 1. PLANNING PHASE
        # In a real SOTA implementation, this would use a dedicated "Thinking Model" (e.g., o1)
        # Here we simulate it with a specific planning prompt.
        
        tool_schemas = json.dumps(self.tools.get_tool_schemas(), indent=2)
        planning_prompt = PROMPT_PLANNING.format(query=query, tool_schemas=tool_schemas)
        
        try:
            plan_response = await self.llm.generate(planning_prompt)
            # Naive parsing - in prod we'd use constrained decoding or robust JSON parser
            # Assuming LLM returns raw JSON for now (or wrapped in markdown blocks)
            content = plan_response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            plan_data = json.loads(content)
            plan = Plan(**plan_data)
            logger.info("plan_generated", goal=plan.goal, steps=len(plan.steps))
            
        except Exception as e:
            logger.error("planning_failed", error=str(e))
            # Fallback to direct answer if planning fails (graceful degradation)
            return await self._fallback_direct_answer(query)

        # 2. EXECUTION PHASE
        final_answer = None
        results = {}
        
        for step in plan.steps:
            logger.info("executing_step", step_id=step.id, tool=step.tool_name)
            
            # Check if this tool exists
            tool = self.tools.get(step.tool_name)
            if not tool:
                # Handle missing tool gracefully?
                logger.warning("tool_not_found", tool_name=step.tool_name)
                continue
            
            # Execute
            try:
                result = await tool.run(**step.tool_input)
                results[step.id] = result
                scratchpad.append({
                    "step": step.id,
                    "thought": step.thought,
                    "action": step.tool_name,
                    "input": step.tool_input,
                    "observation": result.data
                })
            except Exception as e:
                logger.error("step_execution_failed", step_id=step.id, error=str(e))
                results[step.id] = ToolResult(success=False, data=None, error=str(e))

        # 3. SYNTHESIS / REVIEW PHASE
        # Aggregate results into a final answer
        final_answer = await self._synthesize_answer(query, scratchpad)
        
        return AgentResult(
            answer=final_answer,
            metadata={
                "plan": plan.dict(),
                "steps_executed": len(results)
            }
        )

    async def _synthesize_answer(self, query: str, history: List[Dict]) -> str:
        """Synthesize final answer from execution history."""
        prompt = f"""
        User Query: {query}
        
        Execution History:
        {json.dumps(history, indent=2)}
        
        Based on the execution history above, provide a comprehensive answer to the user.
        If the tools didn't provide enough info, admit it.
        """
        response = await self.llm.generate(prompt)
        return response.content

    async def _fallback_direct_answer(self, query: str) -> AgentResult:
        """fallback for when planning fails."""
        response = await self.llm.generate(f"Please answer this directly: {query}")
        return AgentResult(answer=response.content, metadata={"fallback": True}, success=True)
