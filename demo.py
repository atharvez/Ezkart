import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from bot.agents.shopping_agent import process_text_request
from bot.automation.amazon_bot import add_items_to_amazon_cart

async def main():
    print("\n--- AUTO-CART SHOPPING DEMO ---")
    print("Welcome to the smart AI Shopping Agent.")
    
    while True:
        print("\nChoose an option:")
        print("1. Enter text shopping list")
        print("2. Exit")
        
        choice = input("\nEnter your choice (1/2): ").strip()
        
        if choice == '2':
            print("Exiting...")
            break
            
        elif choice == '1':
            user_input = input("\nEnter your shopping list: ")
            
            print("\n[System]: Parsing request using local Ollama model...")
            try:
                cart_request = await process_text_request(user_input)
                
                print("\n=== Parsed Shopping List ===")
                for item in cart_request.items:
                    print(f"  - Name: {item.name}")
                    print(f"    Search Query: '{item.search_query}'")
                    print(f"    Quantity: {item.quantity}")
                print(f"============================")
                print(f"Total Budget: Rs.{cart_request.budget}")
                
            except Exception as e:
                print(f"Error during AI parsing: {e}")
                continue
                
        else:
            print("Invalid choice. Please try again.")
            continue

        if not cart_request.items:
            print("No items found to add to cart.")
            continue

        proceed = input("\nDo you want to proceed searching Amazon for these items? (y/n): ")
        if proceed.lower() == 'y':
            print("\n[System]: Launching browser...")
            try:
                # Pass the budget to the bot
                status = await add_items_to_amazon_cart(cart_request.items, budget=cart_request.budget)
                
                print("\n\n" + "="*40)
                print("           FINAL RECEIPT")
                print("="*40)
                
                if status["success"]:
                    print("\n✅ Successfully Added to Cart:")
                    for item in status["success"]:
                        print(f"  - {item['name']} (x{item['quantity']})")
                        print(f"    Price: Rs.{item['unit_price']} each | Total: Rs.{item['total_price']}")
                        
                if status["failed"]:
                    print("\n❌ Failed to Add:")
                    for item in status["failed"]:
                        print(f"  - {item['name']}: {item['reason']}")
                        
                print("\n" + "-"*40)
                if cart_request.budget > 0:
                    print(f"Budget:       Rs. {cart_request.budget:.2f}")
                print(f"Total Spent:  Rs. {status['total_spent']:.2f}")
                
                if cart_request.budget > 0:
                    remaining = cart_request.budget - status['total_spent']
                    print(f"Remaining:    Rs. {remaining:.2f}")
                print("="*40 + "\n")
                        
            except Exception as e:
                print(f"Error during Amazon automation: {e}")
        else:
            print("Skipped Amazon automation.")

if __name__ == "__main__":
    asyncio.run(main())
