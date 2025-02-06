import subprocess
import sys
import timeit
import tracemalloc
import resource
import re
import json
import os
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import platform
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Backend is running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv("api.env.example")

# Get API credentials
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_JWT_TOKEN = os.getenv("OLLAMA_JWT_TOKEN")
PORT = os.getenv("PORT", "8000")

# File for storing the leaderboard
LEADERBOARD_FILE = "leaderboard.json"
CLEANUP_INTERVAL_SECONDS = 3600
EXPIRATION_DAYS = 7

# Define execution commands for each language
LANGUAGE_COMMANDS = {
    "python": [sys.executable, "-c"],
    "javascript": ["node", "-e"],
    "java": ["java", "Main"],
    "cpp": ["./a.out"],
}

# Ensure leaderboard file exists
if not os.path.exists(LEADERBOARD_FILE):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump([], f)

# Data model for incoming code snippets
class CodeSnippet(BaseModel):
    username: str
    code: str
    language: str

# Set CPU & Memory Limits
def limit_resources():
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))  # Max 2 seconds CPU time
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))  # Max 512MB memory

def get_java_version():
    try:
        version_output = subprocess.run(["java", "-version"], capture_output=True, text=True, stderr=subprocess.STDOUT)
        version_line = version_output.stdout.splitlines()[0]
        java_version = int(version_line.split('"')[1].split(".")[0])  # Extract major version number
        return java_version
    except Exception:
        return 17  # Default to Java 17 if detection fails

def optimize_code_with_deepseek(code: str, language: str) -> str:
    if not OLLAMA_API_URL:
        return "Error: No Ollama API URL provided."

    if not OLLAMA_API_KEY or not OLLAMA_JWT_TOKEN:
        return "Error: Missing API credentials (API Key or JWT Token)."

    headers = {
        "Authorization": f"Bearer {OLLAMA_JWT_TOKEN}",
        "Content-Type": "application/json",
        "x-api-key": OLLAMA_API_KEY
    }

    payload = {
        "model": "deepseek-code",
        "prompt": f"Optimize this {language} code while preserving its functionality:\n{code}",
        "temperature": 0.3,
        "max_tokens": 1024
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, headers=headers)
        response.raise_for_status()

        response_json = response.json()

        if "choices" in response_json:
            optimized_code = response_json.get("choices", [{}])[0].get("text", "").strip()
        elif "response" in response_json:
            optimized_code = response_json["response"].strip()
        else:
            optimized_code = None

        return optimized_code if optimized_code else "⚠️ Error: No valid response from DeepSeek."

    except requests.exceptions.HTTPError as http_err:
        return f"HTTP Error: {http_err}"
    except requests.exceptions.ConnectionError:
        return "Error: Failed to connect to DeepSeek API."
    except requests.exceptions.Timeout:
        return "Error: DeepSeek API request timed out."
    except requests.exceptions.RequestException as e:
        return f"Error calling DeepSeek API: {str(e)}"

