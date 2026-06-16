import subprocess
import logging
from typing import Any

logger = logging.getLogger(__name__)


class PrologExecutor:
    """
    Executes Prolog queries using SWI-Prolog via subprocess.

    Compatible with:
        - QA pipeline
        - ingestion-loaded KB files
    """

    def __init__(self, kb_path: str):
        self.kb_path = kb_path

        # sanity check
        if not kb_path.endswith(".pl"):
            raise ValueError("KB must be a .pl file")

    def run(self, query: str) -> Any:
        """
        Execute a Prolog query against the loaded KB.

        Args:
            query: Prolog query string (e.g. "disease(X).")

        Returns:
            Raw Prolog output as string or parsed result
        """

        try:
            # Build SWI-Prolog command
            # -q = quiet
            # -f = file
            # -g = goal
            # -t halt = exit after execution

            cmd = [
                "swipl",
                "-q",
                "-f", self.kb_path,
                "-g", query,
                "-t", "halt"
            ]

            logger.debug(f"Running Prolog command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10  # prevent infinite loops
            )

            if result.returncode != 0:
                logger.error(f"Prolog error: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr.strip()
                }

            output = result.stdout.strip()

            logger.debug(f"Prolog output: {output}")

            return {
                "success": True,
                "output": output if output else "true"
            }

        except subprocess.TimeoutExpired:
            logger.exception("Prolog execution timed out")
            return {
                "success": False,
                "error": "Execution timed out"
            }

        except Exception as e:
            logger.exception("Prolog execution failed")
            return {
                "success": False,
                "error": str(e)
            }