# Log Analyzer Agent

A command-line tool that analyzes server log files, and an AI agent built on top of it that answers questions about a log by choosing which analysis tools to run.

The project started as a plain Python log parser and grew, step by step, into an agent: a language model (Gemini) that receives a question, decides which of my functions to call, reads their results, and writes a structured report.

## What it does

**`analyzer.py`: the core analysis**
- Reads a log file and counts errors by type
- Ranks the most common errors, breaking ties by severity
- Filters log lines by date
- Saves results to CSV (`error_summary.csv`, `date_lines.csv`)
- Sends the top errors to Gemini for a short explanation and suggested fixes

**`agent.py`: the agent**
- Takes a log file and a question in plain language
- The model chooses which tools to call and with which arguments
- Returns a report with a fixed structure (summary, findings, recommendations) and saves it to `report.md`

## How the agent works

The model never sees my code or the log file. It only sees a short description of each tool. When it wants data, it asks for a tool by name; my code runs the matching Python function and sends the result back. This repeats until the model writes a final answer.

```
send question + tool descriptions
loop (up to MAX_ROUNDS):
    model asked for a tool?  -> run it, send the result back
    no tool request?         -> final answer, stop
```

| Tool | Arguments | Returns |
|---|---|---|
| `get_error_counts` | `log_path` | How many times each error appeared |
| `get_most_common` | `log_path`, `num` (optional, default 5) | Most frequent errors, ties broken by severity |
| `get_logs_in_date` | `log_path`, `wanted_date` (`YYYY-MM-DD`) | All log lines from that date |

Design decisions worth noting:
- **Round limit.** `MAX_ROUNDS` stops an agent that keeps requesting tools. The limit is checked *before* sending a tool result, so the code never pays for a response it will not read.
- **Unknown tools.** If the model asks for a tool that does not exist, it gets an error message back instead of the program crashing, so it can try again.
- **Grounded numbers.** The system instruction tells the model that every number in the report must come from a tool result, not from its own guess.

## Setup

Requires Python 3 (tested with 3.15) and a Gemini API key.

```
git clone <https://github.com/coralTsur/log-analyzer.git>
cd log_analyzer
py -m pip install -r requirements.txt
```

Create a `.env` file in the project folder:

```
GEMINI_API_KEY=your_key_here
```

`.env` is listed in `.gitignore`, so the key is never committed.

## Usage

Analyzer:

```
python analyzer.py app.log
python analyzer.py app.log 2026-10-21
```

Agent (the question is optional; without it the agent gives a general analysis):

```
python agent.py app.log
python agent.py app.log "What were the 3 most common errors?"
python agent.py app.log "What happened on October 21, 2026?"
```

The agent's report is written in Hebrew.

## Log format

Each line is: date, time, level, message.

```
2026-10-20 09:13:45 ERROR Database connection timeout
2026-10-20 09:15:22 WARNING Disk usage at 85%
```

## Tests

```
py -m pytest -v
```

Unit tests for the core functions in `analyzer.py`: error counting, sorting by count, tie-breaking by severity, the `num` limit, filtering by date, and empty results.

One test was written first to expose a real bug: an error type missing from the severity map crashed `most_common` with a `KeyError`. The test failed, the fix (unknown errors get severity 0) made it pass, and it stays in the suite to prevent a regression.

## Project structure

```
analyzer.py        core log analysis and the original CLI
agent.py           tool wrappers, tool descriptions and the agent loop
test_analyzer.py   pytest tests for analyzer.py
app.log            sample log file
requirements.txt   dependencies
```
