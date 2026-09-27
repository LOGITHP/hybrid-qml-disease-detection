"""Command-line interface for the AI Biomedical Data Preprocessing Agent."""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import typer
from typing_extensions import Annotated
from typing import Optional
from app.agent.preprocessing_agent import PreprocessingAgent
from app.utils.file_utils import load_yaml

cli = typer.Typer(
    name="ai-preprocessing-agent",
    help="AI-Powered Biomedical Data Preprocessing and Feature Engineering Agent."
)


@cli.command()
def main(
    dataset: Annotated[Path, typer.Option("--dataset", "-d", help="Path to input dataset file (CSV).", exists=True)],
    config: Annotated[Optional[Path], typer.Option("--config", "-c", help="Path to YAML configuration file.")] = None,
    mode: Annotated[Optional[str], typer.Option("--mode", "-m", help="Execution mode: 'auto' or 'approval'.")] = None,
    target_column: Annotated[Optional[str], typer.Option("--target-column", "-t", help="Target column name.")] = None,
    feature_count: Annotated[Optional[int], typer.Option("--feature-count", "-f", help="Target feature count (e.g. 4 for VQC).")] = None,
    output_dir: Annotated[Optional[Path], typer.Option("--output-dir", "-o", help="Directory for output artifacts.")] = None,
):
    """Executes end-to-end preprocessing, validation, and artifact generation."""
    print("=" * 65)
    print("AI BIOMEDICAL DATA PREPROCESSING & FEATURE ENGINEERING AGENT")
    print("=" * 65)
    print(f"Dataset:       {dataset}")
    print(f"Config File:   {config or 'Default'}")
    print(f"Mode:          {mode or 'From Config'}")
    print(f"Target Column: {target_column or 'Auto-Detect'}")
    print(f"Feature Count: {feature_count or 'From Config'}")
    print(f"Output Dir:    {output_dir or 'data/output'}")
    print("=" * 65 + "\n")

    cfg = load_yaml(config) if config else {}
    agent = PreprocessingAgent(config=cfg)

    interactive = (mode == "approval" or (mode is None and cfg.get("agent", {}).get("mode") == "approval"))

    try:
        result = agent.run(
            dataset_path=dataset,
            target_column=target_column,
            feature_count=feature_count,
            mode=mode,
            output_dir=str(output_dir) if output_dir else None,
            interactive_prompt=interactive
        )

        print("\n" + "=" * 65)
        print("AGENT WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 65)
        print(f"Run ID:            {result.run_id}")
        print(f"Status:            {result.status.upper()}")
        print(f"Target Column:     {result.target_column}")
        print(f"Task Type:         {result.task_type}")
        print(f"Selected Features: {result.feature_selection.selected_features if result.feature_selection else []}")
        print(f"Validation:        {result.validation.status.upper() if result.validation else 'N/A'}")
        print("\nArtifacts Saved:")
        for name, path in result.output_files.items():
            print(f"  • {name:28s} -> {path}")
        print("=" * 65 + "\n")

    except Exception as e:
        print(f"\n❌ Execution Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=1)


if __name__ == "__main__":
    cli()
