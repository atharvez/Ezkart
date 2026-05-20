import os
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

class ShoppingItem(BaseModel):
    name: str = Field(description="The raw name of the product")
    search_query: str = Field(description="An optimized search string for Amazon to find this exact product. Omit the quantity unless it's a specific unit like '500ml' or '1kg'. Example: 'Lays classic potato chips' or 'Pepsi 500ml'")
    quantity: int = Field(description="The integer number of units to buy. Default to 1 if unspecified.", default=1)

class ShoppingCartRequest(BaseModel):
    items: list[ShoppingItem] = Field(description="The list of items to buy")
    budget: float = Field(description="The budget constraint in the local currency. 0 if no budget specified.", default=0.0)

def get_shopping_agent():
    # Initialize the LLM and force JSON mode
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    llm = ChatOllama(model="llama3", base_url=base_url, temperature=0.0, format="json")

    # Setup Parser
    parser = PydanticOutputParser(pydantic_object=ShoppingCartRequest)

    # Setup Prompt
    prompt = PromptTemplate(
        template=(
            "You are a smart shopping assistant. Extract the grocery list, optimizing the search queries for Amazon, and extract the budget.\n"
            "CRITICAL: You must return ONLY raw valid JSON. Do not use markdown blocks (```json). Do not add any conversational text before or after. Do not include any comments (//) inside the JSON.\n"
            "{format_instructions}\n\n"
            "User Request: {request}\n"
        ),
        input_variables=["request"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # Create Chain
    chain = prompt | llm | parser
    return chain

async def process_text_request(text: str) -> ShoppingCartRequest:
    agent = get_shopping_agent()
    # Invoke async
    result = await agent.ainvoke({"request": text})
    return result
