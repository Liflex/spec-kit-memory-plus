#!/usr/bin/env python3


"""


Spec Kit AutoResearch - Local Claude Mode





Запускает Claude CLI с накоплением контекста между итерациями.


Каждая итерация видит изменения предыдущей.





Usage:


    python autoresearch_local.py --max-experiments 10 --interval 5





Requirements:


    - Claude CLI: npm install -g @anthropic-ai/claude-code


    - Python 3.10+


"""





import os


import sys


import json


import time


import subprocess


import shlex


import re


from pathlib import Path


from datetime import datetime


from typing import Dict, Any, List


import argparse





# =============================================================================


# CONFIG


# =============================================================================





PROJECT_ROOT = Path(__file__).parent.resolve()


MAX_EXPERIMENTS = 10


INTERVAL_MINUTES = 5


EXPERIMENTS_DIR = PROJECT_ROOT / ".speckit" / "experiments"


MEMORY_DIR = PROJECT_ROOT / ".claude" / "memory"


CONTEXT_FILE = EXPERIMENTS_DIR / "accumulation_context.md"


LAST_EXPERIMENT_FILE = EXPERIMENTS_DIR / "last_experiment.md"  # Краткая сводка для агента


ENABLE_WEB_SEARCH = True  # Включить curl-based поиск





# Триггеры экспериментов


RUNNING_TRIGGER = EXPERIMENTS_DIR / ".experiment_running"


COMPLETE_MARKER = ">>>EXPERIMENT_COMPLETE<<<"  # Маркер который должен написать агент





# =============================================================================


# LOGGING


# =============================================================================





def get_next_experiment_number(exp_dir: Path) -> int:


    """Автоматически определяет следующий номер эксперимента.





    Проверяет существующие output_N.md файлы и возвращает следующий свободный номер.





    Args:


        exp_dir: Директория с экспериментами





    Returns:


        int: Следующий номер эксперимента


    """


    if not exp_dir.exists():


        return 1





    # Ищем все output_N.md файлы


    existing = []


    for file in exp_dir.glob("output_*.md"):


        match = file.stem.split("_")[1]


        try:


            num = int(match)


            existing.append(num)


        except:


            continue





    if not existing:


        return 1





    max_num = max(existing)


    return max_num + 1





def log(msg: str, level: str = "INFO"):


    """Простой логгер."""


    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    print(f"{timestamp} | {level:8s} | {msg}")





    # Также в файл


    log_dir = PROJECT_ROOT / ".speckit" / "logs"


    log_dir.mkdir(parents=True, exist_ok=True)


    log_file = log_dir / "autoresearch_local.log"





    with open(log_file, "a", encoding="utf-8") as f:


        f.write(f"{timestamp} | {level:8s} | {msg}\n")





# =============================================================================


# WEB SEARCH (curl-based, no API limits)


# =============================================================================





def web_search(query: str, max_results: int = 3) -> List[Dict[str, str]]:


    """Поиск через DuckDuckGo используя curl.





    Args:


        query: Поисковый запрос


        max_results: Максимум результатов





    Returns:


        List of {title, url, snippet}


    """


    if not ENABLE_WEB_SEARCH:


        return []





    try:


        import urllib.parse


        import re





        # DuckDuckGo HTML version


        encoded_query = urllib.parse.quote(query)


        url = f"https://html.duckduckgo.com/html/"





        # Используем curl


        result = subprocess.run(


            ["curl", "-s", "-X", "POST", "-d", f"q={query}", url],


            capture_output=True,


            text=True,


            timeout=15,


            check=False


        )





        if result.returncode != 0:


            log(f"curl search failed: {result.stderr}", "WARNING")


            return []





        html = result.stdout





        # Простая парсинга результатов из HTML


        results = []


        pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'





        for match in re.finditer(pattern, html):


            if len(results) >= max_results:


                break





            url_match = match.group(1)


            title_match = match.group(2)





            # DuckDuckGo использует редиректы, очищаем URL


            clean_url = url_match


            if "/l/?uddg=" in url_match:


                # Пропускаем редиректы


                continue





            results.append({


                "title": title_match,


                "url": clean_url,


                "snippet": f"Search result for: {query}"


            })





        log(f"Web search found {len(results)} results for: {query}", "DEBUG")


        return results





    except Exception as e:


        log(f"Web search error: {e}", "WARNING")


        return []





