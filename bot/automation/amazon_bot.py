import asyncio
import re
# pyrefly: ignore [missing-import]
from playwright.async_api import async_playwright
# pyrefly: ignore [missing-import]
from playwright_stealth.stealth import Stealth
from bot.agents.shopping_agent import ShoppingItem

def parse_price(price_text: str) -> float:
    """Helper to convert Amazon price strings (like '1,200') to float."""
    if not price_text:
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', price_text)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

async def add_items_to_amazon_cart(items: list[ShoppingItem], budget: float = 0.0):
    """
    Automates adding a list of items to the Amazon shopping cart.
    Now extracts prices, selects cheapest non-sponsored items, updates quantity, and respects the budget.
    """
    status = {"success": [], "failed": [], "total_spent": 0.0}
    remaining_budget = budget if budget > 0 else float('inf')
    
    async with async_playwright() as p:
        # Launch browser (headless=False so you can see it in action during the demo)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        try:
            await page.goto("https://www.amazon.in/")
            await page.wait_for_load_state("domcontentloaded")
            
            for item in items:
                search_term = item.search_query
                try:
                    print(f"\n[Amazon Bot]: Searching for '{search_term}'...")
                    # Fill search box
                    await page.fill("input#twotabsearchtextbox", search_term)
                    await page.click("input#nav-search-submit-button")
                    await page.wait_for_load_state("domcontentloaded")
                    
                    # Wait for results to load
                    await page.wait_for_selector("div[data-component-type='s-search-result']")
                    
                    # Scrape top results to find the cheapest valid item
                    results = await page.locator("div[data-component-type='s-search-result']").all()
                    
                    best_product = None
                    cheapest_price = float('inf')
                    
                    # Only check the first 5 results to save time
                    for result in results[:5]:
                        # Skip sponsored
                        sponsored = await result.locator(".puis-sponsored-label-text").count()
                        if sponsored > 0:
                            continue
                            
                        # Get price
                        price_element = result.locator("span.a-price-whole").first
                        if await price_element.is_visible():
                            price_text = await price_element.inner_text()
                            price_val = parse_price(price_text)
                            
                            # Get link
                            link_element = result.locator("h2 a.a-link-normal").first
                            if price_val > 0 and price_val < cheapest_price and await link_element.is_visible():
                                cheapest_price = price_val
                                best_product = link_element
                    
                    if best_product is None:
                        print(f"  -> Could not find a valid price for {search_term}.")
                        status["failed"].append({"name": item.name, "reason": "No valid price found"})
                        continue
                        
                    total_item_cost = cheapest_price * item.quantity
                    print(f"  -> Cheapest found: Rs.{cheapest_price} per unit. Total cost for {item.quantity}: Rs.{total_item_cost}")
                    
                    if budget > 0 and total_item_cost > remaining_budget:
                        print(f"  -> Budget exceeded! Remaining: Rs.{remaining_budget}, Cost: Rs.{total_item_cost}")
                        status["failed"].append({"name": item.name, "reason": f"Exceeds budget (Costs Rs.{total_item_cost})"})
                        continue
                        
                    # Navigate to the product page
                    async with page.expect_popup() as popup_info:
                        await best_product.click()
                    product_page = await popup_info.value
                    await product_page.wait_for_load_state("domcontentloaded")
                    
                    # Select Quantity if needed
                    if item.quantity > 1:
                        # Amazon's quantity dropdown
                        qty_dropdown = product_page.locator("select#quantity")
                        if await qty_dropdown.is_visible():
                            try:
                                await qty_dropdown.select_option(value=str(item.quantity))
                                await asyncio.sleep(1) # wait for DOM update
                            except Exception:
                                print(f"  -> Note: Requested quantity {item.quantity} not available in dropdown. Defaulting to 1.")
                                item.quantity = 1
                                total_item_cost = cheapest_price * item.quantity
                        else:
                            print("  -> Note: Quantity dropdown not found. Defaulting to 1.")
                            item.quantity = 1
                            total_item_cost = cheapest_price * item.quantity
                            
                    # Click Add to Cart
                    add_btn = product_page.locator("input#add-to-cart-button")
                    if await add_btn.is_visible():
                        await add_btn.click()
                        await asyncio.sleep(2)
                        
                        status["success"].append({
                            "name": item.name,
                            "search_query": search_term,
                            "quantity": item.quantity,
                            "unit_price": cheapest_price,
                            "total_price": total_item_cost
                        })
                        remaining_budget -= total_item_cost
                        status["total_spent"] += total_item_cost
                        print(f"  -> Successfully added to cart!")
                    else:
                        print(f"  -> Add to cart button not found.")
                        status["failed"].append({"name": item.name, "reason": "Add to cart button missing"})
                        
                    await product_page.close()
                        
                except Exception as e:
                    print(f"Error processing {search_term}: {e}")
                    status["failed"].append({"name": item.name, "reason": str(e)})
                    
        except Exception as e:
            print(f"Global Amazon error: {e}")
        finally:
            print("\n[System]: Automation finished. Browser will stay open until you press Enter.")
            await asyncio.get_event_loop().run_in_executor(None, input, "Press Enter here in the terminal to close the browser and continue...")
            await browser.close()
            
    return status
