from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from .agent import Agent
import json
import logging
import re

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("composio").setLevel(logging.WARNING)

BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
PURPLE = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
RESET = "\033[0m"

class WorkflowMode(Enum):
    SEQUENTIAL = "sequential"
    SUPERVISED = "supervised"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"

class WorkflowResult:
    def __init__(self, success: bool, final_output: str, agent_outputs: List[Dict[str, Any]], error: Optional[str] = None):
        """
        Workflow execution result container.
        
        Args:
            success (bool): Whether workflow completed successfully
            final_output (str): Final workflow output
            agent_outputs (List[Dict[str, Any]]): List of agent execution results
            error (Optional[str]): Error message if workflow failed
        """
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
        Initialize a multi-agent workflow orchestrator.
        
        Args:
            name (str): Workflow identifier name
            agents (List[Agent]): List of worker agents
            mode (Literal["sequential", "supervised"]): Execution mode
            manager_agent (Optional[Agent]): Manager agent for supervised mode
            max_iterations (int): Maximum iterations for supervised mode
            enable_logging (bool): Enable detailed logging
            
        Raises:
            ValueError: If configuration is invalid
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
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"Workflow-{name}")
        self.logger.setLevel(logging.WARNING) 
        
        self._log(f"\n{BOLD}{PURPLE}🌊 WORKFLOW INITIALIZED: {name.upper()}{RESET}")
        self._log(f"{CYAN}   📋 Mode: {mode.upper()}{RESET}")
        self._log(f"{CYAN}   👥 Agents: {len(agents)} workers{RESET}")
        
        if manager_agent:
            self._log(f"{YELLOW}   👨‍💼 Manager: {manager_agent.name}{RESET}")
        
        self._log(f"{GREEN}   ✅ Workflow ready for execution{RESET}\n")

    def _log(self, message: str, level: str = "info"):
        """
        Log workflow-specific messages with console output.
        
        Args:
            message (str): Message to log
            level (str): Logging level (info, warning, error)
        """
        print(message)
        if hasattr(self, 'logger'):
            getattr(self.logger, level)(message)

    def _run_sequential(self, input_data: str) -> WorkflowResult:
        """
        Execute agents sequentially, passing output from one to next.
        
        Args:
            input_data (str): Initial input for the workflow
            
        Returns:
            WorkflowResult: Result of sequential execution
        """
        self._log(f"{BOLD}{BLUE}🔄 SEQUENTIAL EXECUTION STARTED{RESET}")
        self._log(f"{CYAN}   📊 Pipeline: {len(self.agents)} agents{RESET}")
        
        agent_outputs = []
        current_input = input_data
        
        try:
            for i, agent in enumerate(self.agents):
                self._log(f"\n{BOLD}{PURPLE}{'='*60}{RESET}")
                self._log(f"{BOLD}{PURPLE}🎯 STEP {i+1}/{len(self.agents)}: {agent.name.upper()}{RESET}")
                self._log(f"{BOLD}{PURPLE}{'='*60}{RESET}")

                agent_output = agent.run(current_input)
                
                agent_outputs.append({
                    "agent_name": agent.name,
                    "input": current_input,
                    "output": agent_output,
                    "step": i + 1
                })
                
                current_input = agent_output
                self._log(f"{GREEN}✅ Step {i+1} completed successfully{RESET}")

            self._print_workflow_result(current_input, True)
            
            return WorkflowResult(
                success=True,
                final_output=current_input,
                agent_outputs=agent_outputs
            )
            
        except Exception as e:
            error_msg = f"Sequential workflow failed: {str(e)}"
            self._log(f"{RED}❌ WORKFLOW ERROR: {error_msg}{RESET}", "error")
            return WorkflowResult(
                success=False,
                final_output="",
                agent_outputs=agent_outputs,
                error=str(e)
            )

    def _run_supervised(self, input_data: str) -> WorkflowResult:
        """
        Execute agents under manager supervision with dynamic routing.
        
        Args:
            input_data (str): Initial input for the workflow
            
        Returns:
            WorkflowResult: Result of supervised execution
        """
        self._log(f"{BOLD}{BLUE}🎯 SUPERVISED EXECUTION STARTED{RESET}")
        self._log(f"{YELLOW}   👨‍💼 Manager: {self.manager_agent.name}{RESET}")
        self._log(f"{CYAN}   🔄 Max iterations: {self.max_iterations}{RESET}")
        
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
                self._log(f"\n{BOLD}{PURPLE}{'='*60}{RESET}")
                self._log(f"{BOLD}{PURPLE}🔍 SUPERVISION ROUND {iteration}/{self.max_iterations}{RESET}")
                self._log(f"{BOLD}{PURPLE}{'='*60}{RESET}")
                
                manager_prompt = self._create_manager_prompt(current_context)
                manager_decision = self.manager_agent.run(manager_prompt)
                
                decision = self._parse_manager_decision(manager_decision)
                self._log(f"{CYAN}🤔 Manager Decision: {decision.get('action', 'unknown').upper()}{RESET}")
                
                if decision["action"] == "complete":
                    self._log(f"{GREEN}🏁 Manager completed the workflow{RESET}")
                    final_answer = decision.get("final_answer", manager_decision)
                    self._print_workflow_result(final_answer, True)
                    
                    return WorkflowResult(
                        success=True,
                        final_output=final_answer,
                        agent_outputs=agent_outputs
                    )
                
                elif decision["action"] == "delegate":
                    agent_name = decision.get("agent_name")
                    task_input = decision.get("task_input", input_data)
                    
                    target_agent = self._find_agent_by_name(agent_name)
                    if target_agent:
                        self._log(f"{CYAN}👉 Delegating to: {agent_name}{RESET}")
                        
                        agent_output = target_agent.run(task_input)
                        
                        agent_outputs.append({
                            "agent_name": agent_name,
                            "input": task_input,
                            "output": agent_output,
                            "iteration": iteration,
                            "delegated_by": "manager"
                        })
                        
                        current_context["completed_tasks"].append({
                            "agent": agent_name,
                            "input": task_input,
                            "output": agent_output,
                            "iteration": iteration
                        })
                        current_context["current_status"] = f"completed_task_with_{agent_name}"
                        
                        self._log(f"{GREEN}✅ Delegation completed{RESET}")
                    else:
                        self._log(f"{RED}❌ Agent '{agent_name}' not found{RESET}", "error")
                        current_context["current_status"] = f"agent_{agent_name}_not_found"
                
                else:
                    self._log(f"{YELLOW}⚠️  Unknown manager action: {decision.get('action')}{RESET}", "warning")
                    current_context["current_status"] = "unknown_action"

            error_msg = "Maximum iterations reached"
            self._log(f"{RED}⏰ WORKFLOW TIMEOUT: {error_msg}{RESET}", "warning")
            self._print_workflow_result("Workflow incomplete: maximum iterations reached", False)
            
            return WorkflowResult(
                success=False,
                final_output="Workflow incomplete: maximum iterations reached",
                agent_outputs=agent_outputs,
                error="Maximum iterations reached"
            )
            
        except Exception as e:
            error_msg = f"Supervised workflow failed: {str(e)}"
            self._log(f"{RED}❌ WORKFLOW ERROR: {error_msg}{RESET}", "error")
            return WorkflowResult(
                success=False,
                final_output="",
                agent_outputs=agent_outputs,
                error=str(e)
            )

    def _print_workflow_result(self, final_output: str, success: bool):
        """
        Print beautifully formatted workflow result.
        
        Args:
            final_output (str): Final workflow output
            success (bool): Whether workflow succeeded
        """
        color = GREEN if success else RED
        status = "SUCCESS" if success else "FAILED"
        icon = "🎉" if success else "💥"
        
        self._log(f"\n{BOLD}{color}{'='*80}{RESET}")
        self._log(f"{BOLD}{color}{icon} WORKFLOW '{self.name.upper()}' {status} {icon}{RESET}")
        self._log(f"{BOLD}{color}{'='*80}{RESET}")
        self._log(f"{WHITE}{final_output}{RESET}")
        self._log(f"{BOLD}{color}{'='*80}{RESET}\n")

    def _create_manager_prompt(self, context: Dict[str, Any]) -> str:
        """
        Create decision prompt for manager agent.
        
        Args:
            context (Dict[str, Any]): Current workflow execution context
            
        Returns:
            str: Formatted manager prompt
        """
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
        """
        Parse manager's decision from response text.
        
        Args:
            decision_text (str): Manager's response text
            
        Returns:
            Dict[str, Any]: Parsed decision dictionary
        """
        try:
            decision_json = self._extract_json(decision_text)
            if decision_json and isinstance(decision_json, dict):
                return decision_json
        except:
            pass
        
        if "complete" in decision_text.lower():
            return {"action": "complete", "final_answer": decision_text}
        
        return {"action": "unknown", "raw_response": decision_text}

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON object from text response.
        
        Args:
            text (str): Text containing JSON
            
        Returns:
           Optional[Dict[str, Any]]: Extracted JSON or None if not found
        """
        try:
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            return json.loads(text)
        except Exception:
            return None

    def _find_agent_by_name(self, name: str) -> Optional[Agent]:
        """
        Find agent by name in workflow.
        
        Args:
            name (str): Agent name to search for
            
        Returns:
            Optional[Agent]: Found agent or None
        """
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None
    
    def run(self, input_data: str) -> WorkflowResult:
        """
        Execute the complete workflow based on configured mode.
        
        Args:
            input_data (str): Initial input for the workflow
            
        Returns:
            WorkflowResult: Complete workflow execution result with success status, outputs, and errors
        """
        self._log(f"\n{BOLD}{PURPLE}🚀 WORKFLOW EXECUTION: {self.name.upper()}{RESET}")
        self._log(f"{BLUE}📝 Input: {input_data[:100]}{'...' if len(input_data) > 100 else ''}{RESET}")
        self._log(f"{BLUE}🔧 Mode: {self.mode.value.upper()}{RESET}")
        
        if self.mode == WorkflowMode.SEQUENTIAL:
            return self._run_sequential(input_data)
        elif self.mode == WorkflowMode.SUPERVISED:
            return self._run_supervised(input_data)
        else:
            error_msg = f"Unsupported workflow mode: {self.mode.value}"
            self._log(f"{RED}❌ CONFIGURATION ERROR: {error_msg}{RESET}", "error")
            return WorkflowResult(
                success=False,
                final_output="",
                agent_outputs=[],
                error=error_msg
            )

    def add_agent(self, agent: Agent):
        """
        Add an agent to the workflow.
        
        Args:
            agent (Agent): Agent instance to add
        """
        if agent not in self.agents:
            self.agents.append(agent)
            self._log(f"{GREEN}➕ Agent added: {agent.name}{RESET}")

    def remove_agent(self, agent_name: str) -> bool:
        """
        Remove an agent from workflow by name.
        
        Args:
            agent_name (str): Name of agent to remove
            
        Returns:
            bool: True if agent was found and removed
        """
        for i, agent in enumerate(self.agents):
            if agent.name == agent_name:
                removed_agent = self.agents.pop(i)
                self._log(f"{RED}➖ Agent removed: {removed_agent.name}{RESET}")
                return True
        return False
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive workflow configuration summary.
        
        Returns:
            Dict[str, Any]: Dictionary containing workflow configuration details
        """
        return {
            "name": self.name,
            "mode": self.mode.value,
            "agent_count": len(self.agents),
            "agent_names": [agent.name for agent in self.agents],
            "has_manager": self.manager_agent is not None,
            "manager_name": self.manager_agent.name if self.manager_agent else None,
            "max_iterations": self.max_iterations,
        }
