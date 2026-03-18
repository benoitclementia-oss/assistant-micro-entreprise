"""Tests pour agent/tools.py — validation des schémas OpenAI."""

from agent.tools import TOOLS


class TestToolSchemas:
    def test_nombre_outils(self):
        assert len(TOOLS) == 11

    def test_cles_requises(self):
        for tool in TOOLS:
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool
            func = tool["function"]
            assert "name" in func
            assert "parameters" in func

    def test_noms_uniques(self):
        names = [t["function"]["name"] for t in TOOLS]
        assert len(names) == len(set(names))

    def test_parameters_type_object(self):
        for tool in TOOLS:
            params = tool["function"]["parameters"]
            assert params["type"] == "object"

    def test_required_subset_of_properties(self):
        for tool in TOOLS:
            params = tool["function"]["parameters"]
            required = set(params.get("required", []))
            properties = set(params.get("properties", {}).keys())
            assert required <= properties, (
                f"Outil '{tool['function']['name']}' : "
                f"required {required - properties} absent de properties"
            )
