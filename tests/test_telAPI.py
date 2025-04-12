import asyncio
from aiogram import Bot

async def test_token(token: str):
    try:
        bot = Bot(token=token)
        me = await bot.get_me()
        print(f"Token is valid. Bot name: {me.username}")
        await bot.session.close()  # Important to close the session
    except Exception as e:
        print(f"Token is invalid: {e}")

async def main():
    # Replace with your actual token or load from environment variable
    token = "7718674401:AAHh-h_cKxQ3JHugeBQQuXDsoNltYVPkz9w"  # Or: token = os.environ["TELEGRAM_BOT_TOKEN"]
    await test_token(token)

if __name__ == "__main__":
    asyncio.run(main())