def get_web_context(topic: str) -> str:


    """Получает веб-контекст по теме.





    Args:


        topic: Тема для поиска





    Returns:


        Отформатированные результаты поиска


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


# EXPERIMENT TRIGGERS


# =============================================================================





def check_previous_complete() -> bool:


    """Проверяет что предыдущий эксперимент завершился.





    Returns:


        True если предыдущий завершён или не было активного


    """


    if not RUNNING_TRIGGER.exists():


        return True





    # Предыдущий эксперимент还在运行 - ждём


    log("Previous experiment still running, waiting for completion...", "WARNING")





    start_time = time.time()


    timeout = 3600  # 1 час максимум





    while RUNNING_TRIGGER.exists():


        if time.time() - start_time > timeout:


            log("Timeout waiting for previous experiment!", "ERROR")


            # Удаляем stale триггер


            try:


                RUNNING_TRIGGER.unlink()


            except:


                pass


            return True





        time.sleep(10)  # Проверяем каждые 10 секунд





    log("Previous experiment completed, proceeding...", "INFO")


    return True








def start_experiment_trigger(iteration: int):


    """Создаёт триггер начала эксперимента."""


    write_file(RUNNING_TRIGGER, f"Experiment {iteration} started at {datetime.now().isoformat()}")


    log(f"Experiment trigger created: {RUNNING_TRIGGER}", "DEBUG")








def complete_experiment_trigger():


    """Удаляет триггер эксперимента (завершён)."""


    try:


        if RUNNING_TRIGGER.exists():


            RUNNING_TRIGGER.unlink()


            log("Experiment trigger removed (completed)", "DEBUG")


    except:


        pass








def check_completion_marker(output: str) -> bool:


    """Проверяет наличие маркера завершения в выводе агента.





    Args:


        output: Вывод от Claude





    Returns:


        True если маркер найден


    """


    return COMPLETE_MARKER in output








# =============================================================================


# FILE OPERATIONS


# =============================================================================





def read_file(path: Path, max_chars: int = None) -> str:


    """Читает файл с опциональным ограничением размера."""


    if not path.exists():


        return ""


    content = path.read_text(encoding="utf-8")


    if max_chars and len(content) > max_chars:


        return content[-max_chars:]  # Берем последние N символов


    return content





def read_last_entries(path: Path, max_entries: int = 5) -> str:


    """Читает ТОЛЬКО записи помеченные [CRITICAL] или [IMPORTANT].


    Логика:


    1. Включаются только записи с метками [CRITICAL] или [IMPORTANT]


    2. Обычные записи без меток НЕ включаются


    3. max_entries игнорируется (для совместимости с вызовами)


    """


    if not path.exists():


        return ""





    content = path.read_text(encoding="utf-8")





    # Разбиваем по ## заголовкам


    lines = content.split("\n")


    entries = []


    current_entry = []


    current_header = ""





    for line in lines:


        if line.startswith("## "):


            # Сохраняем предыдущую запись


            if current_entry:


                entries.append({"header": current_header, "content": "\n".join(current_entry)})


            current_header = line


            current_entry = [line]


            current_entry.append(line)





    # Сохраняем последнюю запись


    if current_entry:


        entries.append({"header": current_header, "content": "\n".join(current_entry)})


    # Берем только помеченные записи


    marked_entries = []
    for entry in entries:


        header = entry["header"]


        if "[CRITICAL]" in header or "[IMPORTANT]" in header:


            marked_entries.append(entry)





    return "\n".join(e["content"] for e in marked_entries)








def write_file(path: Path, content: str):


    """Пишет файл."""


    path.parent.mkdir(parents=True, exist_ok=True)


    path.write_text(content, encoding="utf-8")


    log(f"Written: {path}", "DEBUG")





def append_file(path: Path, content: str):


    """Добавляет в файл."""


    path.parent.mkdir(parents=True, exist_ok=True)


    with open(path, "a", encoding="utf-8") as f:


        f.write("\n\n" + content)





# =============================================================================


# CONTEXT ACCUMULATION


# =============================================================================





def load_accumulation_context() -> str:


    """Загружает накопленный контекст от предыдущих итераций."""


    if CONTEXT_FILE.exists():


        return read_file(CONTEXT_FILE)


    return ""





def save_accumulation_context(experiment: Dict[str, Any]):


    """Сохраняет контекст эксперимента для следующей итерации."""





    entry = f"""


