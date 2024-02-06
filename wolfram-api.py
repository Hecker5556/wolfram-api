import asyncio
import websockets
import json
import os
from datetime import datetime
import base64
from typing import Literal

class wolfram_api:

    class api_error(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    async def natural_language(self, question: str, theme: Literal['light', 'dark'] = 'dark', timeout: int = 2):
        self.query = {"type":"newQuery","locationId":"gu311","language":"en","displayDebuggingInfo":False,"yellowIsError":False,"requestSidebarAd":True,"category":"results","input":question,"i2d":False,"assumption":[],"apiParams":{},"file":None,"theme":theme}
        self.timeout = timeout
        self.responses = []
        await self.send_request()
        if not self.responses:
            raise self.api_error("Error with API! Perhaps sent same question too many times? Or too short timeout")
        self.timestamp = str(int(datetime.now().timestamp()))
        self.results = {'filenames': []}
        await self.parse_responses()
        return self.results
    
    async def send_request(self):
        uri = "wss://www.wolframalpha.com/n/v1/api/fetcher/results"
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(self.query))
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), self.timeout)
                    self.responses.append(json.loads(response))
            except asyncio.TimeoutError:
                return

    async def parse_responses(self):
        index = 0
        for i in self.responses:
            if i.get("pods"):
                for j in i["pods"]:
                    if j.get("subpods"):
                        for k in j["subpods"]:
                            if k.get('img'):
                                if not os.path.exists("wolfram_pics"):
                                    os.mkdir("wolfram_pics")
                                with open(f"wolfram_pics/image-{self.timestamp}-{index}-{j.get('id')}.{k['img'].get('contenttype').split('/')[1]}", 'wb') as f1:
                                    f1.write(base64.b64decode(k['img']['data']))
                                self.results['filenames'].append(f"wolfram_pics/image-{self.timestamp}-{index}-{j.get('id')}.{k['img'].get('contenttype').split('/')[1]}")
                                if k['img'].get('title'):
                                    self.results[j.get('id') + '-' +  str(index)] = k['img']['title']
                                index += 1

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("question", type=str, help="mathematical equation using natural syntax")
    parser.add_argument("--theme", "-th", type=str, help="what theme to use for images - light, dark")
    parser.add_argument("--timeout", "-t", type=int, help="how long to wait for an answer from wolfram (the harder the question the longer you should set the timeout)")
    args = parser.parse_args()
    if args.theme:
        if args.theme not in ['light', 'dark']:
            print("not valid theme! avaliable themes: light, dark")
            from sys import exit
            exit(1)
    results = asyncio.run(wolfram_api().natural_language(args.question, args.theme, args.timeout))