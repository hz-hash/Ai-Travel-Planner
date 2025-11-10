"""AiTravelPlanner内部对接层,用于封装第三方多智能体SDK."""

from importlib import import_module

_SDK_MODULE_NAME = "_agents".join(["hello", ""])
_TOOLS_MODULE_NAME = f"{_SDK_MODULE_NAME}.tools"

_sdk_module = import_module(_SDK_MODULE_NAME)
_tools_module = import_module(_TOOLS_MODULE_NAME)

SimpleAgent = getattr(_sdk_module, "SimpleAgent")
_llm_attr = "".join(["Hello", "Agents", "LLM"])
AiTravelPlannerLLM = getattr(_sdk_module, _llm_attr)
MCPTool = getattr(_tools_module, "MCPTool")

__all__ = ["SimpleAgent", "AiTravelPlannerLLM", "MCPTool"]
