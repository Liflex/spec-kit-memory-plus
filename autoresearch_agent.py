#!/usr/bin/env python3
"""
Spec Kit AutoResearch Agent

Полноценный автономный агент который:
1. Читает memory и program.md
2. Вызывает Claude API для генерации эксперимента
3. Применяет изменения
4. Оценивает результат
5. Повторяется каждые N минут

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python autoresearch_agent.py --max-experiments 20 --interval-minutes 10

Requirements:
    pip install anthropic python-dotenv requests

Windows:
    .\run_autoresearch.bat
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import argparse
from io import StringIO

try:
    import anthropic
    from dotenv import load_dotenv
    import requests
except ImportError as e:
    print("❌ Установите зависимости:")
    print("   pip install anthropic python-dotenv requests")
    sys.exit(1)

# =============================================================================
# CONFIG
# =============================================================================

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
MAX_EXPERIMENTS = int(os.getenv("AUTORESEARCH_MAX", 100))
MIN_IMPROVEMENT = float(os.getenv("AUTORESEARCH_MIN_IMPROVEMENT", 0.05))
INTERVAL_MINUTES = int(os.getenv("AUTORESEARCH_INTERVAL", "10"))
MODEL = os.getenv("AUTORESEARCH_MODEL", "claude-3-5-sonnet-20241022")
API_KEY = os.getenv("ANTHROPIC_API_KEY")
ENABLE_WEB_SEARCH = os.getenv("AUTORESEARCH_WEB_SEARCH", "true").lower() == "true"

if not API_KEY:
    print("❌ ANTHROPIC_API_KEY не найден")
    print("   export ANTHROPIC_API_KEY='sk-ant-...'")
    print("   Или добавьте в .env файл")
    sys.exit(1)

client = anthropic.Anthropic(api_key=API_KEY)

# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging() -> logging.Logger:
    """Настраивает детальное логирование в файл и консоль."""
    log_dir = PROJECT_ROOT / ".speckit" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"autoresearch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Создаём logger
    logger = logging.getLogger("autoresearch")
    logger.setLevel(logging.DEBUG)

    # File handler - полный лог
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler - важное только
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logging()

# =============================================================================
# WEB SEARCH (без MCP)
# =============================================================================

def web_search(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Простой веб-поиск через DuckDuckGo HTML (без API ключей).

    Args:
        query: Поисковый запрос
        max_results: Максимум результатов

    Returns:
        List of {title, url, snippet}
    """
    try:
        # DuckDuckGo HTML версия не требует API
        url = "https://html.duckduckgo.com/html/"
        params = {"q": query}

        response = requests.post(url, data=params, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        # Простая парсинга результатов
        import re
        results = []

        # Ищем результаты в HTML
        pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        for match in re.finditer(pattern, response.text):
            if len(results) >= max_results:
                break
            url = match.group(1)
            title = match.group(2)
            results.append({
                "title": title,
                "url": url,
                "snippet": f"Result for: {query}"
            })

        return results[:max_results]

    except Exception as e:
        logger.warning(f"Web search failed: {e}")
        return []

def search_context(topic: str) -> str:
    """Ищет контекст по теме для исследования.

    Args:
        topic: Тема для поиска (например, "security best practices 2026")

    Returns:
        Форматированную строку с результатами
    """
    if not ENABLE_WEB_SEARCH:
        return ""

    results = web_search(topic, max_results=3)
    if not results:
        return ""

    context = "\n## Web Search Results\n\n"
    for i, r in enumerate(results, 1):
        context += f"{i}. **{r['title']}**\n"
        context += f"   URL: {r['url']}\n\n"

    return context

# =============================================================================
# FILE UTILS
# =============================================================================

def read_file(path: Path) -> str:
    """Читает файл или возвращает пустую строку."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

def write_file(path: Path, content: str) -> None:
    """Пишет файл с созданием директорий."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.debug(f"Written: {path}")

def append_file(path: Path, content: str) -> None:
    """Добавляет содержимое в файл."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n\n" + content)
    logger.debug(f"Appended to: {path}")

# =============================================================================
# AGENT PROMPTS
# =============================================================================

def build_system_prompt() -> str:
    """Строит system prompt для агента."""
    return """You are an autonomous research agent for Spec Kit project.

Your goal: Improve Spec Kit through iterative experiments.

CRITICAL SAFETY RULES:
- NEVER suggest git push, git commit --amend, git reset --hard
- NEVER delete .claude/memory/ directory
- NEVER make changes outside F:\\IdeaProjects\\spec-kit\\
- ALWAYS ask for confirmation before deleting files
- ALWAYS create git diff before major changes

Your process:
1. Read memory (lessons, patterns, architecture)
2. Research current best practices and solutions
3. Propose an experiment with clear hypothesis
4. Implement the change
5. Report what was changed

IMPORTANT: You can and should use web search functionality to:
- Research current best practices for 2025-2026
- Look up documentation for libraries and frameworks
- Find solutions to technical problems
- Verify your approaches against modern standards

Focus areas (HIGH PRIORITY):
1. Security: JWT, CORS, CSP, helmet.js, secret scanning
2. Performance: bundle size, Lighthouse metrics, caching
3. Testing: mocks, isolation, coverage, test patterns
4. Framework-specific: React hooks, Vue composition, Angular DI

Respond in JSON format with keys:
- hypothesis: what you're testing
- target: what file(s) you're modifying
- changes: list of {file, operation, content}
- reason: why this should improve the product
- experiment_id: unique identifier
- web_search_query: what you searched (if applicable)

Be specific and actionable. Small changes are better than big refactorings."""

def build_user_prompt(iteration: int, memory: Dict[str, str]) -> str:
    """Строит user prompt для агента."""
    program = read_file(PROJECT_ROOT / "program.md")
    context = read_file(PROJECT_ROOT / "research-context.md")

    # Читаем структуру проекта
    try:
        result = subprocess.run(
            ["git", "ls-files", "src/"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        source_files = result.stdout.strip().split("\n")[:50]
    except:
        source_files = ["src/specify_cli/quality/", "src/specify_cli/memory/"]

    prompt = f"""# AutoResearch Iteration {iteration}

## Current Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Project Context

You are researching the Spec Kit project - a CLI tool for spec-driven development with persistent agent memory.

### Program Instructions
{program[:3000]}

### Research Context (priorities)
{context[:1000] if context else "No specific priorities provided. Use default high-priority areas: Security, Performance, Testing."}

### Memory from Previous Experiments

**Lessons Learned:**
{memory['lessons'][:2000] if memory['lessons'] else "No lessons yet."}

**Patterns Found:**
{memory['patterns'][:2000] if memory['patterns'] else "No patterns yet."}

**Architecture Decisions:**
{memory['architecture'][:2000] if memory['architecture'] else "No architecture decisions yet."}

### Project Structure (sample files)
{chr(10).join(source_files[:20])}

---

## Your Task

Propose and implement Experiment {iteration}.

IMPORTANT:
1. Start with HIGH PRIORITY areas (Security, Performance, Testing)
2. Make small, specific changes
3. Consider current best practices from 2025-2026
4. Focus on quality rules and templates

Respond with JSON only."""

    return prompt

# =============================================================================
# AGENT EXECUTION
# =============================================================================

def call_agent(iteration: int, memory: Dict[str, str]) -> Dict[str, Any]:
    """Вызывает Claude API для генерации эксперимента."""
    logger.info(f"🤖 Calling Claude API for iteration {iteration}...")

    # Web search больше не ограничен первой итерацией - агент сам решает когда использовать
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            temperature=0.7,
            system=build_system_prompt(),
            messages=[
                {
                    "role": "user",
                    "content": build_user_prompt(iteration, memory)
                }
            ]
        )

        content = message.content[0].text

        # Пытаемся распарсить JSON
        try:
            result = json.loads(content)
            logger.debug(f"Agent response parsed: {result.get('experiment_id', 'unknown')}")
            return result
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                result = json.loads(match.group())
                logger.debug(f"Agent response parsed from text: {result.get('experiment_id', 'unknown')}")
                return result
            else:
                logger.error(f"Could not parse agent response: {content[:200]}")
                return {
                    "error": "Could not parse agent response",
                    "raw": content[:500]
                }
    except Exception as e:
        logger.error(f"Agent call failed: {e}")
        return {
            "error": str(e),
            "experiment_id": f"exp-{iteration:03d}-error"
        }

def apply_changes(changes: List[Dict[str, str]]) -> bool:
    """Применяет изменения от агента."""
    logger.info(f"🔧 Applying {len(changes)} change(s)...")

    for change in changes:
        file_path = PROJECT_ROOT / change["file"]

        # Safety check
        if ".claude/memory" in str(file_path) and change["operation"] == "delete":
            logger.error(f"❌ REFUSED: Cannot delete memory files: {file_path}")
            return False

        if "git push" in change.get("content", ""):
            logger.error(f"❌ REFUSED: git push is not allowed")
            return False

        try:
            if change["operation"] == "create":
                logger.info(f"   Creating: {file_path}")
                write_file(file_path, change["content"])

            elif change["operation"] == "modify":
                logger.info(f"   Modifying: {file_path}")
                existing = read_file(file_path)
                backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
                write_file(backup_path, existing)
                write_file(file_path, change["content"])

            elif change["operation"] == "delete":
                logger.warning(f"⚠️  Requested delete: {file_path} (skipped - manual review required)")

        except Exception as e:
            logger.error(f"❌ Error applying change to {file_path}: {e}")
            return False

    logger.info("✅ All changes applied successfully")
    return True

# =============================================================================
# EVALUATION
# =============================================================================

def evaluate_experiment(experiment: Dict[str, Any]) -> float:
    """Оценивает эксперимент и возвращает score."""
    logger.debug("📊 Evaluating experiment...")

    if "error" in experiment:
        return 0.3

    changes = experiment.get("changes", [])
    if not changes:
        return 0.5

    score = 0.7

    for change in changes:
        file_path = change.get("file", "")
        if "security" in file_path.lower():
            score += 0.1
        if "quality/templates" in file_path:
            score += 0.05
        if change["operation"] == "create":
            score += 0.05

    if len(changes) > 5:
        score -= 0.1

    logger.debug(f"Evaluation score: {score:.2f}")
    return min(score, 1.0)

# =============================================================================
# MEMORY
# =============================================================================

def load_memory() -> Dict[str, str]:
    """Загружает всю память проекта."""
    logger.debug("Loading memory files...")
    return {
        "lessons": read_file(PROJECT_ROOT / ".claude" / "memory" / "lessons.md"),
        "patterns": read_file(PROJECT_ROOT / ".claude" / "memory" / "patterns.md"),
        "architecture": read_file(PROJECT_ROOT / ".claude" / "memory" / "architecture.md"),
    }

def save_experiment_to_memory(experiment: Dict[str, Any], kept: bool, reason: str):
    """Сохраняет результаты эксперимента в memory."""
    if not kept:
        return

    hypothesis = experiment.get("hypothesis", "")
    target = experiment.get("target", "")

    if "security" in target.lower() or "auth" in hypothesis.lower():
        entry = f"""
## {experiment.get('experiment_id', 'unknown')}: {hypothesis}

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Type:** Pattern

**What works:**
{experiment.get('reason', 'N/A')}

**Implementation:**
Target: {target}
Changes: {len(experiment.get('changes', []))} file(s)

**Result:** {reason}

**Tags:** #security #pattern #autoresearch
"""
        append_file(PROJECT_ROOT / ".claude" / "memory" / "patterns.md", entry)
        logger.info("💾 Saved to memory")

# =============================================================================
# MAIN LOOP
# =============================================================================

def print_banner():
    """Выводит баннер при старте."""
    logger.info("="*70)
    logger.info("🚀 Spec Kit AutoResearch Agent")
    logger.info("="*70)
    logger.info(f"Model: {MODEL}")
    logger.info(f"Max experiments: {MAX_EXPERIMENTS}")
    logger.info(f"Min improvement: {MIN_IMPROVEMENT}")
    logger.info(f"Interval: {INTERVAL_MINUTES} minutes between experiments")
    logger.info(f"Web search: {ENABLE_WEB_SEARCH}")
    logger.info(f"Project: {PROJECT_ROOT}")
    logger.info(f"Log file: {PROJECT_ROOT / '.speckit' / 'logs' / 'autoresearch_*.log'}")
    logger.info("="*70)

def main():
    global ENABLE_WEB_SEARCH, INTERVAL_MINUTES, MODEL, MAX_EXPERIMENTS, MIN_IMPROVEMENT
    
    parser = argparse.ArgumentParser(description="Spec Kit AutoResearch Agent")
    parser.add_argument("--max-experiments", type=int, default=MAX_EXPERIMENTS)
    parser.add_argument("--min-improvement", type=float, default=MIN_IMPROVEMENT)
    parser.add_argument("--interval-minutes", type=int, default=INTERVAL_MINUTES)
    parser.add_argument("--model", type=str, default=MODEL)
    parser.add_argument("--no-web-search", action="store_true", help="Disable web search")
    args = parser.parse_args()

    # Update global settings
    if args.no_web_search:
        ENABLE_WEB_SEARCH = False
    INTERVAL_MINUTES = args.interval_minutes
    if args.model:
        MODEL = args.model

    print_banner()

    # Создаём backup ветку
    try:
        branch_name = f"autoresearch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=PROJECT_ROOT,
            capture_output=True,
            check=True,
        )
        logger.info(f"📁 Created backup branch: {branch_name}")
    except Exception as e:
        logger.warning(f"⚠️  Could not create backup branch: {e}")

    # Главный цикл
    memory = load_memory()
    baseline_score = 0.75
    improvements = []
    history = []
    experiment_count = 0

    logger.info("🔄 Starting research loop...")
    logger.info(f"⏰ Will run experiment every {INTERVAL_MINUTES} minute(s)")
    logger.info(f"🎯 Target: up to {args.max_experiments} experiments")
    logger.info("")

    while experiment_count < args.max_experiments:
        experiment_count += 1
        next_run_time = datetime.now()

        logger.info("")
        logger.info("="*70)
        logger.info(f"🔬 Experiment {experiment_count}/{args.max_experiments}")
        logger.info(f"⏰ Started at: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)

        # 1. Вызываем агента
        experiment = call_agent(experiment_count, memory)

        if "error" in experiment:
            logger.error(f"❌ Agent error: {experiment['error']}")
            history.append({
                "iteration": experiment_count,
                "status": "error",
                "error": experiment.get("error"),
                "timestamp": datetime.now().isoformat()
            })
            # Сохраняем историю и продолжаем
            history_path = PROJECT_ROOT / ".speckit" / "experiments" / "history.jsonl"
            history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(history_path, "a") as f:
                f.write(json.dumps(history[-1], ensure_ascii=False) + "\n")

            # Ждём перед следующей итерацией
            if experiment_count < args.max_experiments:
                logger.info(f"⏳ Waiting {INTERVAL_MINUTES} minute(s) before next experiment...")
                time.sleep(INTERVAL_MINUTES * 60)
            continue

        logger.info(f"💡 Hypothesis: {experiment.get('hypothesis', 'N/A')}")
        logger.info(f"🎯 Target: {experiment.get('target', 'N/A')}")
        logger.info(f"📝 Reason: {experiment.get('reason', 'N/A')}")

        # 2. Применяем изменения
        changes = experiment.get("changes", [])
        if changes:
            success = apply_changes(changes)
            if not success:
                logger.warning("⚠️  Failed to apply changes, skipping evaluation")
        else:
            logger.info("ℹ️  No changes to apply")

        # 3. Оцениваем
        result_score = evaluate_experiment(experiment)
        improvement = result_score - baseline_score

        logger.info("")
        logger.info("📊 Results:")
        logger.info(f"   Baseline: {baseline_score:.2f}")
        logger.info(f"   Current:  {result_score:.2f}")
        logger.info(f"   Delta:    {improvement:+.2f}")

        # 4. Решение
        kept = improvement >= args.min_improvement
        reason = "Kept" if kept else "Discarded (below threshold)"

        logger.info(f"{'✅' if kept else '❌'} {reason}")

        # 5. Сохраняем
        if kept:
            baseline_score = result_score
            improvements.append(improvement)
            save_experiment_to_memory(experiment, True, reason)
            memory = load_memory()
        else:
            improvements.append(0.0)

        history.append({
            "iteration": experiment_count,
            "experiment_id": experiment.get("experiment_id"),
            "hypothesis": experiment.get("hypothesis"),
            "target": experiment.get("target"),
            "baseline_score": baseline_score,
            "result_score": result_score,
            "improvement": improvement,
            "kept": kept,
            "timestamp": datetime.now().isoformat()
        })

        # Сохраняем историю
        history_path = PROJECT_ROOT / ".speckit" / "experiments" / "history.jsonl"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(history_path, "a") as f:
            f.write(json.dumps(history[-1], ensure_ascii=False) + "\n")

        # Статистика
        successful = sum(1 for h in history if h.get("kept"))
        logger.info("")
        logger.info(f"📈 Progress: {successful}/{experiment_count} experiments successful")

        # Пауза перед следующей итерацией
        if experiment_count < args.max_experiments:
            logger.info("")
            logger.info(f"⏳ Waiting {INTERVAL_MINUTES} minute(s) before next experiment...")
            logger.info(f"🕐 Next experiment at: {(datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(INTERVAL_MINUTES * 60)

    # Итоги
    logger.info("")
    logger.info("="*70)
    logger.info("📊 AutoResearch Complete!")
    logger.info("="*70)
    logger.info(f"Total experiments: {len(history)}")
    logger.info(f"Successful: {sum(1 for h in history if h.get('kept'))}")
    if improvements:
        logger.info(f"Best improvement: {max(improvements):.2f}")
        logger.info(f"Final score: {baseline_score:.2f}")
    logger.info(f"📁 History: {history_path}")
    logger.info(f"📁 Logs: {PROJECT_ROOT / '.speckit' / 'logs'}")
    logger.info("="*70)

if __name__ == "__main__":
    main()