## Experiment {experiment['number']} - {experiment.get('title', 'Untitled')}





**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}


**Status:** {experiment.get('status', 'unknown')}





### What Was Done


{experiment.get('what_done', 'N/A')}





### Files Modified


{chr(10).join(f"- {f}" for f in experiment.get('files_modified', []))}





### Results


{experiment.get('results', 'N/A')}





### Notes for Next Iteration


{experiment.get('notes_next', 'N/A')}





---





"""





    current = read_file(CONTEXT_FILE)


    write_file(CONTEXT_FILE, current + entry)


    log(f"Context updated for next iteration", "INFO")








def save_last_experiment_summary(experiment: Dict[str, Any]):


    """Сохраняет краткую сводку ТОЛЬКО последнего эксперимента для агента.





    Этот файл перезаписывается каждой итерацией — в контекст попадает только последний!


    """





    summary = f"""# Last Experiment Summary





**Experiment #{experiment['number']}** — {experiment.get('title', 'Untitled')}


**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}





## What Was Done


{experiment.get('what_done', 'N/A')}





## Files Modified


{chr(10).join(f"- {f}" for f in experiment.get('files_modified', []))}





## Key Results


{experiment.get('results', 'N/A')}





## For Next Iteration


{experiment.get('notes_next', 'N/A')}


"""





    write_file(LAST_EXPERIMENT_FILE, summary)


    log(f"Last experiment summary updated", "DEBUG")





def get_full_context() -> str:


    """Собирает полный контекст для агента с ограничениями размера."""


    parts = []





    # 1. Инструкции (ограничим до 5000 символов)


    parts.append("# INSTRUCTIONS")


    parts.append(read_file(PROJECT_ROOT / "program.md", 5000))


    parts.append("")





    # 2. Приоритеты (ограничим до 1500 символов)


    context = read_file(PROJECT_ROOT / "research-context.md", 1500)


    if context:


        parts.append("# PRIORITIES")


        parts.append(context)


        parts.append("")





    # 3. Memory от предыдущих сессий (только последние 5 записей каждый)


    parts.append("# PROJECT MEMORY")


    parts.append(f"## Lessons Learned\n{read_last_entries(MEMORY_DIR / 'lessons.md', 5)}")


    parts.append(f"\n## Patterns Found\n{read_last_entries(MEMORY_DIR / 'patterns.md', 5)}")


    parts.append(f"\n## Architecture Decisions\n{read_last_entries(MEMORY_DIR / 'architecture.md', 5)}")


    parts.append("")





    # 4. ТОЛЬКО последний эксперимент (не весь лог!)


    last_exp = read_file(LAST_EXPERIMENT_FILE)


    if last_exp:


        parts.append("# LAST EXPERIMENT (for context)")


        parts.append(last_exp)


        parts.append("")





    # 5. Текущее состояние проекта


    parts.append("# CURRENT PROJECT STATE")





    # Показываем структуру


    try:


        result = subprocess.run(


            ["git", "status", "--short"],


            cwd=PROJECT_ROOT,


            capture_output=True,


            text=True,


            check=False


        )


        if result.stdout.strip():


            parts.append("## Modified Files (git status)")


            parts.append("```")


            parts.append(result.stdout.strip())


            parts.append("```")


    except:


        pass





    return "\n" + "\n".join(parts)





# =============================================================================


# AGENT PROMPT


# =============================================================================





def build_agent_prompt(iteration: int, total: int) -> str:


    """Строит полный prompt для агента."""


    full_context = get_full_context()

    # Log context size
    context_size_kb = len(full_context.encode('utf-8')) / 1024
    log(f"Context size: {context_size_kb:.1f} KB ({len(full_context):,} characters)", "INFO")

    return f"""# AutoResearch Experiment {iteration}/{total}





You are an autonomous research agent improving Spec Kit project.





## Your Task





Run Experiment {iteration} to improve Spec Kit. Consider:





1. **Previous experiments in this session** - build upon what was done


2. **Project memory** - learn from past lessons and patterns


