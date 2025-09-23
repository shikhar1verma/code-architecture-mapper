"""
Dedicated Diagram Correction Subgraph

This module implements a specialized agent for correcting Mermaid diagram syntax errors.
It's separate from the generation workflow and focuses solely on correction through:

1. Validation → 2. Manual Fixes → 3. LLM Correction → 4. Final Validation

This separation provides better modularity and allows for specialized correction logic.
"""

import re
from typing import List
from langgraph.graph import StateGraph, END, START

from backend.services.content_generation import ContentGenerationService
from backend.utils.logger import get_logger
from .state import CorrectionState

logger = get_logger(__name__)
content_service = ContentGenerationService()

# Validation regex patterns and functions for correction
# All the validation logic that was previously in diagram_subgraph.py

# Tolerant header match near the top
_HEADER_OK_RE = re.compile(r'^\s*(?:graph|flowchart)\b', re.IGNORECASE)

# Subgraph declaration validation
_SUBGRAPH_DECL_RE = re.compile(
    r'^\s*subgraph\s+(?P<id>[A-Za-z][\w-]*)\s*(?P<label>\[[^\]]*\])?\s*(?P<trailer>.*)$'
)

# Edge ID validation for spaces
_EDGE_ID_RE = re.compile(
    r'^\s*(?P<src>[A-Za-z][\w-]*)\s*(?:[-.=ox]{1,3}\s*(?:"[^"]*"|\|[^|]*\|)?\s*[-.=]{0,3}>)\s*(?P<dst>[A-Za-z][\w-]*)\s*$'
)

# Node declaration validation
_NODE_DECL_RE = re.compile(r'^\s*(?P<id>[A-Za-z][\w-]*)\s*[\[\(]')

# Class line validation
_CLASS_LINE_RE = re.compile(r'^\s*class\s+(?P<ids>[^;]+?)\s+[A-Za-z_][\w-]*\s*;?\s*$')

# Tolerant edge matcher for flowcharts
# Examples matched:
#   A --> B
#   A -- "Uses configuration" --> B
#   A --|guard|--> B
#   A -.-> B
#   A ===> B
#   src o-- "opt" --> dst
_EDGE_RE = re.compile(
    r"""
    ^\s*
    (?P<src>[A-Za-z][\w-]*)                          # source id
    \s*
    (?:
        (?P<left>(?:[ox])?-{1,3}|\.{1,3}|={1,3})     # left stroke, optional open/close marker
        \s*
        (?:"[^"]*"|\|[^|]*\|)?                       # optional label, quotes or pipes
        \s*
        (?P<right>-{0,3}|\.{0,3}|={0,3})>            # right side before '>'
    )
    \s*
    (?P<dst>[A-Za-z][\w-]*)                          # dest id
    \s*$
    """,
    re.VERBOSE,
)

# Lines that are not edges and should be ignored by edge checks
_IGNORE_PREFIXES = (
    "classDef",
    "class ",
    "style ",
    "linkStyle",
    "subgraph",
    "end",
    "direction",
    "%%",       # Mermaid comment
)


def _subgraph_errors(diagram: str) -> List[str]:
    """Check for subgraph declaration syntax errors."""
    errs: List[str] = []
    for ln, line in enumerate(diagram.splitlines(), 1):
        s = line.strip()
        if not s.startswith("subgraph"):
            continue

        # 1) forbid ::: on subgraph declaration
        if ":::" in s:
            # only error if it appears on same line as 'subgraph'
            if "subgraph" in s and ":::" in s:
                errs.append(f"Line {ln}: ':::' class shorthand is not allowed on subgraph declaration. Move it to a separate 'class <id> <className>;' line.")
                continue  # skip further checks for this line

        # 2) validate basic structure and id
        m = _SUBGRAPH_DECL_RE.match(line)
        if not m:
            # Mermaid expects: subgraph <id>[optional title]
            errs.append(f"Line {ln}: subgraph declaration must be 'subgraph <id>[optional title]'.")
            continue

        sid = m.group("id")
        trailer = m.group("trailer") or ""
        # disallow style/class tokens on the line
        if "::: " in trailer or trailer.strip().startswith(":::") or " class " in trailer:
            errs.append(f"Line {ln}: styling on subgraph declaration is not supported. Put it after 'end' with 'class {sid} <className>;'.")
        
        # check for any other trailing content that should be on next line
        elif trailer and trailer.strip():
            errs.append(f"Line {ln}: extra content after subgraph declaration. Move '{trailer.strip()}' to next line.")
    
    return errs