def execute_code_safely(code, language):
    if language not in LANGUAGE_COMMANDS:
        return {"error": "Unsupported language"}

    try:
        tracemalloc.start()
        start_time = timeit.default_timer()

        is_macos = platform.system() == "Darwin"
        is_windows = platform.system() == "Windows"

        # Execute the code using subprocess
        if language == "python":
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True, text=True, timeout=2,
                preexec_fn=None if is_macos or is_windows else limit_resources
            )
        elif language == "javascript":
            result = subprocess.run(
                ["node", "-e", code],
                capture_output=True, text=True, timeout=2,
                preexec_fn=None if is_macos or is_windows else limit_resources
            )
        elif language == "java":
            result = subprocess.run(
                ["java", "Main"],
                capture_output=True, text=True, timeout=2
            )
        elif language == "cpp":
            result = subprocess.run(
                ["./a.out"],
                capture_output=True, text=True, timeout=2
            )
        else:
            return {"error": "Unsupported language"}

        end_time = timeit.default_timer()
        memory_used = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()

        if result.returncode != 0:
            return {"error": f"Runtime Error:\n{result.stderr.strip()}"}

        return {
            "runtime": round(end_time - start_time, 4),
            "memory": memory_used // 1024,
            "output": result.stdout.strip()
        }

    except subprocess.TimeoutExpired:
        return {"error": "Code execution timed out (infinite loop or too slow)."}
    except FileNotFoundError:
        return {"error": "Execution file not found. Ensure compilation was successful."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@app.post("/analyze")
def analyze_code(snippet: CodeSnippet):
    code = snippet.code.strip()
    language = snippet.language.lower()
    username = snippet.username.strip()

    if not code or not username:
        raise HTTPException(status_code=400, detail="Code snippet and username cannot be empty.")

    # Performance Evaluation
    performance = execute_code_safely(code, language)

    if "error" in performance:
        return {"error": performance["error"]}

    # Readability Analysis
    results = {
        "comments_score": evaluate_comments(code),
        "formatting_score": evaluate_formatting(code),
        "naming_score": evaluate_naming_conventions(code),
        "complexity_score": evaluate_complexity(code),
    }

    total_score = sum(results.values()) // len(results)
    suggestions = generate_suggestions(results)

    # Update Leaderboard
    update_leaderboard(username, code, language, total_score, performance)

    return {
        "username": username,
        "readability_score": total_score,
        "breakdown": results,
        "suggestions": suggestions,
        "runtime": f"{performance['runtime']} seconds",
        "memory": f"{performance['memory']} KB",
        "output": performance["output"]
    }

@app.post("/optimize")
def optimize_code(snippet: CodeSnippet):

    optimized_code = optimize_code_with_deepseek(snippet.code, snippet.language)

    if "Error" in optimized_code:
        raise HTTPException(status_code=500, detail=optimized_code)

    return {
        "username": snippet.username,
        "original_code": snippet.code,
        "optimized_code": optimized_code,
        "language": snippet.language
    }

@app.get("/leaderboard")
def get_leaderboard():
    return {"leaderboard": load_leaderboard()}

def load_leaderboard():
    with open(LEADERBOARD_FILE, "r") as f:
        return json.load(f)

def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f, indent=4)

def update_leaderboard(username, code, language, score, performance):
    leaderboard = load_leaderboard()
    timestamp = datetime.utcnow().isoformat()

    new_entry = {
        "username": username,
        "code": code,
        "language": language,
        "score": score,
        "runtime": performance["runtime"],
        "memory": performance["memory"],
        "timestamp": timestamp
    }
    leaderboard.append(new_entry)

    # Sort leaderboard by highest score
    leaderboard = sorted(leaderboard, key=lambda x: x["score"], reverse=True)
    leaderboard = leaderboard[:3]
    save_leaderboard(leaderboard)

async def cleanup_leaderboard():
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)  # Wait 1 hour
        leaderboard = load_leaderboard()
        cutoff_time = datetime.utcnow() - timedelta(days=EXPIRATION_DAYS)

        new_leaderboard = [
            entry for entry in leaderboard
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]

        if len(new_leaderboard) != len(leaderboard):
            save_leaderboard(new_leaderboard)
            print(f"🔥 Cleanup: Removed {len(leaderboard) - len(new_leaderboard)} old entries")

# Run Cleanup Task in the Background
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_leaderboard())

# Readability Evaluation Functions
def evaluate_comments(code):
    comment_lines = sum(1 for line in code.splitlines() if line.strip().startswith("#") or "//" in line)
    total_lines = len(code.splitlines())
    if total_lines == 0:
        return 0
    ratio = comment_lines / total_lines
    return int(min(100, ratio * 200))

def evaluate_formatting(code):
    lines = code.splitlines()
    long_lines = sum(1 for line in lines if len(line) > 80)
    improper_indent = sum(1 for line in lines if line.startswith(" ") and len(line) % 4 != 0)
    penalty = long_lines * 2 + improper_indent * 3
    return max(0, 100 - penalty)

def evaluate_naming_conventions(code):
    variables = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", code)
    bad_names = sum(1 for name in variables if len(name) < 3 or name.isupper() or "_" not in name)
    penalty = bad_names * 2
    return max(0, 100 - penalty)

def evaluate_complexity(code):
    nesting_levels = max([line.count("{") - line.count("}") for line in code.splitlines()], default=0)
    return max(0, 100 - nesting_levels * 10)

def generate_suggestions(results):
    suggestions = []
    if results["comments_score"] < 50:
        suggestions.append("Add more meaningful comments to explain your code.")
    if results["formatting_score"] < 70:
        suggestions.append("Fix inconsistent formatting, long lines, or incorrect indentation.")
    return suggestions
