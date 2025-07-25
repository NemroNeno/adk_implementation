# A central place to define subscription plan limits
PLANS = {
    "free": {
        "name": "Free Tier",
        "limits": {
            "max_agents": 2,
            "max_tokens_per_month": 50000,
        }
    },
    "pro": {
        "name": "Pro Tier",
        "limits": {
            "max_agents": 20,
            "max_tokens_per_month": 1000000,
        }
    }
}