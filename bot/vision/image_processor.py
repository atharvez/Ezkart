import os
import base64
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage

def get_vision_agent():
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    # llava is a vision model in Ollama
    return ChatOllama(model="llava", base_url=base_url, temperature=0.1)

async def extract_items_from_image(image_bytes: bytes) -> str:
    """
    Takes image bytes, converts to base64, and uses llava to extract a list of grocery items.
    """
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    
    agent = get_vision_agent()
    
    message = HumanMessage(
        content=[
            {"type": "text", "text": "List all the grocery items, food products, or written grocery list items you can see in this image. Only reply with the list of items separated by commas."},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
            }
        ]
    )
    
    response = await agent.ainvoke([message])
    return response.content
