import asyncio
import os
import socket
import subprocess
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def test_loopback_http_roundtrip_and_private_store_disabled():
    with socket.socket() as socket_:
        socket_.bind(("127.0.0.1", 0))
        port = socket_.getsockname()[1]
    env = {
        **os.environ,
        "JT_LOCAL_DB": "/deliberately/unavailable/private.sqlite",
        "JT_PRINCIPAL": "fake-user",
        "PISTE_CLIENT_ID": "",
        "PISTE_CLIENT_SECRET": "",
        "JUDILIBRE_KEY_ID": "",
    }
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "droit_territorial.cli",
            "serve",
            "--transport",
            "streamable-http",
            "--port",
            str(port),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=2) as client:
            for _ in range(100):
                if process.poll() is not None:
                    raise AssertionError(process.communicate()[1].decode()[-2000:])
                try:
                    await client.get(url)
                    break
                except httpx.ConnectError:
                    await asyncio.sleep(0.05)
            else:
                raise AssertionError("MCP HTTP did not start within five seconds")
        async with (
            streamable_http_client(url + "/mcp") as streams,
            ClientSession(streams[0], streams[1], read_timeout_seconds=10) as session,
        ):
            await session.initialize()
            method = await session.call_tool("get_methodology", {"topic": "core"})
            assert not method.is_error
            local = await session.call_tool(
                "search_local_acts", {"query": "secret", "case_id": "c"}
            )
            assert local.is_error
            assert local.structured_content["error"]["code"] == "local_not_configured"
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)
