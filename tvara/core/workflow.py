from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from .agent import Agent
import json
import logging
import re

blue = "\033[94m"
reset = "\033[0m"

class WorkflowMode(Enum):
    SEQUENTIAL = "sequential"
    SUPERVISED = "supervised"
    PARALLEL = "parallel"  # Future extension
    CONDITIONAL = "conditional"  # Future extension

class WorkflowResult:
    def __init__(self, success: bool, final_output: str, agent_outputs: List[Dict[str, Any]], error: Optional[str] = None):
        self.success = success
        self.final_output = final_output
        self.agent_outputs = agent_outputs
        self.error = error

class Workflow:
    def __init__(
        self,
        name: str,
        agents: List[Agent],
        mode: Literal["sequential", "supervised"] = "sequential",
        manager_agent: Optional[Agent] = None,
        max_iterations: int = 10,
        enable_logging: bool = True
    ):
        """
        Initializes a Tvara Workflow for orchestrating multiple agents.

        ## Params:
        - name (str): The name of the workflow.
        - agents (List[Agent]): List of agents to be used in the workflow.
        - mode (Literal["sequential", "supervised"]): Execution mode for the workflow.
        - manager_agent (Optional[Agent]): Required for supervised mode. Acts as the coordinator.
        - max_iterations (int): Maximum iterations for supervised mode to prevent infinite loops.
        - enable_logging (bool): Whether to enable detailed logging.

        ## Raises:
        - ValueError: If configuration is invalid.
        """
        if not agents:
            raise ValueError("At least one agent must be provided.")
        
        if mode == "supervised" and manager_agent is None:
            raise ValueError("Manager agent is required for supervised mode.")
        
        if mode == "supervised" and manager_agent in agents:
            raise ValueError("Manager agent should not be in the agents list.")

        self.name = name
        self.agents = agents
        self.mode = WorkflowMode(mode)
        self.manager_agent = manager_agent
        self.max_iterations = max_iterations
        self.enable_logging = enable_logging
        
        if enable_logging:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(f"Workflow-{name}")

    def _log(self, message: str, level: str = "info"):
        """Internal logging method."""
        if self.enable_logging:
            getattr(self.logger, level)(message)

    def _run_sequential(self, input_data: str) -> WorkflowResult:
        """
        Executes agents sequentially, passing output from one agent to the next.
        """
        self._log(f"Starting sequential workflow with {len(self.agents)} agents")
        
        agent_outputs = []
        current_input = input_data
        
        try:
            for i, agent in enumerate(self.agents):
                self._log(f"{blue}Executing agent {i+1}/{len(self.agents)}: {agent.name}{reset}")

                agent_output = agent.run(current_input)
                agent_outputs.append({
                    "agent_name": agent.name,
                    "input": current_input,
                    "output": agent_output,
                    "step": i + 1
                })
                
                current_input = agent_output

                self._log(f"{blue}Agent {agent.name} completed. Output: {agent_output}{reset}")

            return WorkflowResult(
                success=True,
                final_output=current_input,
                agent_outputs=agent_outputs
            )
            
        except Exception as e:
            self._log(f"{blue}Error in sequential workflow: {str(e)}{reset}", "error")
            return WorkflowResult(
                success=False,
                final_output="",
                agent_outputs=agent_outputs,
                error=str(e)
            )

    def _run_supervised(self, input_data: str) -> WorkflowResult:
        """
        Executes agents under supervision of a manager agent that decides the flow.
        """
        self._log(f"{blue}Starting supervised workflow with manager: {self.manager_agent.name}{reset}")
        
        agent_outputs = []
        iteration = 0
        current_context = {
            "original_input": input_data,
            "completed_tasks": [],
            "available_agents": [agent.name for agent in self.agents],
            "current_status": "starting"
        }
        
        try:
            while iteration < self.max_iterations:
                iteration += 1
                self._log(f"{blue}Supervision iteration {iteration}/{self.max_iterations}{reset}")
                
                manager_prompt = self._create_manager_prompt(current_context)
                manager_decision = self.manager_agent.run(manager_prompt)
                
                decision = self._parse_manager_decision(manager_decision)

                self._log(f"{blue}Manager decision: {decision}{reset}")
                
                if decision["action"] == "complete":
                    self._log(f"{blue}Manager decided to complete the workflow{reset}")
                    return WorkflowResult(
                        success=True,
                        final_output=decision.get("final_answer", manager_decision),
                        agent_outputs=agent_outputs
                    )
                
                elif decision["action"] == "delegate":
                    agent_name = decision.get("agent_name")
                    task_input = decision.get("task_input", input_data)
                    
                    # Find and execute the specified agent
                    target_agent = self._find_agent_by_name(agent_name)
                    if target_agent:
                        self._log(f"{blue}Manager delegating to agent: {agent_name}{reset}")
                        
                        agent_output = target_agent.run(task_input)
                        agent_outputs.append({
                            "agent_name": agent_name,
                            "input": task_input,
                            "output": agent_output,
                            "iteration": iteration,
                            "delegated_by": "manager"
                        })

                        self._log(f"{blue}Agent {agent_name} completed. Output: {agent_output}{reset}")
                        
                        current_context["completed_tasks"].append({
                            "agent": agent_name,
                            "input": task_input,
                            "output": agent_output,
                            "iteration": iteration
                        })
                        current_context["current_status"] = f"completed_task_with_{agent_name}"
                    else:
                        self._log(f"{blue}Agent {agent_name} not found{reset}", "warning")
                        current_context["current_status"] = f"agent_{agent_name}_not_found"
                
                else:
                    self._log(f"{blue}Unknown manager action: {decision.get('action')}{reset}", "warning")
                    current_context["current_status"] = "unknown_action"

            self._log(f"{blue}Max iterations reached in supervised mode{reset}", "warning")
            return WorkflowResult(
                success=False,
                final_output="Workflow incomplete: maximum iterations reached",
                agent_outputs=agent_outputs,
                error="Maximum iterations reached"
            )
            
        except Exception as e:
            self._log(f"{blue}Error in supervised workflow: {str(e)}", "error")
            return WorkflowResult(
                success=False,
                final_output="",
                agent_outputs=agent_outputs,
                error=str(e)
            )

    def _create_manager_prompt(self, context: Dict[str, Any]) -> str:
        """Creates a prompt for the manager agent based on current context."""
        return f"""
You are a workflow manager coordinating multiple AI agents. Your job is to decide what should happen next.

Original user input: {context['original_input']}
Available agents: {', '.join(context['available_agents'])}
Current status: {context['current_status']}

Completed tasks so far:
{json.dumps(context['completed_tasks'], indent=2)}

You must respond with a JSON object containing one of these actions:

1. To delegate a task to an agent:
{{
    "action": "delegate",
    "agent_name": "agent_name_here",
    "task_input": "specific input for the agent",
    "reasoning": "why you chose this agent and task"
}}

2. To complete the workflow:
{{
    "action": "complete",
    "final_answer": "the final response to the user",
    "reasoning": "why the workflow is complete"
}}

Choose wisely based on the context and completed tasks.
"""

    def _parse_manager_decision(self, decision_text: str) -> Dict[str, Any]:
        """Parses the manager's decision from text response."""
        try:
            decision_json = self._extract_json(decision_text)
            if decision_json and isinstance(decision_json, dict):
                return decision_json
        except:
            pass
        
        if "complete" in decision_text.lower():
            return {"action": "complete", "final_answer": decision_text}
        
        return {"action": "unknown", "raw_response": decision_text}

    def _extract_json(self, text: str) -> dict | None:
        """Extracts JSON from text (reusing the Agent's method)."""
        try:
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            return json.loads(text)
        except Exception:
            return None

    def _find_agent_by_name(self, name: str) -> Optional[Agent]:
        """Finds an agent by name."""
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None
    
    def run(self, input_data: str) -> WorkflowResult:
        """
        Executes the workflow based on the configured mode.
        
        ## Params:
        - input_data (str): The initial input to the workflow.
        
        ## Returns:
        - WorkflowResult: Contains success status, final output, and detailed agent outputs.
        """
        self._log(f"{blue}Starting workflow '{self.name}' in {self.mode.value} mode{reset}")
        
        if self.mode == WorkflowMode.SEQUENTIAL:
            return self._run_sequential(input_data)
        elif self.mode == WorkflowMode.SUPERVISED:
            return self._run_supervised(input_data)
        else:
            return WorkflowResult(
                success=False,
                final_output="",
                agent_outputs=[],
                error=f"Unsupported workflow mode: {self.mode.value}"
            )

    def add_agent(self, agent: Agent):
        """Adds an agent to the workflow."""
        if agent not in self.agents:
            self.agents.append(agent)
            self._log(f"{blue}Added agent: {agent.name}{reset}")

    def remove_agent(self, agent_name: str) -> bool:
        """Removes an agent from the workflow by name."""
        for i, agent in enumerate(self.agents):
            if agent.name == agent_name:
                removed_agent = self.agents.pop(i)
                self._log(f"{blue}Removed agent: {removed_agent.name}{reset}")
                return True
        return False
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Returns a summary of the workflow configuration."""
        return {
            "name": self.name,
            "mode": self.mode.value,
            "agent_count": len(self.agents),
            "agent_names": [agent.name for agent in self.agents],
            "has_manager": self.manager_agent is not None,
            "manager_name": self.manager_agent.name if self.manager_agent else None,
            "max_iterations": self.max_iterations,
        }
