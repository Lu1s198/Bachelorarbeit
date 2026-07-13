# Provider werden bewusst NICHT eager importiert, damit ein fehlendes SDK
# (z.B. openai) nur stört, wenn genau dieser Provider verwendet wird.
# Verwende die Factory: `from llm.factory import get_provider`.