def _identifier_errors(diagram: str) -> List[str]:
    """Check for spaces in node identifiers."""
    errs: List[str] = []
    
    def has_space(tok: str) -> bool:
        return " " in tok or "\t" in tok

    for ln, line in enumerate(diagram.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith(("%%", "classDef", "style", "linkStyle", "direction", "end")):
            continue

        # edges
        em = _EDGE_ID_RE.match(s)
        if em:
            if has_space(em.group("src")):
                errs.append(f"Line {ln}: source id contains a space. Use FE_NAVBAR not 'FE_ NAVBAR'.")
            if has_space(em.group("dst")):
                errs.append(f"Line {ln}: destination id contains a space. Use FE_NAVBAR not 'FE_ NAVBAR'.")

        # node declarations
        nm = _NODE_DECL_RE.match(s)
        if nm and has_space(nm.group("id")):
            errs.append(f"Line {ln}: node id contains a space. Use FE_NAVBAR not 'FE_ NAVBAR'.")

        # class statement
        cm = _CLASS_LINE_RE.match(s)
        if cm:
            id_part = cm.group("ids")
            for tok in [t.strip() for t in id_part.split(",")]:
                # tokens can be ranges or groups in other graph types but for flowchart ids are simple
                if has_space(tok):
                    errs.append(f"Line {ln}: id '{tok}' in class statement contains a space.")

    return errs


def _has_header(diagram: str) -> bool:
    # Scan first ~15 non-empty, non-comment lines for header
    seen = 0
    for line in diagram.splitlines():
        s = line.strip()
        if not s or s.startswith("%%"):
            continue
        seen += 1
        if _HEADER_OK_RE.match(s):
            return True
        if seen >= 15:
            break
    return False


def _edge_warnings(diagram: str) -> List[str]:
    """Non-blocking lints about suspicious edge lines."""
    warns: List[str] = []
    for ln, line in enumerate(diagram.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith(_IGNORE_PREFIXES):
            continue
        # quick filter for lines that look like edges
        if "->" in s or "--" in s or ".->" in s or "==>" in s:
            if not _EDGE_RE.search(s):
                # do not fail validation, only warn
                warns.append(f"Line {ln}: edge looks unusual for flowchart syntax")
    return warns


def _label_warnings(diagram: str) -> List[str]:
    """Very conservative label lints. Never block."""
    warns: List[str] = []
    # Find text inside [ ], ( ), { } to approximate labels
    for ln, line in enumerate(diagram.splitlines(), 1):
        # skip style lines to avoid hex colors, etc.
        if line.lstrip().startswith(_IGNORE_PREFIXES):
            continue
        for label in re.findall(r'\[([^\]]+)\]|\(([^\)]+)\)|\{([^\}]+)\)', line):
            text = next((t for t in label if t), "")
            # Only warn on raw '<' which often indicates accidental HTML
            if "<" in text:
                warns.append(f"Line {ln}: label contains '<' which may be HTML-like")
            # Only warn on a raw '&' that is not a known HTML entity
            if "&" in text and not re.search(r'&(?:amp|lt|gt|quot|#39);', text):
                warns.append(f"Line {ln}: label contains '&' without an entity, consider &amp;")
    return warns


def _node_id_warnings(diagram: str) -> List[str]:
    """Duplicate id definitions are usually fine in Mermaid, so only warn on very long ids."""
    warns: List[str] = []
    for nid in re.findall(r'\b([A-Za-z_][\w-]*)\s*[\[\(]', diagram):
        if len(nid) > 40:
            warns.append(f"Node id is very long: '{nid[:40]}...'")
    return warns


def _complexity_warnings(diagram: str) -> List[str]:
    warns: List[str] = []
    node_count = len(re.findall(r'\b[A-Za-z_][\w-]*\s*[\[\(]', diagram))
    edge_count = sum(1 for line in diagram.splitlines() if "->" in line or "--" in line)
    if node_count > 120:
        warns.append(f"Large diagram, nodes {node_count}")
    if edge_count > 250:
        warns.append(f"Large diagram, edges {edge_count}")
    return warns


def _parentheses_errors(diagram: str) -> List[str]:
    """Check for parentheses in node labels that can cause parse errors."""
    errs: List[str] = []
    for ln, line in enumerate(diagram.splitlines(), 1):
        s = line.strip()
        # Skip comment lines and other special lines
        if not s or s.startswith(_IGNORE_PREFIXES):
            continue
        
        # Look for patterns like NODE[Label (with parens)] that cause "got 'PS'" errors
        if re.search(r'\b[A-Za-z_][\w-]*\[[^\]]*\([^\]]*\)[^\]]*\]', s):
            errs.append(f"Line {ln}: parentheses in node label can cause parse errors. Use quotes: NODE[\"Label (with parens)\"]")
    
    return errs


def _parser_errors_python_only(diagram: str) -> List[str]:
    """
    Minimal error set we can assert confidently in Python without Mermaid:
      - missing header
      - unbalanced subgraph blocks
      - subgraph declaration syntax errors
      - identifier syntax errors
      - parentheses in node labels
    Everything else should be a warning.
    """
    errs: List[str] = []
    if not _has_header(diagram):
        errs.append("Missing diagram type declaration. Add 'flowchart LR' or 'graph TD' at the top.")

    # balance subgraph blocks
    opens = sum(1 for l in diagram.splitlines() if l.strip().startswith("subgraph"))
    closes = sum(1 for l in diagram.splitlines() if l.strip() == "end")
    if opens != closes:
        errs.append(f"Unbalanced subgraph blocks. subgraph={opens}, end={closes}.")

    # new deterministic syntax errors
    errs.extend(_subgraph_errors(diagram))
    errs.extend(_identifier_errors(diagram))
    errs.extend(_parentheses_errors(diagram))

    return errs


def _apply_correction(diagram: str, error: str) -> str:
    """Apply rule-based corrections for common Mermaid syntax errors."""
    # Only fix header and subgraph balance
    if "Missing diagram type" in error:
        if not diagram.strip().startswith(("graph", "flowchart")):
            diagram = "flowchart LR\n" + diagram

    elif "Unbalanced subgraph blocks" in error:
        opens = sum(1 for l in diagram.splitlines() if l.strip().startswith("subgraph"))
        closes = sum(1 for l in diagram.splitlines() if l.strip() == "end")
        if opens > closes:
            diagram = diagram.rstrip() + ("\nend" * (opens - closes))
        elif closes > opens:
            # safest is to prepend missing subgraphs, but that is risky
            # better to leave as an error and let the generator retry
            pass

    # subgraph ::: fix
    elif "subgraph declaration" in error or "':::' class shorthand is not allowed" in error:
        fixed_lines = []
        for line in diagram.splitlines():
            if line.strip().startswith("subgraph") and ":::" in line:
                # strip ':::className' from this line and add a separate class line
                m = _SUBGRAPH_DECL_RE.match(line)
                if m:
                    sid = m.group("id")
                    # remove any :::className chunk
                    newline = re.sub(r':::\s*[A-Za-z_][\w-]*', '', line)
                    fixed_lines.append(newline)
                    # add a separate class line immediately after
                    fixed_lines.append(f"class {sid} folder;")
                    continue
            fixed_lines.append(line)
        diagram = "\n".join(fixed_lines)

    # fix trailing content after subgraph declarations
    elif "extra content after subgraph declaration" in error:
        fixed_lines = []
        for line in diagram.splitlines():
            if line.strip().startswith("subgraph"):
                m = _SUBGRAPH_DECL_RE.match(line)
                if m and m.group("trailer") and m.group("trailer").strip():
                    # Split the line: keep declaration, move trailing content to next line
                    trailer_content = m.group("trailer").strip()
                    decl_part = line.replace(m.group("trailer"), "").rstrip()
                    fixed_lines.append(decl_part)
                    # Add trailing content on next line with proper indentation
                    fixed_lines.append("    " + trailer_content)
                    continue
            fixed_lines.append(line)
        diagram = "\n".join(fixed_lines)

    # id with space fix: replace occurrences like FE_ NAVBAR with FE_NAVBAR
    elif "contains a space" in error:
        # Fix patterns like "FE_ NAVBAR" -> "FE_NAVBAR"
        diagram = re.sub(r'\b([A-Za-z_]+)\s+([A-Za-z][\w-]*)\b', lambda m: m.group(1).rstrip('_') + "_" + m.group(2), diagram)

    # Parentheses in node labels fix - for "got 'PS'" errors and similar parsing issues
    elif "got 'PS'" in error or "Expecting 'SQE'" in error or "parentheses in node label" in error:
        # Fix patterns like NODE[Label (with parens)] -> NODE["Label (with parens)"]
        # This handles parentheses inside square bracket labels that cause parse errors
        # Only apply to unquoted labels (avoid double-quoting)
        diagram = re.sub(
            r'\b([A-Za-z_][\w-]*)\[([^"\]]*\([^"\]]*\)[^"\]]*)\]',
            r'\1["\2"]',
            diagram
        )

    # Optional: truncate very long labels, but do not touch quotes or '>'
    diagram = re.sub(r'\[([^\]]{120,})\]', lambda m: f"[{m.group(1)[:117]}...]", diagram)

    return diagram


def validate_diagram_node(state: CorrectionState) -> CorrectionState:
    """
    Validation node: Detect syntax errors in the current diagram.
    This is the entry point and exit verification for the correction process.
    """
    logger.info(f"🔍 Validating diagram (attempt {state['current_attempt']})")
    
    raw_diagram = state["raw_diagram"]
    if not raw_diagram:
        new_state = dict(state)
        new_state["validation_errors"] = ["No diagram provided for correction"]
        new_state["validation_warnings"] = []
        new_state["is_valid"] = False
        return new_state
    
    # Python-based validation errors
    parse_errors = _parser_errors_python_only(raw_diagram)
    
    # Non-blocking warnings
    lint_warnings = []
    lint_warnings.extend(_edge_warnings(raw_diagram))
    lint_warnings.extend(_label_warnings(raw_diagram))
    lint_warnings.extend(_node_id_warnings(raw_diagram))
    lint_warnings.extend(_complexity_warnings(raw_diagram))
    
    # Create new state dict to avoid concurrent updates
    new_state = dict(state)
    new_state["validation_errors"] = parse_errors
    new_state["validation_warnings"] = lint_warnings
    new_state["is_valid"] = len(parse_errors) == 0
    
    if new_state["is_valid"]:
        logger.info("✅ Diagram validation passed")
        new_state["corrected_diagram"] = raw_diagram
        new_state["correction_success"] = True
    else:
        logger.warning(f"❌ Validation failed with {len(parse_errors)} error(s)")
        for error in parse_errors[:3]:
            logger.warning(f"  - {error}")
    
    return new_state


def manual_fix_node(state: CorrectionState) -> CorrectionState:
    """
    Manual fix node: Apply regex-based rule corrections for common syntax errors.
    These are deterministic fixes that don't require LLM intelligence.
    """
    logger.info("🔧 Applying manual rule-based corrections")
    
    raw_diagram = state["raw_diagram"]
    validation_errors = state["validation_errors"]
    fixes_applied = []
    
    corrected_diagram = raw_diagram
    
    # Apply manual corrections for each error
    for error in validation_errors:
        original_diagram = corrected_diagram
        corrected_diagram = _apply_correction(corrected_diagram, error)
        
        if corrected_diagram != original_diagram:
            fix_description = f"Manual fix applied for: {error}"
            fixes_applied.append(fix_description)
            logger.info(f"✅ Applied manual fix for: {error[:50]}...")
    
    # Update state - return a new state dict to avoid concurrent updates
    new_state = dict(state)
    new_state["raw_diagram"] = corrected_diagram
    new_state["manual_fixes_applied"] = fixes_applied
    
    if fixes_applied:
        logger.info(f"✅ Applied {len(fixes_applied)} manual fixes")
    else:
        logger.info("ℹ️ No manual fixes applicable")
    
    return new_state


def llm_correction_node(state: CorrectionState) -> CorrectionState:
    """
    LLM correction node: Use LLM for intelligent correction of complex syntax errors.
    This handles errors that manual rules can't fix.
    """
    logger.info("🤖 Applying LLM-based corrections")
    
    # Check if we still have errors after manual fixes
    if state["is_valid"]:
        logger.info("ℹ️ Diagram already valid, skipping LLM correction")
        return state
    
    # Create new state dict to avoid concurrent updates
    new_state = dict(state)
    
    try:
        # Use LLM correction with current validation errors
        corrected_diagram = content_service.correct_llm_diagram(
            broken_diagram=state["raw_diagram"],
            validation_errors=state["validation_errors"]
        )
        
        new_state["raw_diagram"] = corrected_diagram
        new_state["llm_correction_applied"] = True
        
        logger.info("✅ LLM correction applied")
        
    except Exception as e:
        logger.warning(f"⚠️ LLM correction failed: {e}")
        new_state["llm_correction_applied"] = False
    
    return new_state


def should_retry_correction(state: CorrectionState) -> str:
    """
    Decision function: Determine if correction should be retried or finalized.
    """
    if state["is_valid"]:
        logger.info("✅ Diagram is valid, finalizing")
        return "finalize"
    
    if state["current_attempt"] >= state["max_attempts"]:
        logger.warning(f"⚠️ Max attempts ({state['max_attempts']}) reached")
        return "finalize"
    
    logger.info(f"🔄 Retrying correction (attempt {state['current_attempt'] + 1})")
    return "retry"


def increment_attempt_node(state: CorrectionState) -> CorrectionState:
    """
    Increment the attempt counter for retry logic.
    """
    new_state = dict(state)
    new_state["current_attempt"] += 1
    logger.info(f"🔄 Starting correction attempt {new_state['current_attempt']}")
    return new_state


def finalize_correction_node(state: CorrectionState) -> CorrectionState:
    """
    Finalize the correction process and prepare summary.
    """
    logger.info("🏁 Finalizing diagram correction")
    
    # Create new state dict to avoid concurrent updates
    new_state = dict(state)
    
    # Determine final result
    if new_state["is_valid"]:
        new_state["corrected_diagram"] = new_state["raw_diagram"]
        new_state["correction_success"] = True
        logger.info("✅ Correction successful")
    else:
        # Use best attempt even if not perfect
        new_state["corrected_diagram"] = new_state["raw_diagram"]
        new_state["correction_success"] = False
        logger.warning("⚠️ Correction incomplete, using best attempt")
    
    # Generate correction summary
    summary = []
    if new_state.get("manual_fixes_applied"):
        summary.extend(new_state["manual_fixes_applied"])
    if new_state.get("llm_correction_applied"):
        summary.append("LLM-based intelligent correction applied")
    
    new_state["correction_summary"] = summary
    
    logger.info(f"📊 Correction summary: {len(summary)} corrections applied")
    
    return new_state


def create_correction_subgraph() -> StateGraph:
    """
    Create the dedicated diagram correction subgraph.
    
    Flow: Validate → Manual Fixes → LLM Correction → Re-validate → Retry Decision → Finalize
    """
    subgraph = StateGraph(CorrectionState)
    
    # Add nodes
    subgraph.add_node("validate", validate_diagram_node)
    subgraph.add_node("manual_fix", manual_fix_node)
    subgraph.add_node("llm_correct", llm_correction_node)
    subgraph.add_node("revalidate", validate_diagram_node)  # Separate validation after correction
    subgraph.add_node("increment_attempt", increment_attempt_node)
    subgraph.add_node("finalize", finalize_correction_node)
    
    # Define the correction flow
    subgraph.add_edge(START, "validate")
    
    # If valid after initial validation, go straight to finalize
    # Otherwise start correction process
    subgraph.add_conditional_edges(
        "validate",
        lambda state: "finalize" if state["is_valid"] else "manual_fix"
    )
    
    # Manual fixes → LLM correction
    subgraph.add_edge("manual_fix", "llm_correct")
    
    # LLM correction → revalidate 
    subgraph.add_edge("llm_correct", "revalidate")
    
    # After revalidation, decide retry or finalize
    subgraph.add_conditional_edges(
        "revalidate",
        should_retry_correction,
        {
            "retry": "increment_attempt",
            "finalize": "finalize"
        }
    )
    
    # Retry loop: increment → manual fixes  
    subgraph.add_edge("increment_attempt", "manual_fix")
    
    # End
    subgraph.add_edge("finalize", END)
    
    return subgraph.compile()


def correct_diagram(
    raw_diagram: str,
    analysis_id: str = "unknown",
    diagram_mode: str = "balanced",
    max_attempts: int = 3
) -> CorrectionState:
    """
    Convenience function to correct a diagram using the correction subgraph.
    
    Args:
        raw_diagram: The diagram to correct
        analysis_id: Analysis ID for context
        diagram_mode: Diagram mode for context
        max_attempts: Maximum correction attempts
        
    Returns:
        Final correction state with results
    """
    initial_state: CorrectionState = {
        "raw_diagram": raw_diagram,
        "analysis_id": analysis_id,
        "diagram_mode": diagram_mode,
        "current_attempt": 1,
        "max_attempts": max_attempts,
        "validation_errors": [],
        "validation_warnings": [],
        "is_valid": False,
        "manual_fixes_applied": [],
        "llm_correction_applied": False,
        "corrected_diagram": None,
        "correction_success": False,
        "correction_summary": []
    }
    
    correction_subgraph = create_correction_subgraph()
    final_state = correction_subgraph.invoke(initial_state)
    
    return final_state