3. **Current state** - see what's already been modified





## Full Context





{full_context}





## Instructions for This Experiment





1. **Analyze** the current state and previous experiments


2. **Propose** a specific improvement (build upon previous work!)


3. **Implement** the change


4. **Document** what you did in multiple places:


   - Update code/files as needed


   - Update README.md if relevant


   - Add to patterns.md if reusable (MARK as [CRITICAL] or [IMPORTANT]!)


   - Add to lessons.md if something learned (MARK as [CRITICAL] or [IMPORTANT]!)


   - Leave notes for NEXT iteration


5. **Report** results in structured format





## Memory Entry Priority System





**When adding entries to memory files (.claude/memory/), you MUST mark them:**





**[CRITICAL]** — Mark if:


- This is a key feature or fundamental architecture decision


- Without this, the project structure is unclear


- This defines how the project works





**[IMPORTANT]** — Mark if:


- This is a significant UX improvement


- This is a reusable pattern for other tasks


- This is a successful experiment result worth repeating





**No mark** — Don't mark if:


- This is a minor fix or improvement


- This is a generic quality rule (already in code)


- This is a temporary workaround





**Example:**


```markdown


## [CRITICAL] Lesson: Priority Scoring System Architecture


## [IMPORTANT] Pattern: Cascade Merge Strategies


## Lesson: Minor UI tweak (no mark - won't be loaded)


```





**Why this matters:** AutoResearch loads ONLY [CRITICAL] and [IMPORTANT] entries to keep prompt size manageable (~30-50 KB instead of 200+ KB).





## Web Search Available





You can use WebSearch and WebFetch tools at any time to:


- Research current best practices


- Look up documentation for libraries/frameworks


- Find solutions to technical problems


- Verify your approaches





Use web search whenever it would help improve the quality of your work.





## Output Format





At the end, provide:





```markdown


## Experiment Report





**Number:** {iteration}


**Title:** [brief title]


**Hypothesis:** [what you tested]


**Files Modified:** [list]


**Changes Made:** [description]


**Results:** [what happened]


**Notes for Next:** [what next iteration should know]


```





## ⚠️ CRITICAL: Completion Marker





**After completing the Experiment Report, you MUST write this exact marker as the very last line:**





```


{COMPLETE_MARKER}


```





**This is required for the experiment to be marked as complete. Without it, the system will wait indefinitely.**





## Safety





- NO git push


- NO deletion of .claude/memory/


- Changes only within {PROJECT_ROOT}


- Ask before destructive operations





Begin Experiment {iteration}.


