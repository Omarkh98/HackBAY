# devguard_cli.py
import typer
import requests
import os
import subprocess # For running shell scripts
import json
import logging
from pathlib import Path
import shutil
import tempfile

# Configure basic logging for the CLI (optional)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Configuration ---
# Best to get API_BASE_URL from an environment variable or a config file
# For simplicity here, using an environment variable with a default.
API_BASE_URL = os.getenv("DEVGUARD_API_URL", "http://localhost:8000")

# Create the Typer application
app = typer.Typer(
    name="devguard",
    help="DevGuardAI: Your intelligent compliance, sustainability, and documentation co-pilot.",
    add_completion=True # Enables shell completion
)

# --- Callback function for executable check ---
def _validate_executable(ctx: typer.Context, param: typer.CallbackParam, value: Path):
    """Callback to validate if a path is an executable file."""
    if value is None: # If the option is not provided (e.g. if it had a default of None and wasn't specified)
        return None
    # Typer already handles exists, file_okay, readable if specified in Option.
    # We just add the executable check.
    # Note: exists=True and file_okay=True should ideally be on the Option itself.
    if not value.exists(): # Should be caught by exists=True, but good to be robust
        raise typer.BadParameter(f"File not found: {value}", ctx=ctx, param=param)
    if not value.is_file(): # Should be caught by file_okay=True
        raise typer.BadParameter(f"Path is not a file: {value}", ctx=ctx, param=param)
    if not os.access(str(value), os.X_OK):
        raise typer.BadParameter(f"File is not executable: {value}", ctx=ctx, param=param)
    return value

