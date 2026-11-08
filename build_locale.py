#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Antigravity Turkish Locale Builder
Path: D:\Android\Tools\Antigravity-TR\build_locale.py
Reads tr-dictionary.json and generates tr-locale.js
"""

import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_PATH = os.path.join(SCRIPT_DIR, "tr-dictionary.json")
LOCALE_PATH = os.path.join(SCRIPT_DIR, "tr-locale.js")

def build():
    with open(DICT_PATH, "r", encoding="utf-8") as f:
        d = json.load(f)

    exact_json = json.dumps(d["exact"], ensure_ascii=False, indent=4)

    patterns_code = "  const PATTERNS = [\n"
    for p in d["patterns"]:
        rep = p["replace"]
        reg = p["regex"]
        if "$2" in rep:
            fn_body = rep.replace("$1", "${a}").replace("$2", "${b}")
            patterns_code += f"    {{ regex: /{reg}/, fn: (_, a, b) => `{fn_body}` }},\n"
        elif "$1" in rep:
            fn_body = rep.replace("$1", "${n}")
            patterns_code += f"    {{ regex: /{reg}/, fn: (_, n) => `{fn_body}` }},\n"
        else:
            patterns_code += f"    {{ regex: /{reg}/, fn: () => `{rep}` }},\n"
    patterns_code = patterns_code.rstrip(",\n") + "\n  ];"

    template = f"""// Antigravity Turkish Localization Module (tr-locale.js)
// Signature: ANTIGRAVITY_TR_PATCH_V1
(() => {{
  if (window.__ANTIGRAVITY_TR_OBSERVER__) {{
    try {{ window.__ANTIGRAVITY_TR_OBSERVER__.disconnect(); }} catch (_) {{}}
  }}
  window.__ANTIGRAVITY_TR_LOADED__ = true;
  window.__ANTIGRAVITY_TR_RESOLVE__ = resolveTranslation;

  const DICT = {exact_json};

{patterns_code}

  const IGNORE_TAGS = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "PRE", "CODE", "TEXTAREA"]);
  let isMutating = false;

  function isProtected(node) {{
    let curr = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
    let depth = 0;
    while (curr && depth < 6) {{
      if (IGNORE_TAGS.has(curr.tagName)) return true;
      if (curr.isContentEditable) return true;
      const cls = curr.className;
      if (typeof cls === "string" && (
        cls.includes("monaco") ||
        cls.includes("prism") ||
        cls.includes("markdown-body") ||
        cls.includes("code-block")
      )) {{
        return true;
      }}
      curr = curr.parentElement;
      depth++;
    }}
    return false;
  }}

  function resolveTranslation(raw) {{
    if (!raw) return null;
    const trimmed = raw.trim();
    if (!trimmed) return null;

    if (DICT[trimmed]) {{
      return raw.replace(trimmed, DICT[trimmed]);
    }}

    for (const p of PATTERNS) {{
      if (p.regex.test(trimmed)) {{
        const rep = trimmed.replace(p.regex, p.fn);
        return raw.replace(trimmed, rep);
      }}
    }}
    return null;
  }}

  function translateTextNode(node) {{
    if (isProtected(node)) return;
    const raw = node.nodeValue;
    const trans = resolveTranslation(raw);
    if (trans && trans !== raw) {{
      isMutating = true;
      try {{
        node.nodeValue = trans;
      }} finally {{
        isMutating = false;
      }}
    }}
  }}

  function translateElementAttrs(el) {{
    if (isProtected(el)) return;
    for (const attr of ["placeholder", "title", "aria-label"]) {{
      const val = el.getAttribute(attr);
      if (val) {{
        const trans = resolveTranslation(val);
        if (trans && trans !== val) {{
          isMutating = true;
          try {{
            el.setAttribute(attr, trans);
          }} finally {{
            isMutating = false;
          }}
        }}
      }}
    }}
  }}

  function scanNode(root) {{
    if (!root) return;
    if (root.nodeType === Node.TEXT_NODE) {{
      translateTextNode(root);
      return;
    }}
    if (root.nodeType === Node.ELEMENT_NODE) {{
      if (isProtected(root)) return;
      translateElementAttrs(root);
      const walker = document.createTreeWalker(
        root,
        NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
        null
      );
      let curr = walker.nextNode();
      while (curr) {{
        if (curr.nodeType === Node.TEXT_NODE) {{
          translateTextNode(curr);
        }} else if (curr.nodeType === Node.ELEMENT_NODE) {{
          translateElementAttrs(curr);
        }}
        curr = walker.nextNode();
      }}
    }}
  }}

  function initObserver() {{
    if (!document.body) {{
      window.requestAnimationFrame(initObserver);
      return;
    }}

    scanNode(document.body);

    const observer = new MutationObserver((mutations) => {{
      if (isMutating) return;
      for (const m of mutations) {{
        if (m.type === "childList") {{
          for (const added of m.addedNodes) {{
            scanNode(added);
          }}
        }} else if (m.type === "characterData") {{
          translateTextNode(m.target);
        }} else if (m.type === "attributes") {{
          translateElementAttrs(m.target);
        }}
      }}
    }});

    observer.observe(document.body, {{
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["placeholder", "title", "aria-label"]
    }});

    window.__ANTIGRAVITY_TR_OBSERVER__ = observer;
  }}

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", initObserver);
  }} else {{
    initObserver();
  }}
}})();
"""
    with open(LOCALE_PATH, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"[+] Successfully built {LOCALE_PATH} ({len(d['exact'])} terms, {len(d['patterns'])} patterns).")

if __name__ == "__main__":
    build()
