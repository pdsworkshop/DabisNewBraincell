from dotenv import load_dotenv
import asyncio
import random

async def main():
    num = random.random()
    num *= 17
    print(num)
    
if __name__ == "__main__":
    asyncio.run(main())