# from langchain_groq import ChatGroq
# from app.core.config import get_settings

# settings = get_settings()

# def get_llm(model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.0):
#     """
#     Get an instance of ChatGroq.
    
#     Args:
#         model_name: The name of the model to use. Default is 'llama3-70b-8192'.
#                     Other options: 'mixtral-8x7b-32768', 'gemma-7b-it'.
#         temperature: The temperature for generation.
        
#     Returns:
#         ChatGroq instance.
#     """
#     if not settings.GROQ_API_KEY:
#         raise ValueError("GROQ_API_KEY is not set in environment variables.")
        
#     return ChatGroq(
#         model_name=model_name,
#         temperature=temperature,
#         api_key=settings.GROQ_API_KEY
#     )


from langchain_groq import ChatGroq
from app.core.config import get_settings

settings = get_settings()

def get_llm(model_name: str = "openai/gpt-oss-20b", temperature: float = 0.0):
    """
    Get an instance of ChatGroq.
    
    Args:
        model_name: The name of the model to use. Default is 'openai/gpt-oss-20b'.
                    
                    GPT-OSS models (OpenAI's open models on Groq):
                      - 'openai/gpt-oss-20b': Fast, cost-efficient (1000+ t/s, 128K context)
                        $0.10/M input tokens, $0.50/M output tokens
                      - 'openai/gpt-oss-120b': More capable flagship model (500+ t/s, 128K context)
                        $0.15/M input tokens, $0.75/M output tokens
                      - 'openai/gpt-oss-safeguard-20b': Safety classification model
                    
                    Other Groq models:
                      - 'llama-3.3-70b-versatile'
                      - 'mixtral-8x7b-32768'
                      - 'gemma-7b-it'
                      
        temperature: The temperature for generation (0.0 to 1.0).
        
    Returns:
        ChatGroq instance.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in environment variables.")
        
    return ChatGroq(
        model_name=model_name,
        temperature=temperature,
        api_key=settings.GROQ_API_KEY
    )