# --- Helper function for making API requests ---
def _call_api(method: str, endpoint: str, data: dict = None, files: dict = None, params: dict = None) -> dict:
    """Helper to make requests to the DevGuard AI API."""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"accept": "application/json"}
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, data=data, files=files, timeout=120) # Increased timeout for potentially long operations
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()  # Will raise an HTTPError for bad responses (4XX or 5XX)
        return response.json()
    except requests.exceptions.ConnectionError:
        typer.secho(f"Error: Could not connect to DevGuard AI service at {url}. Please ensure it's running.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except requests.exceptions.HTTPError as e:
        typer.secho(f"API Error ({e.response.status_code}): {e.response.text}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except requests.exceptions.RequestException as e:
        typer.secho(f"Request failed: {str(e)}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except json.JSONDecodeError:
        typer.secho(f"Error: Could not decode JSON response from API: {response.text}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

# --- CLI Commands ---

@app.command("create-documentation")
def cli_create_documentation(
    file_path: Path = typer.Option(..., "--file", "-f", help="Path to the source code file.", exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True),
    language: str = typer.Option(..., "--lang", "-l", help="Programming language of the file (e.g., java, python, javascript).")
):
    """
    Generates documentation stubs for a given source code file using DevGuard AI.
    """
    typer.echo(f"Requesting documentation for '{file_path}' (language: {language})...")
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            code_content = f.read()
    except Exception as e:
        typer.secho(f"Error reading file {file_path}: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    payload = {"code_snippet": code_content, "language": language, "analysis_type": "documentation"}
    response = _call_api("POST", "/analyze", data=payload)

    if response and response.get("documentation_stubs"):
        typer.secho("Generated Documentation Stub:", fg=typer.colors.GREEN)
        typer.echo(response["documentation_stubs"])
    elif response and response.get("errors"):
        typer.secho("Errors:", fg=typer.colors.RED, err=True)
        for error in response["errors"]:
            typer.echo(f"- {error}", err=True)
    else:
        typer.secho("No documentation generated or unexpected response.", fg=typer.colors.YELLOW)

@app.command("license-check")
def cli_license_check(
    script_path: Path = typer.Option(
        None,
        "--script",
        help="Path to an external license checking shell script (optional).",
        exists=True,      # Typer handles this
        file_okay=True,   # Typer handles this
        dir_okay=False,   # Typer handles this
        readable=True,    # Typer handles this
        resolve_path=True,# Typer handles this
        callback=_validate_executable # Our custom callback for executable check
    ),
    project_path: Path = typer.Option(Path("."), "--project-path", "-p", help="Path to the project directory for analysis.", exists=True, file_okay=False, dir_okay=True, readable=True, resolve_path=True),
    dependency_file: Path = typer.Option(None, "--dep-file", "-d", help="Path to a specific dependency file (e.g., pom.xml, package.json). Overrides project path scan.", exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True)
):
    """
    Checks licenses of dependencies using DevGuard AI.
    Can optionally use an external script for initial scan or analyze specified dependency file.
    """
    # (The rest of your cli_license_check function remains the same)
    typer.echo(f"Initiating license check for project/file at '{dependency_file or project_path}'...")
    payload = {}
    files_to_send = None

    if script_path: # script_path will be None if not provided, or a validated Path object if provided
        typer.echo(f"Running external license script: {script_path}...")
        try:
            process_args = [str(script_path), str(project_path)]
            process = subprocess.run(process_args, capture_output=True, text=True, check=False, timeout=180)
            script_output = process.stdout
            script_error = process.stderr

            if process.returncode != 0:
                typer.secho(f"Warning: License script '{script_path}' exited with code {process.returncode}.", fg=typer.colors.YELLOW, err=True)
                if script_error:
                    typer.secho(f"Script stderr:\n{script_error}", fg=typer.colors.YELLOW, err=True)
            
            if not script_output and not script_error:
                 typer.secho(f"Warning: License script '{script_path}' produced no output.", fg=typer.colors.YELLOW, err=True)

            response = _call_api("POST", "/analyze", data={"analysis_type": "license_from_script", "script_output": script_output})

        except FileNotFoundError: # Should be caught by exists=True now
            typer.secho(f"Error: Script not found at {script_path}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        except subprocess.TimeoutExpired:
            typer.secho(f"Error: Script {script_path} timed out.", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        except Exception as e:
            typer.secho(f"Error running script {script_path}: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
    # ... (rest of your function) ...
    elif dependency_file:
        typer.echo(f"Analyzing dependency file: {dependency_file}...")
        try:
            with open(dependency_file, 'rb') as f:
                files_to_send = {'dependencies_file': (os.path.basename(dependency_file), f, 'application/octet-stream')}
            response = _call_api("POST", "/analyze", files=files_to_send, data={"analysis_type": "license_from_file"})
        except Exception as e:
            typer.secho(f"Error processing dependency file {dependency_file}: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
    else:
        typer.secho("Please specify a --script or a --dep-file for license checking.", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)

    if response and response.get("dependency_checks"):
        typer.secho("License Check Results:", fg=typer.colors.BLUE)
        for check in response["dependency_checks"]:
            status_color = typer.colors.GREEN
            if check.get("status", "").lower() == "non-compliant":
                status_color = typer.colors.RED
            elif check.get("status", "").lower() == "conditional":
                status_color = typer.colors.YELLOW

            typer.secho(f"  Library: {check.get('library', 'N/A')}", fg=status_color)
            typer.echo(f"    License: {check.get('identified_license', 'N/A')}")
            typer.echo(f"    Status: {check.get('status', 'N/A')}")
            typer.echo(f"    Notes: {check.get('assessment_detail', 'No details.')}")
    elif response and response.get("errors"):
        typer.secho("Errors:", fg=typer.colors.RED, err=True)
        for error in response["errors"]:
            typer.echo(f"- {error}", err=True)
    else:
        typer.secho("No license check results or unexpected response.", fg=typer.colors.YELLOW)


@app.command("sustainability-check")
def cli_sustainability_check(
    target_path: Path = typer.Option(
        ".", # Default to current directory
        "--path", "-p", # Changed option name for clarity
        help="Path to the Java source code file or directory to analyze.",
        exists=True,
        file_okay=True,
        dir_okay=True,
        readable=True,
        resolve_path=True # Converts to absolute path
    ),
    ruleset: str = typer.Option(
        "category/java/bestpractices.xml", # A default PMD ruleset, can be overridden
        "--ruleset", "-R",
        help="PMD ruleset to use (e.g., path to a ruleset XML file or a PMD built-in ruleset category)."
    )
):
    """
    Checks a Java source code file or directory for sustainability-related
    best practices using PMD and a custom scorer.
    """
    typer.echo(f"Initiating sustainability check for: {target_path}")

    # --- 1. Determine paths to PMD and scorer script ---
    try:
        # Assuming this CLI script is at the root of your installable package,
        # and 'devguard/tools/...' is relative to that.
        # If your CLI script is devguard_cli.py at project root:
        # SCRIPT_DIR = Path(__file__).parent.resolve()
        # If your CLI script is, e.g., devguard_pkg/cli.py (installed from src/devguard_pkg/cli.py):
        # SCRIPT_DIR = Path(__file__).parent.resolve() # this is devguard_pkg/
        # DEVGUARD_PACKAGE_ROOT = SCRIPT_DIR # If your tools are devguard_pkg/devguard/tools... this is wrong.
        
        # Let's assume 'devguard' is the package, and this CLI script is part of it.
        # e.g., devguard/cli.py, and tools are in devguard/tools/
        # This requires your packaging (pyproject.toml, MANIFEST.in) to include these tools.
        package_root = Path(__file__).parent.resolve() # Assuming this script is in the 'devguard' package root or a sub-module.
                                                    # If this script is top-level, then package_root = Path("devguard")
                                                    # This needs to point to where the 'tools' folder is accessible.
                                                    # For robustness, if 'devguard' is an installed package:
        try:
            import devguard # Try to import the main package
            # package_root should point to the directory containing 'tools' if tools is inside 'devguard' package
            # If devguard_cli.py is at the root of the installed "devguard" module/package:
            package_base_path = Path(devguard.__file__).parent
        except ImportError:
            typer.secho("Error: Could not determine 'devguard' package path. Ensure it's installed correctly.", fg=typer.colors.RED, err=True)
            # Fallback assuming script is run from project root or tools are relative to script
            # This part is sensitive to your exact project structure and installation.
            # For an installed package, tools should be relative to the package path.
            # For local dev, relative to script might work.
            # The user's original paths were 'devguard/tools/...'
            # Let's assume the `devguard` directory IS the package, and this script is run from somewhere that
            # can see it, or this script is devguard_cli.py at the HackBAY root.
            # If script is at HackBAY root:
            package_base_path = Path.cwd() / "devguard" # Assuming devguard is a subdir of CWD
            if not (package_base_path / "tools").exists(): # A check
                 package_base_path = Path(__file__).parent / "devguard" # If script is one level above devguard folder

        tools_dir = package_base_path / "tools" / "sustainability_checker"
        pmd_executable_dir = tools_dir / "pmd-bin-7.13.0" / "bin"
        pmd_executable = pmd_executable_dir / "pmd" # For Linux/macOS. For Windows, it's pmd.bat or pmd.cmd
        if os.name == 'nt': # Windows
            pmd_executable = pmd_executable_dir / "pmd.bat" # Or pmd.cmd

        scorer_script = tools_dir / "pmd_scorer.py"

        if not pmd_executable.exists():
            typer.secho(f"Error: PMD executable not found at {pmd_executable}", fg=typer.colors.RED, err=True)
            typer.secho("Please ensure PMD is correctly placed and packaged.", fg=typer.colors.YELLOW, err=True)
            raise typer.Exit(code=1)
        if not scorer_script.exists():
            typer.secho(f"Error: PMD scorer script not found at {scorer_script}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.secho(f"Error determining tool paths: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


    # --- 2. Create a temporary file for the PMD report ---
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as tmp_report_file:
        pmd_report_path_str = tmp_report_file.name
    # We closed it, so PMD can write to it. We'll delete it manually later.

    # --- 3. Construct and run the PMD command ---
    # PMD command structure: pmd check -d <source_path> -R <ruleset_path> -f <format> -r <report_file>
    pmd_cmd = [
        str(pmd_executable),
        "check",
        "-d", str(target_path),
        "-R", ruleset,
        "-f", "xml",
        "-r", pmd_report_path_str,
        # "- मिनिमम-प्राथमिकता", "3" # Example: Set minimum priority (1=High, 5=Low)
        "--no-cache" # Useful for consistent results during testing
    ]

    try:
        pmd_process = subprocess.run(pmd_cmd, capture_output=True, text=True, check=False) # check=False to handle errors manually

        if pmd_process.returncode != 0 and pmd_process.returncode != 4 : # PMD returns 4 if violations are found but no error occurred
            typer.secho(f"PMD execution failed with exit code {pmd_process.returncode}:", fg=typer.colors.RED, err=True)
            if pmd_process.stdout:
                typer.secho("PMD STDOUT:", fg=typer.colors.YELLOW, err=True)
                typer.echo(pmd_process.stdout, err=True)
            if pmd_process.stderr:
                typer.secho("PMD STDERR:", fg=typer.colors.YELLOW, err=True)
                typer.echo(pmd_process.stderr, err=True)
            # os.remove(pmd_report_path_str) # Clean up temp file
            # raise typer.Exit(code=1) # Decide if to exit or try scoring partial report
        elif pmd_process.returncode == 0: # No violations found
             typer.secho("PMD analysis completed. No violations found by the specified ruleset.", fg=typer.colors.GREEN)
             # os.remove(pmd_report_path_str) # Clean up temp file
             # return # Nothing to score
        else: # returncode == 4, violations found
             typer.secho("PMD analysis completed. Violations found.", fg=typer.colors.YELLOW)


        if pmd_process.stderr and " मुख्यतः उपयोग में आने वाली त्रुटियां " in pmd_process.stderr: # Checking for common PMD error patterns
            typer.secho("PMD reported usage errors, check configuration and paths.", fg=typer.colors.RED, err=True)
            typer.echo(pmd_process.stderr, err=True)
            # os.remove(pmd_report_path_str)
            # raise typer.Exit(code=1)


    except FileNotFoundError:
        typer.secho(f"Error: PMD command '{pmd_executable}' not found. Is it in your PATH or packaged correctly?", fg=typer.colors.RED, err=True)
        # os.remove(pmd_report_path_str)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"An unexpected error occurred while running PMD: {e}", fg=typer.colors.RED, err=True)
        # os.remove(pmd_report_path_str)
        raise typer.Exit(code=1)

    # --- 4. Run the pmd_scorer.py script ---
    # Command structure: python <scorer_script_path> <report_file_path>
    # First, ensure the report file actually exists and is not empty
    if not Path(pmd_report_path_str).exists() or Path(pmd_report_path_str).stat().st_size == 0:
        if pmd_process.returncode == 0: # No violations, so empty report is expected
            typer.secho("No PMD violations to score.", fg=typer.colors.GREEN)
            os.remove(pmd_report_path_str)
            return
        else:
            typer.secho(f"PMD report file '{pmd_report_path_str}' is missing or empty, cannot run scorer.", fg=typer.colors.RED, err=True)
            typer.secho("This might be due to PMD errors or no violations found with the current rules.", fg=typer.colors.YELLOW, err=True)
            if pmd_process.stdout: typer.echo(f"PMD STDOUT:\n{pmd_process.stdout}")
            if pmd_process.stderr: typer.echo(f"PMD STDERR:\n{pmd_process.stderr}")
            os.remove(pmd_report_path_str) # Clean up empty/missing report attempt
            raise typer.Exit(code=1)


    scorer_cmd = [
        "python", # Assuming 'python' resolves to your venv's python
        str(scorer_script),
        pmd_report_path_str
    ]

    try:
        scorer_process = subprocess.run(scorer_cmd, capture_output=True, text=True, check=True) # check=True will raise CalledProcessError on non-zero exit
        typer.secho("Sustainability Scorer Output:", fg=typer.colors.CYAN)
        typer.echo(scorer_process.stdout)
        if scorer_process.stderr:
            typer.secho("Scorer STDERR (warnings/info):", fg=typer.colors.YELLOW, err=True)
            typer.echo(scorer_process.stderr, err=True)

    except subprocess.CalledProcessError as e:
        typer.secho(f"PMD Scorer script failed with exit code {e.returncode}:", fg=typer.colors.RED, err=True)
        if e.stdout:
            typer.secho("Scorer STDOUT:", fg=typer.colors.YELLOW, err=True)
            typer.echo(e.stdout, err=True)
        if e.stderr:
            typer.secho("Scorer STDERR:", fg=typer.colors.YELLOW, err=True)
            typer.echo(e.stderr, err=True)
        raise typer.Exit(code=1)
    except FileNotFoundError:
        typer.secho(f"Error: Python interpreter or scorer script '{scorer_script}' not found.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"An unexpected error occurred while running the PMD Scorer: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    finally:
        # --- 5. Clean up the temporary report file ---
        try:
            if Path(pmd_report_path_str).exists():
                os.remove(pmd_report_path_str)
        except OSError as e:
            typer.secho(f"Warning: Could not delete temporary report file {pmd_report_path_str}: {e}", fg=typer.colors.YELLOW, err=True)


@app.command("ask")
def cli_ask(
    query: str = typer.Argument(..., help="Your question for DevGuard AI about guidelines, policies, etc.")
):
    """
    Ask DevGuard AI a question (powered by RAG).
    """
    typer.echo(f"Asking DevGuard AI: \"{query}\"")
    # Ensure your /ask endpoint expects a form data field named 'query' or JSON.
    # If form data:
    response = _call_api("POST", "/ask", data={"query": query})
    # If JSON:
    # response = _call_api("POST", "/ask", data=json.dumps({"query": query}), headers={"Content-Type": "application/json"})


    if response and response.get("answer"):
        typer.secho("DevGuard AI says:", fg=typer.colors.CYAN)
        typer.echo(response["answer"])
    elif response and response.get("error"):
        typer.secho(f"Error from DevGuard AI: {response['error']}", fg=typer.colors.RED, err=True)
    else:
        typer.secho("No answer received or unexpected response.", fg=typer.colors.YELLOW)
        # typer.echo(f"Full API response: {response}", err=True)

@app.command("chat")
def cli_chat(
    app_file_name: str = typer.Option("llm_assistant_ui.py", "--app-file", help="Name of the Streamlit app file within the 'ui' directory of the package."),
    port: int = typer.Option(None, "--port", help="Port to run Streamlit on (e.g., 8501).")
):
    """
    Launches the DevGuard AI Streamlit chat interface.
    """
    streamlit_exe = shutil.which("streamlit")
    if not streamlit_exe:
        typer.secho("Error: Streamlit is not installed or not found in your PATH.", fg=typer.colors.RED, err=True)
        typer.secho("Please install it: pip install streamlit", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)

    try:
        # Determine the path to the packaged Streamlit app
        # This assumes devguard_cli.py and the 'ui' folder (containing app_file_name)
        # are installed together in the site-packages directory.
        # Path(__file__) is the path to the currently executing devguard_cli.py script.
        current_script_path = Path(__file__).resolve()
        # The 'ui' directory should be a sibling to this script's parent if packaged correctly.
        # More accurately, it's relative to the package root.
        # If devguard_cli.py is the module, its parent is the package root.
        streamlit_app_path = current_script_path.parent / "frontend" / app_file_name

        if not streamlit_app_path.exists():
            typer.secho(f"Error: Streamlit app '{streamlit_app_path}' not found.", fg=typer.colors.RED, err=True)
            typer.secho(f"Ensure '{app_file_name}' is in a 'ui' directory and packaged with DevGuard CLI.", fg=typer.colors.YELLOW, err=True)
            typer.secho(f"(Searched at: {streamlit_app_path})", fg=typer.colors.YELLOW, err=True)
            raise typer.Exit(code=1)

        cmd = [streamlit_exe, "run", "devguard/app.py"]
        if port:
            cmd.extend(["--server.port", str(port)])

        typer.echo(f"Launching DevGuard Chat UI: {' '.join(cmd)}")
        typer.echo("You can stop the Streamlit server by pressing Ctrl+C in its terminal window.")

        # subprocess.run will block until the command (Streamlit server) completes.
        # Streamlit typically runs until Ctrl+C is pressed.
        process = subprocess.run(cmd)

        if process.returncode != 0:
            typer.secho(f"Streamlit command exited with error code {process.returncode}.", fg=typer.colors.YELLOW, err=True)

    except Exception as e:
        typer.secho(f"Failed to launch Streamlit app: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()