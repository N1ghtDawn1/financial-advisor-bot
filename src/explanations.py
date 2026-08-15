"""I generate faithful explanations from immutable transition evidence."""

from __future__ import annotations

from .environment import ACTION_NAMES, BUY, HOLD, SELL, Transition


def explain(transition: Transition, policy_name: str) -> tuple[str, list[str]]:
    """I name only evidence that is present in the recorded transition."""
    action = transition.executed_action
    rules: list[str] = []
    evidence: list[str] = []
    if transition.delta_sma <= -0.015:
        rules.append("SMA_BELOW_THRESHOLD")
        evidence.append(f"price is {abs(transition.delta_sma) * 100:.1f}% below its 10-day SMA")
    if transition.rsi_14 < 40:
        rules.append("RSI_OVERSOLD")
        evidence.append(f"RSI is {transition.rsi_14:.1f}, below 40")
    if transition.delta_sma >= 0.018:
        rules.append("SMA_ABOVE_THRESHOLD")
        evidence.append(f"price is {transition.delta_sma * 100:.1f}% above its 10-day SMA")
    if transition.rsi_14 > 62:
        rules.append("RSI_OVERBOUGHT")
        evidence.append(f"RSI is {transition.rsi_14:.1f}, above 62")
    if transition.rejected_reason:
        rules.append("ACTION_REJECTED")
        return (
            f"I converted the requested action to Hold because {transition.rejected_reason.lower()}. "
            f"The simulated portfolio remains ${transition.portfolio_value:,.2f}.",
            rules,
        )
    prefix = f"The {policy_name} selected {ACTION_NAMES[action]} at ${transition.close:.2f}."
    if action == BUY and evidence:
        return prefix + " Supporting context: " + "; ".join(evidence) + ".", rules
    if action == SELL and evidence:
        return prefix + " Risk context: " + "; ".join(evidence) + ".", rules
    if action == HOLD:
        rules.append("NO_TRADE")
        return prefix + " No simulated trade was executed at this step.", rules
    return prefix + " I label the indicators as context rather than claiming they caused the learned decision.", rules
