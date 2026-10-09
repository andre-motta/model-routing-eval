"""List prices in USD per 1M tokens. Keep this table honest: it is the basis of every cost figure.

Sources (checked 2026-10-09):
  OpenAI pricing page (user-supplied table for GPT-5.6, digitalapplied.com launch post for GPT-6).
  Anthropic: Claude Code reports cost itself (total_cost_usd); the rows below are only used
  when a record has tokens but no reported cost.
"""

PRICES = {
    # model id:        input, cached input, cache write, output
    "gpt-6-astra":     dict(input=10.00, cached=1.00, cache_write=12.50, output=50.00),
    "gpt-6.1-sol":     dict(input=2.00,  cached=0.10, cache_write=2.50,  output=10.00),  # 6.1 halved cache reads
    "gpt-6-sol":       dict(input=2.00,  cached=0.20, cache_write=2.50,  output=10.00),
    "gpt-6-luna":      dict(input=0.10,  cached=0.01, cache_write=0.125, output=0.50),
    "gpt-5.6-sol":     dict(input=4.00,  cached=0.40, cache_write=5.00,  output=20.00),
    "gpt-5.6-terra":   dict(input=2.00,  cached=0.20, cache_write=2.50,  output=12.00),
    "gpt-5.6-luna":    dict(input=0.20,  cached=0.02, cache_write=0.25,  output=1.20),
    # GLM 5.3 via the Red Hat EnMaaS gateway: free (does not draw on the API budget). 252K context, no prompt cache.
    "rits/zai-org/glm-5-3": dict(input=0.0, cached=0.0, cache_write=0.0, output=0.0),
    # Anthropic list prices per claude-api skill table cached 2026-10-06. Claude Code reports cost
    # itself (total_cost_usd); these rows are only used when a record has tokens but no cost.
    "claude-fable-5-1":  dict(input=10.00, cached=1.00, cache_write=12.50, output=50.00),
    "claude-opus-5-5":   dict(input=4.00,  cached=0.40, cache_write=5.00,  output=20.00),
    "claude-opus-5":     dict(input=5.00,  cached=0.50, cache_write=6.25,  output=25.00),
    "claude-sonnet-5-5": dict(input=2.00,  cached=0.20, cache_write=2.50,  output=10.00),
    "claude-sonnet-5":   dict(input=2.00,  cached=0.20, cache_write=2.50,  output=10.00),
    "claude-haiku-5-5":  dict(input=0.10,  cached=0.01, cache_write=0.125, output=0.50),
    "claude-haiku-4-5-20251001": dict(input=1.00, cached=0.10, cache_write=1.25, output=5.00),
}

ALIASES = {"astra": "gpt-6-astra", "sol": "gpt-6.1-sol", "luna": "gpt-6-luna", "terra": "gpt-5.6-terra",
           "glm": "rits/zai-org/glm-5-3", "fable": "claude-fable-5-1", "opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5"}


def resolve(model: str) -> str:
    return ALIASES.get(model, model)


def cost_usd(model: str, tokens: dict) -> float | None:
    p = PRICES.get(resolve(model))
    if not p:
        return None
    # Codex reports input_tokens inclusive of cached; Claude reports them separately. Callers normalise
    # to: input = uncached input, cached = cache reads, cache_write = cache creation, output = all output.
    return (tokens.get("input", 0) * p["input"]
            + tokens.get("cached", 0) * p["cached"]
            + tokens.get("cache_write", 0) * p["cache_write"]
            + tokens.get("output", 0) * p["output"]) / 1_000_000