"""





# =============================================================================


# CLAUDE CLI INTEGRATION


# =============================================================================





def get_claude_command() -> str:


    """Находит команду для запуска Claude CLI.





    Returns:


        Команда для запуска (например 'claude' или 'powershell.exe -File path\\to\\claude.ps1')


    """


    # Windows: проверяем путь к claude.ps1 через PowerShell


    if sys.platform == "win32":


        ps1_path = None





        # Пробуем найти через powershell.exe (классическая PowerShell)


        try:


            result = subprocess.run(


                ["powershell.exe", "-Command", "Get-Command claude | Select-Object -ExpandProperty Source"],


                capture_output=True,


                text=True,


                timeout=10,


                check=False


            )


            if result.returncode == 0 and result.stdout.strip():


                found_path = result.stdout.strip()


                if found_path.endswith(".ps1"):


                    ps1_path = found_path


                    log(f"Claude CLI found via powershell.exe: {ps1_path}", "INFO")


        except:


            pass





        # Если не нашли, пробуем через cmd.exe where


        if not ps1_path:


            try:


                result = subprocess.run(


                    ["cmd", "/c", "where claude.ps1"],


                    capture_output=True,


                    text=True,


                    timeout=10,


                    check=False


                )


                if result.returncode == 0 and result.stdout.strip():


                    ps1_path = result.stdout.strip().split('\n')[0].strip()


                    log(f"Claude CLI found via where: {ps1_path}", "INFO")


            except:


                pass





        # Если нашли путь, возвращаем команду с powershell.exe


        if ps1_path:


            return f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{ps1_path}"'





    # Unix или fallback - просто 'claude'


    return "claude"





def check_claude_cli() -> bool:


    """Проверяет наличие Claude CLI."""


    try:


        claude_cmd = get_claude_command()





        # Для Windows с PowerShell просто проверяем что файл существует


        if sys.platform == "win32" and "powershell.exe" in claude_cmd:


            match = re.search(r'-File\s+"([^"]+)"', claude_cmd)


            if not match:


                match = re.search(r'-File\s+(\S+)', claude_cmd)





            if match:


                ps1_path = match.group(1)


                # Проверяем что файл существует


                if Path(ps1_path).exists():


                    log(f"Claude CLI verified: {ps1_path}", "INFO")


                    return True


                else:


                    log(f"Claude.ps1 file not found at: {ps1_path}", "WARNING")


                    return False





        # Для Unix пробуем прямую команду


        result = subprocess.run(


            claude_cmd.split() + ["--version"],


            capture_output=True,


            text=True,


            timeout=15,


            check=False


        )





        if result.returncode == 0:


            log(f"Claude CLI version: {result.stdout.strip()}", "INFO")


            return True





        log("Claude CLI not found but will attempt to run anyway", "WARNING")


        log("Install with: npm install -g @anthropic-ai/claude-code", "INFO")


        return True





    except Exception as e:


        log(f"Error checking Claude CLI: {e}", "WARNING")


        log("Will attempt to run anyway. Install if fails: npm install -g @anthropic-ai/claude-code", "INFO")


        return True  # Пробуем всё равно





def run_claude_with_prompt(prompt: str, iteration: int) -> Dict[str, Any]:


    """Запускает Claude CLI с prompt и возвращает результат."""





    log(f"Running Claude CLI for experiment {iteration}...", "INFO")





    # Создаём временный файл с prompt


    prompt_file = EXPERIMENTS_DIR / f"prompt_{iteration}.md"


    write_file(prompt_file, prompt)

    # Show prompt size
    prompt_size_kb = len(prompt.encode('utf-8')) / 1024
    log(f"Prompt size: {prompt_size_kb:.1f} KB ({len(prompt):,} characters)", "INFO")

    # Создаём файл для вывода
    output_file = EXPERIMENTS_DIR / f"output_{iteration}.md"

    log(f"Prompt file: {prompt_file}", "DEBUG")





    try:


        # Получаем команду для запуска Claude


        claude_cmd = get_claude_command()


        log(f"Using Claude command: {claude_cmd}", "DEBUG")





        # Читаем prompt из файла


        prompt_content = read_file(prompt_file)





        # Формируем команду в зависимости от платформы


        if sys.platform == "win32" and "powershell.exe" in claude_cmd:


            # Windows: powershell.exe -NoProfile -ExecutionPolicy Bypass -File "path\to\claude.ps1"


            # Извлекаем путь к .ps1 из команды


            match = re.search(r'-File\s+"([^"]+)"', claude_cmd)


            if not match:


                match = re.search(r'-File\s+(\S+)', claude_cmd)





            if match:


                ps1_path = match.group(1)


                # Claude CLI: используем --print для неинтерактивного режима


                cmd_args = [


                    "powershell.exe",


                    "-NoProfile",


                    "-ExecutionPolicy", "Bypass",


                    "-File", ps1_path,


                    "--print",  # Неинтерактивный режим - выводит ответ и завершается


                ]


            else:


                raise ValueError(f"Cannot parse PowerShell command: {claude_cmd}")


        else:


            # Unix: claude --print для неинтерактивного режима


            cmd_args = claude_cmd.split() + ["--print"]





        log(f"Full command args: {cmd_args}", "DEBUG")





        # Устанавливаем переменные окружения для UTF-8


        env = os.environ.copy()


        env['PYTHONIOENCODING'] = 'utf-8'





        # CRITICAL: Отключаем CLAUDECODE чтобы избежать nested session check


        # Claude CLI нельзя запускать изнутри другой сессии Claude Code


        env.pop('CLAUDECODE', None)


        env.pop('CLAUDE_SESSION_ID', None)





        # Запускаем Claude CLI с передачей prompt через stdin


        # Добавляем timeout чтобы не зависнуть если Claude CLI зависнет


        result = subprocess.run(


            cmd_args,


            input=prompt_content,


            cwd=PROJECT_ROOT,


            capture_output=True,


            text=True,


            encoding='utf-8',


            errors='replace',


            env=env,


            check=False,


            timeout=1800  # 30 минут максимум для одного эксперимента


        )





        log(f"Claude exit code: {result.returncode}", "DEBUG")





        if result.returncode != 0:


            log(f"Claude error: {result.stderr}", "ERROR")


            return {


                "status": "error",


                "error": result.stderr,


                "output": ""


            }





        # Сохраняем вывод в файл


        output = result.stdout


        write_file(output_file, output)





        return {


            "status": "success",


            "output": output,


            "output_file": str(output_file)


        }





    except subprocess.TimeoutExpired as e:


        log(f"Claude CLI timeout after 30 minutes!", "ERROR")


        log(f"Experiment {iteration} timed out - may be stuck on permission prompt or hanging", "ERROR")


        return {


            "status": "error",


            "error": f"Timeout after 30 minutes. Claude CLI may be waiting for permission approval or stuck.",


            "output": ""


        }


    except Exception as e:


        log(f"Error running Claude: {e}", "ERROR")


        return {


            "status": "error",


            "error": str(e),


            "output": ""


        }





# =============================================================================


# REPORT PARSING


# =============================================================================





def parse_experiment_report(output: str) -> Dict[str, Any]:


    """Парсит отчёт из вывода Claude."""





    report = {


        "number": 0,


        "title": "",


        "hypothesis": "",


        "files_modified": [],


        "changes_made": "",


        "results": "",


        "notes_next": ""


    }





    # Ищем Experiment Report блок


    if "## Experiment Report" not in output:


        return report





    # Извлекаем блок отчёта


    lines = output.split("\n")


    in_report = False


    current_field = None


    current_value = []





    # Флаг, что значение для текущего поля уже было сохранено с той же строки


    field_saved_inline = False





    for line in lines:


        if "## Experiment Report" in line:


            in_report = True


            continue





        if not in_report:


            continue





        # Конец отчёта


        if line.startswith("## ") and "Experiment Report" not in line:


            break





        # Поля отчёта


        if line.startswith("**") and ":" in line:


            # Сохраняем предыдущее поле только если оно НЕ было сохранено inline


            if current_field is not None and not field_saved_inline and current_value:


                report[current_field] = "\n" + "\n".join(current_value).strip()


            # Извлекаем имя поля и значение (если на той же строке)


            # Используем split (первое двоеточие), т.к. значение может содержать двоеточия


            field_line = line.strip()


            parts = field_line.split(":", 1)


            field_name_raw = parts[0].replace("**", " ").strip()


            field_value = parts[1].strip() if len(parts) > 1 else ""





            # Маппинг имён полей


            field_mapping = {


                "number": "number",


                "title": "title",


                "hypothesis": "hypothesis",


                "files modified": "files_modified",


                "changes made": "changes_made",


                "results": "results",


                "notes for next": "notes_next"


            }





            field_key = field_name_raw.lower()


            current_field = field_mapping.get(field_key, field_key.replace(" ", "_"))





            # Если значение есть на той же строке, сохраняем сразу


            # Убираем ** из значения (агент может добавить для форматирования)


            if field_value:


                # Убираем ** в начале/конце значения


                field_value = field_value.strip().strip("*").strip()


                # Если после удаления ** осталось непустое значение


                if field_value:


                    report[current_field] = field_value


                    field_saved_inline = True


                    current_value = []


                else:


                    # Значение было только из **, считаем пустым


                    field_saved_inline = False


                    current_value = []


            else:


                field_saved_inline = False


                current_value = []  # Значения на следующих строках


        elif current_field is not None and not field_saved_inline:


            current_value.append(line)





    # Последнее поле


    if current_field:


        report[current_field] = "\n" + "\n".join(current_value).strip()


    # Парсим files_modified как список


        files = [f.strip("- ").strip() for f in report["files_modified"].split("\n") if f.strip()]


        report["files_modified"] = files





    # Debug: выводим распарсенные данные


    log(f"Parsed report - title: {report.get('title', 'N/A')}, files: {len(report.get('files_modified', []))}", "DEBUG")





    return report





# =============================================================================


# MAIN LOOP


# =============================================================================





def main():


    parser = argparse.ArgumentParser(


        description="Spec Kit AutoResearch - Local Claude Mode",


        formatter_class=argparse.RawDescriptionHelpFormatter,


        epilog="""


