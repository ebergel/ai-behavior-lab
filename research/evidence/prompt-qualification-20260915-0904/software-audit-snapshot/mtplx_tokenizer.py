"""Optional helper run with MTPLX's Python, never imported by the stdlib core.

Only local tokenizer files are loaded. This independent template rendering is
compared with the engine's captured dispatch tokens, rather than assuming the
server used the messages verbatim. The helper never loads model weights.
"""
import json
from pathlib import Path
import sys


def main():
    from transformers import AutoTokenizer
    data = json.load(sys.stdin)
    path = Path(data["model_path"])
    tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True, trust_remote_code=False)
    template = (path / "chat_template.jinja").read_text()
    payload = data["request"]
    kwargs = {"chat_template": template, "add_generation_prompt": True,
              "enable_thinking": payload["enable_thinking"], "preserve_thinking": False,
              "reasoning_effort": payload["reasoning_effort"]}
    text = tokenizer.apply_chat_template(payload["messages"], tokenize=False, **kwargs)
    ids = tokenizer.encode(text, add_special_tokens=False)
    print(json.dumps({"token_ids": list(ids), "rendered_text": text}))


if __name__ == "__main__":
    main()
