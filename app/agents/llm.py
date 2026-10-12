import logging

from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

def create_model(model_name=None):
    selected_model = model_name or "openai/gpt-oss-120b"
    logger.info("Creating LLM: provider=groq model=%s", selected_model)
    return ChatGroq(
        model=selected_model,
        temperature=0,
    )

def get_model(model_name=None):
    if not hasattr(get_model, "_model"):
        get_model._model = create_model(model_name)
    else:
        logger.debug("Reusing cached LLM")
    return get_model._model