Examples:


  python autoresearch_local.py                 # 10 experiments, 5 min interval


  python autoresearch_local.py 20              # 20 experiments


  python autoresearch_local.py 50 10           # 50 experiments, 10 min interval


  python autoresearch_local.py --no-search     # Disable web search





Parameters:


  max_experiments    Maximum number of experiments to run (default: 10)


  interval           Minutes between experiments (default: 5)


  --no-search        Disable web search via curl


        """


    )


    # Позиционные аргументы (для обратной совместимости с bat-файлами)


    parser.add_argument("max_experiments", nargs="?", type=int, default=MAX_EXPERIMENTS,


                       help="Maximum number of experiments (default: 10)")


    parser.add_argument("interval", nargs="?", type=int, default=INTERVAL_MINUTES,


                       help="Interval between experiments in minutes (default: 5)")


    # Именованные аргументы (для прямого вызова из Python)


    parser.add_argument("--max-experiments", dest="max_experiments_opt", type=int,


                       help="Maximum number of experiments (overrides positional)")


    parser.add_argument("--interval", dest="interval_opt", type=int,


                       help="Interval between experiments in minutes (overrides positional)")


    parser.add_argument("--start-from", dest="start_from", type=int, default=1,


                       help="Start experiment from this number (default: 1, useful for continuation)")


    parser.add_argument("--no-search", action="store_true",


                       help="Disable web search")


    args = parser.parse_args()





    # Приоритет именованных аргументов над позиционными


    if args.max_experiments_opt is not None:


        args.max_experiments = args.max_experiments_opt


    if args.interval_opt is not None:


        args.interval = args.interval_opt





    # Определяем стартовый номер


    start_from = args.start_from


    if start_from == 1:


        # Автоопределяем следующий номер эксперимента


        next_num = get_next_experiment_number(EXPERIMENTS_DIR)


        if next_num > 1:


            log(f"Найдены предыдущие эксперименты. Продолжаем с Experiment {next_num}", "INFO")


            start_from = next_num





    # Вычисляем конечный номер эксперимента


    max_experiment_number = start_from + args.max_experiments - 1





    # Global setting for search


    global ENABLE_WEB_SEARCH


    if args.no_search:


        ENABLE_WEB_SEARCH = False





    log("="*70)


    log("Spec Kit AutoResearch - Local Claude Mode")


    log("="*70)


    log(f"Starting from: Experiment {start_from}")


    log(f"Max experiments: {args.max_experiments}")


    log(f"Ending at: Experiment {max_experiment_number}")


    log(f"Interval: {args.interval} minutes")


    log(f"Web search: {'Enabled (curl-based)' if ENABLE_WEB_SEARCH else 'Disabled'}")


    log(f"Project: {PROJECT_ROOT}")


    log(f"Context file: {CONTEXT_FILE}")


    log("="*70)


    log("")





    # Проверка Claude CLI


    if not check_claude_cli():


        log("Please install Claude Code CLI:", "ERROR")


        log("  npm install -g @anthropic-ai/claude-code", "INFO")


        return 1





    # Инициализация


    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)


    MEMORY_DIR.mkdir(parents=True, exist_ok=True)





    # Backup ветка


    try:


        branch = f"autoresearch-local-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


        subprocess.run(


            ["git", "checkout", "-b", branch],


            cwd=PROJECT_ROOT,


            capture_output=True,


            check=True


        )


        log(f"Created backup branch: {branch}", "INFO")


    except Exception as e:


        log(f"Could not create backup: {e}", "WARNING")





    # Главный цикл


    all_reports = []





    for iteration in range(start_from, max_experiment_number + 1):


        log("")


        log("="*70)


        log(f"EXPERIMENT {iteration}/{max_experiment_number}")


        log("="*70)


        log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


        log("")





        # Проверка что предыдущий эксперимент завершился


        if not check_previous_complete():


            log("Cannot start experiment, waiting for previous to complete", "ERROR")


            break





        # Создаём триггер запуска


        start_experiment_trigger(iteration)





        try:


            # Строим prompt с накопленным контекстом


            # Web search больше не ограничен - агент сам решает когда использовать WebSearch/WebFetch


            prompt = build_agent_prompt(iteration, args.max_experiments)





            # Запускаем Claude


            result = run_claude_with_prompt(prompt, iteration)





            if result["status"] == "error":


                log(f"Experiment failed: {result.get('error', 'Unknown')}", "ERROR")





                all_reports.append({


                    "number": iteration,


                    "status": "error",


                    "error": result.get("error")


                })





                if iteration < max_experiment_number:


                    wait_time = args.interval * 60


                    log(f"Waiting {args.interval} minutes before next experiment...", "INFO")


                    time.sleep(wait_time)


                continue





            # Проверяем маркер завершения


            output = result.get("output", "")


            if not check_completion_marker(output):


                log("WARNING: Completion marker not found in output!", "WARNING")


                log("Agent may not have completed properly. Checking output content...", "WARNING")





                # Проверяем есть ли хотя бы Experiment Report


                if "## Experiment Report" in output:


                    log("Experiment Report found, proceeding...", "INFO")


                else:


                    log("No Experiment Report found, treating as error", "ERROR")





                    all_reports.append({


                        "number": iteration,


                        "status": "error",


                        "error": "No completion marker or report found"


                    })





                    if iteration < max_experiment_number:


                        time.sleep(args.interval * 60)


                    continue





            log(f"Completion marker found: {COMPLETE_MARKER}", "DEBUG")


            log("Claude completed successfully", "INFO")


            log(f"Output saved to: {result.get('output_file')}", "INFO")





            # Парсим отчёт


            report = parse_experiment_report(result["output"])


            report["number"] = iteration


            report["status"] = "completed"





            log(f"Title: {report.get('title', 'N/A')}", "INFO")


            log(f"Files modified: {len(report.get('files_modified', []))}", "INFO")


            for f in report.get("files_modified", []):


                log(f"  - {f}", "DEBUG")





            # Сохраняем отчёт


            all_reports.append(report)





            # Данные для контекста


            experiment_data = {


                "number": iteration,


                "title": report.get("title", "Untitled"),


                "status": "completed",


                "what_done": report.get("changes_made", "N/A"),


                "files_modified": report.get("files_modified", []),


                "results": report.get("results", "N/A"),


                "notes_next": report.get("notes_next", "N/A")


            }





            # Полный лог (для человека)


            save_accumulation_context(experiment_data)





            # Краткая сводка ТОЛЬКО последнего (для агента!)


            save_last_experiment_summary(experiment_data)





            # Лог изменений


            changes_log = EXPERIMENTS_DIR / "changes_log.md"


            entry = f"""


