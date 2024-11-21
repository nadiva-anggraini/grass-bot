import asyncio
import websockets
import json
import uuid
import requests
import time
from datetime import datetime
import pytz
from termcolor import colored

class Configuration:
    def __init__(self):
        self.websocket_host = "wss://proxy.wynd.network:4444"  # Ganti jika perlu
        self.retry_interval = 20  # Waktu untuk mencoba kembali (dalam detik)


class BotInstance:
    def __init__(self, configuration):
        self.configuration = configuration
        self.total_data_usage = {}

    async def direct_connect(self, user_id):
        try:
            async with websockets.connect(self.configuration.websocket_host, extra_headers=self.default_headers()) as websocket:
                print(colored(f"Connect directly Without Proxy/Local network", "white"))
                await self.send_ping(websocket, "Direct IP")

                while True:
                    try:
                        message = await websocket.recv()
                        data_usage = len(message)
                        self.total_data_usage[user_id] = self.total_data_usage.get(user_id, 0) + data_usage
                        message = json.loads(message)

                        if message.get("action") == "AUTH":
                            auth_response = {
                                "id": message.get("id"),
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": str(uuid.uuid4()),
                                    "user_id": user_id,
                                    "user_agent": "Mozilla/5.0",
                                    "timestamp": int(time.time()),
                                    "device_type": "desktop",
                                    "version": "4.28.2"
                                }
                            }
                            await websocket.send(json.dumps(auth_response))
                            print(colored(f"Trying to send authentication for userID: {user_id}", "white"))

                        elif message.get("action") == "PONG":
                            total_data_usage_kb = round(self.total_data_usage[user_id] / 1024, 2)
                            timezone = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%H:%M:%S WIB %d-%m-%Y")
                            print(colored(f"{timezone} Received PONG for UserID: {user_id}, Used {total_data_usage_kb} KB total packet data", "cyan"))

                    except websockets.ConnectionClosed as e:
                        print(colored(f"WebSocket closed: {e.code} {e.reason}", "red"))
                        break

        except Exception as e:
            print(colored(f"Failed to connect directly: {e}", "red"))

        await asyncio.sleep(self.configuration.retry_interval)
        await self.direct_connect(user_id)

    async def send_ping(self, websocket, proxy_ip):
        while True:
            timezone = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%H:%M:%S WIB %d-%m-%Y")
            ping_msg = {
                "id": str(uuid.uuid4()),
                "version": "1.0.0",
                "action": "PING",
                "data": {}
            }
            await websocket.send(json.dumps(ping_msg))
            print(colored(f"{timezone} Sent PING from {proxy_ip}", "green"))
            await asyncio.sleep(26)  # Kirim ping setiap 26 detik

    def default_headers(self):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
            "Pragma": "no-cache",
            "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "OS": "Windows",
            "Platform": "Desktop",
            "Browser": "Mozilla"
        }


async def load_lines(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(colored(f"Failed to load file {file_path}: {e}", "red"))
        return []


async def main():
    show_header()
    await asyncio.sleep(1)

    configuration = Configuration()
    bot_instance = BotInstance(configuration)

    user_id_list = await load_lines("userid.txt")
    if not user_id_list:
        print(colored("Account is not available in userid.txt", "red"))
        return

    print(colored(f"Detected total {len(user_id_list)} accounts, trying to connect...\n", "white"))

    connection_tasks = [bot_instance.direct_connect(user_id) for user_id in user_id_list]
    await asyncio.gather(*connection_tasks)


def center(text):
    width = 80
    return text.center(width)


def show_intro():
    print("\n")
    print(colored(center("🌱 Grass Network 🌱"), "green", attrs=["bold"]))
    print(colored(center("GitHub: Caulia Wilson"), "cyan"))
    print(colored(center("Link: https://github.com/wcaulia"), "cyan"))


def show_header():
    show_intro()
    print("\n")
    print(colored(center("Processing, please wait a moment..."), "cyan", attrs=["bold"]))
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
