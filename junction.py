import asyncio
from typing import Dict, Any, List
import aiohttp
import subprocess
import json
import logging
import os

logger = logging.getLogger(__name__)

class Junction:
    def __init__(self):
        self.sockets: Dict[str, Any] = {}

    async def create_socket(self, ai_id: str) -> None:
        self.sockets[ai_id] = {
            "status": "connected",
            "last_used": asyncio.get_event_loop().time()
        }
        logger.info(f"Created socket for AI {ai_id}")

    async def remove_socket(self, ai_id: str) -> None:
        if ai_id in self.sockets:
            del self.sockets[ai_id]
            logger.info(f"Removed socket for AI {ai_id}")

    async def process(self, ai: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        ai_id = ai['id']
        ai_type = ai['type']

        if ai_id not in self.sockets:
            await self.create_socket(ai_id)

        self.sockets[ai_id]["last_used"] = asyncio.get_event_loop().time()

        try:
            if ai_type == 'api':
                return await self._process_api(ai, input_data)
            elif ai_type == 'bot':
                return await self._process_bot(ai, input_data)
            elif ai_type == 'local_ai':
                return await self._process_local_ai(ai, input_data)
            elif ai_type == 'custom_ai':
                return await self._process_custom_ai(ai, input_data)
            else:
                raise ValueError(f"Unknown AI type: {ai_type}")
        except Exception as e:
            logger.error(f"Error processing with AI {ai_id}: {str(e)}")
            raise

    async def _process_api(self, ai: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': f"Bearer {ai['api-key']}", 'Content-Type': 'application/json'}
            async with session.post(ai['api-endpoint'], json=input_data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"API request failed with status {response.status}: {error_text}")

    async def _process_bot(self, ai: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        bot_file = ai['ai-file']
        if not os.path.exists(bot_file):
            raise FileNotFoundError(f"Bot file not found: {bot_file}")

        process = await asyncio.create_subprocess_exec(
            'python', bot_file,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        input_json = json.dumps(input_data).encode()
        stdout, stderr = await process.communicate(input_json)

        if process.returncode != 0:
            raise Exception(f"Bot execution failed: {stderr.decode()}")

        try:
            return json.loads(stdout.decode())
        except json.JSONDecodeError:
            raise Exception("Bot output is not valid JSON")

    async def _process_local_ai(self, ai: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        command = ai['ai-command'].split()
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        input_json = json.dumps(input_data).encode()
        stdout, stderr = await process.communicate(input_json)

        if process.returncode != 0:
            raise Exception(f"Local AI execution failed: {stderr.decode()}")

        try:
            return json.loads(stdout.decode())
        except json.JSONDecodeError:
            raise Exception("Local AI output is not valid JSON")

    async def _process_custom_ai(self, ai: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        if 'ai-command' in ai:
            return await self._process_local_ai(ai, input_data)
        elif 'ai-file' in ai:
            return await self._process_bot(ai, input_data)
        else:
            raise ValueError("Custom AI must have either 'ai-command' or 'ai-file'")

    async def cleanup_inactive_sockets(self, max_idle_time: float = 3600) -> None:
        current_time = asyncio.get_event_loop().time()
        inactive_sockets = [
            ai_id for ai_id, socket_info in self.sockets.items()
            if current_time - socket_info["last_used"] > max_idle_time
        ]
        for ai_id in inactive_sockets:
            await self.remove_socket(ai_id)
        logger.info(f"Cleaned up {len(inactive_sockets)} inactive sockets")

    async def health_check(self) -> Dict[str, Any]:
        active_sockets = len(self.sockets)
        memory_usage = self._get_memory_usage()
        return {
            "status": "healthy",
            "active_sockets": active_sockets,
            "memory_usage": memory_usage
        }

    def _get_memory_usage(self) -> float:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # in MB

    async def bulk_process(self, ai_list: List[Dict[str, Any]], input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        tasks = [self.process(ai, input_data) for ai in ai_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            {"ai_id": ai['id'], "result": result} if not isinstance(result, Exception) else {"ai_id": ai['id'], "error": str(result)}
            for ai, result in zip(ai_list, results)
        ]

    async def graceful_shutdown(self) -> None:
        for ai_id in list(self.sockets.keys()):
            await self.remove_socket(ai_id)
        logger.info("All sockets have been gracefully closed")