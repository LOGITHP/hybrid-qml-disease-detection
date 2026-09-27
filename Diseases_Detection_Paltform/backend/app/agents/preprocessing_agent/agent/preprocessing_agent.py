"""Clean service interface wrapping LangGraph workflow for API and CLI integration."""

import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Union
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from .graph import build_preprocessing_graph
from .state import PreprocessingState
from ..schemas.dataset import DatasetAnalysis
from ..schemas.preprocessing import PreprocessingPlan
from ..schemas.result import AgentRunResult
from ..utils.file_utils import load_yaml
from ..utils.reproducibility import set_seed


class PreprocessingAgent:
    """Production-grade AI Preprocessing Agent for biomedical datasets."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[Union[str, Path]] = None):
        if config_path:
            self.config = load_yaml(config_path)
        else:
            self.config = config or {}

        # Set reproducibility seed
        seed = self.config.get("split", {}).get("random_state", 42)
        set_seed(seed)

        self.checkpointer = MemorySaver()
        self.workflow = build_preprocessing_graph()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)

        self.current_state: Optional[PreprocessingState] = None
        self.thread_id: str = str(uuid.uuid4())
        self.run_id: str = self.thread_id

    def run(
        self,
        dataset_path: Union[str, Path],
        target_column: Optional[str] = None,
        feature_count: Optional[int] = None,
        mode: Optional[str] = None,
        output_dir: Optional[str] = None,
        interactive_prompt: bool = False
    ) -> AgentRunResult:
        """Executes the complete preprocessing workflow.

        Args:
            dataset_path: Path to raw dataset CSV/format.
            target_column: Optional target override.
            feature_count: Optional target feature count override (e.g. 4 for VQC).
            mode: 'auto' or 'approval'.
            output_dir: Directory to save processed outputs.
            interactive_prompt: If True and paused at approval gate, prompts user via CLI.

        Returns:
            AgentRunResult containing complete structured execution details.
        """
        # Apply runtime overrides
        cfg = dict(self.config)
        if target_column:
            cfg.setdefault("task", {})["target_column"] = target_column
        if feature_count is not None:
            cfg.setdefault("feature_selection", {})["target_feature_count"] = feature_count
        if mode:
            cfg.setdefault("agent", {})["mode"] = mode
        if output_dir:
            cfg["output_dir"] = output_dir

        thread_config = {"configurable": {"thread_id": self.thread_id}}

        # Normalize dataset path to clean relative path
        norm_path = Path(dataset_path)
        try:
            rel_path = norm_path.relative_to(Path.cwd()).as_posix()
        except ValueError:
            rel_path = norm_path.as_posix()

        initial_state: PreprocessingState = {
            "run_id": self.run_id,
            "dataset_path": rel_path,
            "config": cfg,
            "max_retries": cfg.get("validation", {}).get("max_retries", 3),
            "retry_count": 0,
            "executed_operations": [],
            "warnings": [],
            "errors": [],
            "fitted_transformers": {},
            "approval_status": "approved" if cfg.get("agent", {}).get("mode") == "auto" else "pending"
        }

        # Step 1: Run graph
        result_state = self.app.invoke(initial_state, config=thread_config)

        # Check if paused at interrupt (Approval Gate)
        snapshot = self.app.get_state(thread_config)
        if snapshot.next and "approval_gate" in snapshot.next:
            interrupt_val = snapshot.tasks[0].interrupts[0].value if snapshot.tasks and snapshot.tasks[0].interrupts else {}
            
            if interactive_prompt:
                print("\n" + "=" * 60)
                print("HUMAN-IN-THE-LOOP APPROVAL REQUIRED")
                print("=" * 60)
                print(f"Target Column: {interrupt_val.get('target_column')}")
                print(f"Task Type:     {interrupt_val.get('task_type')}")
                print(f"Summary:       {interrupt_val.get('plan_summary')}")
                print("\nProposed Operations:")
                for op in interrupt_val.get("operations", []):
                    print(f"  • {op}")
                if interrupt_val.get("warnings"):
                    print("\nWarnings:")
                    for w in interrupt_val.get("warnings"):
                        print(f"  ⚠️ {w}")
                print("=" * 60)

                choice = input("\nApprove preprocessing plan and execute? [Y/n]: ").strip().lower()
                approved_response = "approved" if choice in ["", "y", "yes"] else "rejected"
            else:
                approved_response = "approved"

            # Resume execution with user response
            result_state = self.app.invoke(Command(resume=approved_response), config=thread_config)

        self.current_state = result_state
        return result_state.get("final_result")

    def analyze(self, dataset_path: Union[str, Path]) -> DatasetAnalysis:
        """Inspects and profiles dataset without executing preprocessing."""
        res = self.run(dataset_path=dataset_path, mode="approval")
        return res.dataset_analysis

    def get_result(self) -> Optional[AgentRunResult]:
        """Returns the current execution result."""
        if self.current_state:
            return self.current_state.get("final_result")
        return None

    def get_report(self) -> Optional[str]:
        """Returns the generated Markdown report."""
        if self.current_state:
            return self.current_state.get("final_report")
        return None