## Experiment {iteration} - {report.get('title', 'Untitled')}





**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}


**Files:** {', '.join(report.get('files_modified', []))}





**What was done:**


{report.get('changes_made', 'N/A')}





**Results:**


{report.get('results', 'N/A')}


"""


            append_file(changes_log, entry)





            log("Experiment completed and logged", "INFO")





        finally:


            # Всегда удаляем триггер (даже при ошибке)


            complete_experiment_trigger()





        # Пауза перед следующей итерацией


        if iteration < max_experiment_number:


            if args.interval > 0:


                log(f"Waiting {args.interval} minutes before next experiment...", "INFO")


                log(f"Next experiment at: {(datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}", "INFO")


                time.sleep(args.interval * 60)


            else:


                log("Starting next experiment immediately...", "INFO")





    # Итоги


    log("")


    log("="*70)


    log("AUTORESEARCH COMPLETE")


    log("="*70)


    log(f"Total experiments: {len(all_reports)}")


    successful = sum(1 for r in all_reports if r.get("status") == "completed")


    log(f"Successful: {successful}")


    log(f"Failed: {len(all_reports) - successful}")





    # Сохраняем итоги


    summary_file = EXPERIMENTS_DIR / "summary.json"


    with open(summary_file, "w", encoding="utf-8") as f:


        json.dump(all_reports, f, indent=2, ensure_ascii=False)





    log(f"Summary saved to: {summary_file}")


    log(f"Context saved to: {CONTEXT_FILE}")


    log(f"Changes log: {EXPERIMENTS_DIR / 'changes_log.md'}")


    log("="*70)





    return 0





if __name__ == "__main__":


    sys.exit(main())


