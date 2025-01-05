import asyncio
import aiohttp
import json
import os
from datetime import datetime
import base64
from typing import Literal

class wolfram_api:

    class invalid_input(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class api_error(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    async def natural_language(self, question: str, theme: Literal['light', 'dark'] = 'dark'):
        self.query = {"type":"newQuery","locationId":"gu311","language":"en","displayDebuggingInfo":False,"yellowIsError":False,"requestSidebarAd":True,"category":"results","input":question,"i2d":False,"assumption":[],"apiParams":{},"file":None,"theme":theme}
        self.responses = []
        self.question = question
        async with aiohttp.ClientSession() as session:
            if not hasattr(self, "session") or self.session.closed:
                self.session = session
            await self.send_request()
        if not self.responses:
            raise self.api_error("Error with API! Perhaps sent same question too many times? Or too short timeout")
        self.timestamp = str(int(datetime.now().timestamp()))
        self.results = {'filenames': []}
        await self.parse_responses()
        return self.results
    
    async def send_request(self):
        uri = "wss://gateway.wolframalpha.com/gateway"
        async with self.session.ws_connect(uri) as websocket:
            await websocket.send_json(self.query)
            async for response in websocket:
                if response.json()['type'] == 'queryComplete':
                    break
                self.responses.append(response.json())

    async def parse_responses(self):
        index = 0
        for i in self.responses:
            if i.get('type') and i.get('type') == 'noResult' or i.get('type') == 'didyoumean':
                raise self.invalid_input(f"Invalid input!: {self.question}")
            clear = lambda x: "".join([i for i in x if i not in "\\/:*?<>|()"])
            if i.get("pods"):
                for j in i["pods"]:
                    if j.get("subpods"):
                        for k in j["subpods"]:
                            if k.get('img'):
                                if not os.path.exists("wolfram_pics"):
                                    os.mkdir("wolfram_pics")
                                filename = f"wolfram_pics/image-{self.timestamp}-{index}-{clear(j.get('id'))}.{k['img'].get('contenttype').split('/')[1]}"
                                with open(filename, 'wb') as f1:
                                    f1.write(base64.b64decode(k['img']['data']))
                                self.results['filenames'].append(filename)
                                if k['img'].get('title'):
                                    self.results[j.get('id') + '-' +  str(index)] = k['img']['title']
                                index += 1
                            else:
                                self.results[j.get('title') + '-' +  str(index)] = k.get('plaintext')
                                index += 1

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("question", type=str, help="mathematical equation using natural syntax")
    parser.add_argument("--theme", "-th", type=str, help="what theme to use for images - light, dark")
    args = parser.parse_args()
    if args.theme:
        if args.theme not in ['light', 'dark']:
            print("not valid theme! avaliable themes: light, dark")
            from sys import exit
            exit(1)

    results = asyncio.run(wolfram_api().natural_language(args.question, args.theme))
    print(json.dumps(results, indent=4))