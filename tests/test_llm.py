"""Tests pour agent/llm.py — _trim_history."""

from agent.llm import KEEP_RECENT, MAX_HISTORY, Agent


def _make_agent(history):
    """Crée un Agent sans appeler __init__, avec l'historique donné."""
    agent = object.__new__(Agent)
    agent._history = list(history)
    return agent


class TestTrimHistory:
    def test_no_trim_under_limit(self):
        history = [{"role": "system", "content": "sys"}]
        history += [{"role": "user", "content": f"msg{i}"} for i in range(10)]
        agent = _make_agent(history)
        original_len = len(agent._history)
        agent._trim_history()
        assert len(agent._history) == original_len

    def test_trim_when_over_limit(self):
        history = [{"role": "system", "content": "sys"}]
        for i in range(MAX_HISTORY):
            history.append({"role": "user", "content": f"msg{i}"})
            history.append({"role": "assistant", "content": f"reply{i}"})
        # 1 + 100 = 101 > MAX_HISTORY (50)
        agent = _make_agent(history)
        agent._trim_history()
        assert len(agent._history) <= MAX_HISTORY + 1
        assert len(agent._history) >= KEEP_RECENT

    def test_keeps_system_message(self):
        history = [{"role": "system", "content": "system prompt"}]
        for i in range(MAX_HISTORY):
            history.append({"role": "user", "content": f"msg{i}"})
            history.append({"role": "assistant", "content": f"reply{i}"})
        agent = _make_agent(history)
        agent._trim_history()
        assert agent._history[0] == {"role": "system", "content": "system prompt"}

    def test_no_cut_in_tool_sequence(self):
        """Le trim ne coupe pas au milieu d'une séquence tool_calls -> tool."""
        history = [{"role": "system", "content": "sys"}]
        # 30 messages normaux (15 paires user/assistant)
        for i in range(15):
            history.append({"role": "user", "content": f"msg{i}"})
            history.append({"role": "assistant", "content": f"reply{i}"})
        # Séquence tool_calls → tool
        history.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "tc1", "function": {"name": "test"}}],
            }
        )
        history.append(
            {
                "role": "tool",
                "tool_call_id": "tc1",
                "content": "result",
            }
        )
        # 19 messages normaux après (pour atteindre KEEP_RECENT)
        for i in range(9):
            history.append({"role": "user", "content": f"late{i}"})
            history.append({"role": "assistant", "content": f"late{i}"})
        history.append({"role": "user", "content": "dernier"})
        # Total: 1 + 30 + 2 + 19 = 52 > MAX_HISTORY (50)
        assert len(history) > MAX_HISTORY

        agent = _make_agent(history)
        agent._trim_history()

        # Vérifier que chaque message "tool" a son parent assistant+tool_calls
        for i, msg in enumerate(agent._history):
            if msg.get("role") == "tool":
                found = False
                for j in range(i - 1, -1, -1):
                    if agent._history[j].get("tool_calls"):
                        found = True
                        break
                    if agent._history[j].get("role") not in ("tool",):
                        break
                assert found, f"Tool orphelin à l'index {i}"
