"""
Core client functionality
"""

import os
import time
import sys
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
import shutil
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp import ClientSession

from .utils import load_mcp_config_from_file
from .providers.openai import generate_with_openai
from .providers.deepseek import generate_with_deepseek
from .providers.anthropic import generate_with_anthropic
from .providers.ollama import generate_with_ollama
from .providers.lmstudio import generate_with_lmstudio
from .providers.vllm import generate_with_vllm
from .providers.bytedance import generate_with_bytedance
from .providers.zhipu import generate_with_zhipu

logger = logging.getLogger(__name__)


class SSEMCPClient:
    """Implementation for a SSE-based MCP server."""

    def __init__(self, server_name: str, url: str):
        self.server_name = server_name
        self.url = url
        self.tools = []
        self._streams_context = None
        self._session_context = None
        self.session = None

    async def start(self):
        try:
            self._streams_context = sse_client(url=self.url)
            streams = await self._streams_context.__aenter__()

            self._session_context = ClientSession(*streams)
            self.session = await self._session_context.__aenter__()

            # Initialize
            await self.session.initialize()
            return True
        except Exception as e:
            logger.error(f"Server {self.server_name}: SSE connection error: {str(e)}")
            return False

    async def list_tools(self):
        if not self.session:
            return []
        try:
            response = await self.session.list_tools()
            # 将 pydantic 模型转换为字典格式
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    # "inputSchema": tool.inputSchema.model_dump() if tool.inputSchema else None
                    "inputSchema": tool.inputSchema
                }
                for tool in response.tools
            ]
            return self.tools
        except Exception as e:
            logger.error(f"Server {self.server_name}: List tools error: {str(e)}")
            return []

    async def call_tool(self, tool_name: str, arguments: dict):
        if not self.session:
            return {"error": "MCP Not connected"}
        try:
            logger.info(f"开始使用MCP协议调用工具，tool_name: {tool_name}, arguments: {arguments}")
            response = await self.session.call_tool(tool_name, arguments)
            # 将 pydantic 模型转换为字典格式
            return response.model_dump() if hasattr(response, 'model_dump') else response
        except Exception as e:
            logger.error(f"call_tool: Server {self.server_name}: Tool call error: {str(e)}")
            return {"error": str(e)}

    async def stop(self):
        if self.session:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)


class MCPClient:
    """Manages MCP server connections and tool execution."""

    def __init__(self, server_name: str, command, args=None, env=None) -> None:
        self.name: str = server_name
        self.config: dict[str, Any] = {"command": command, "args": args, "env": env}
        self.stdio_context: Any | None = None
        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()
        self.tools = []

    async def start(self) -> bool:
        """Initialize the server connection."""
        command = (
            shutil.which("npx")
            if self.config["command"] == "npx"
            else self.config["command"]
        )
        if command is None:
            raise ValueError("The command must be a valid string and cannot be None.")

        server_params = StdioServerParameters(
            command=command,
            args=self.config["args"],
            env={**os.environ, **self.config["env"]}
            if self.config.get("env")
            else None,
        )
        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.session = session
            return True
        except Exception as e:
            logging.error(f"Error initializing server {self.name}: {e}")
            await self.cleanup()
            return False

    async def list_tools(self) -> list[Any]:
        """List available tools from the server.

        Returns:
            A list of available tools.

        Raises:
            RuntimeError: If the server is not initialized.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools = []

        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                tools.extend(
                    Tool(tool.name, tool.description, tool.inputSchema)
                    for tool in item[1]
                )
        # 工具名称
        self.tools = tools
        return tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        """Execute a tool with retry mechanism.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Tool arguments.
            retries: Number of retry attempts.
            delay: Delay between retries in seconds.

        Returns:
            Tool execution result.

        Raises:
            RuntimeError: If server is not initialized.
            Exception: If tool execution fails after all retries.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        attempt = 0
        while attempt < retries:
            try:
                logging.info(f"Executing {tool_name}...")
                result = await self.session.call_tool(tool_name, arguments)

                return result

            except Exception as e:
                attempt += 1
                logging.warning(
                    f"Error executing tool: {e}. Attempt {attempt} of {retries}."
                )
                if attempt < retries:
                    logging.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logging.error("Max retries reached. Failing.")
                    raise

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
                self.stdio_context = None
            except Exception as e:
                logging.error(f"Error during cleanup of server {self.name}: {e}")

    # async def stop(self):
    #     await self.cleanup()
    # async def close(self):
    #     await self.cleanup()

class Tool:
    """Represents a tool with its properties and formatting."""

    def __init__(
        self, name: str, description: str, input_schema: dict[str, Any]
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.input_schema: dict[str, Any] = input_schema

    def format_for_llm(self) -> str:
        """Format tool information for LLM.

        Returns:
            A formatted string describing the tool.
        """
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = (
                    f"- {param_name}: {param_info.get('description', 'No description')}"
                )
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)

        return f"""
Tool: {self.name}
Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""


async def generate_text(conversation: List[Dict], model_cfg: Dict,
                       all_functions: List[Dict], stream: bool = False) -> Union[Dict, AsyncGenerator]:
    """
    Generate text using the specified provider.

    Args:
        conversation: The conversation history
        model_cfg: Configuration for the model
        all_functions: Available functions for the model to call
        stream: Whether to stream the response

    Returns:
        If stream=False: Dict containing assistant_text and tool_calls
        If stream=True: AsyncGenerator yielding chunks of assistant text and tool calls
    """
    provider = model_cfg.get("provider", "").lower()

    # --- Streaming Case ---
    if stream:
        if provider == "openai":
            # *** Return the generator object directly ***
            generator_coroutine = generate_with_openai(conversation, model_cfg, all_functions, stream=True)
            # If generate_with_openai itself *is* the async generator, await it to get the generator object
            # If it returns a coroutine that *needs* awaiting to get the generator, await it.
            # Let's assume the first await gets the generator object needed for async for.
            return await generator_coroutine # Return the awaitable generator object
        elif provider == "vllm":
            # *** Return the generator object directly ***
            generator_coroutine = generate_with_vllm(conversation, model_cfg, all_functions, stream=True)
            # Await the coroutine returned by the async generator function call
            # to get the actual async generator object.
            return await generator_coroutine # Return the awaitable generator object
        elif provider == "bytedance":
            # *** Return the generator object directly ***
            generator_coroutine = generate_with_bytedance(conversation, model_cfg, all_functions, stream=True)
            # Await the coroutine returned by the async generator function call
            # to get the actual async generator object.
            return await generator_coroutine # Return the awaitable generator object
        elif provider == "deepseek":
            # *** Return the generator object directly ***
            generator_coroutine = generate_with_deepseek(conversation, model_cfg, all_functions, stream=True)
            # Await the coroutine returned by the async generator function call
            # to get the actual async generator object.
            return await generator_coroutine # Return the awaitable generator object
        elif provider == "zhipu":
            # *** Return the generator object directly ***
            generator_coroutine = generate_with_zhipu(conversation, model_cfg, all_functions, stream=True)
            # Await the coroutine returned by the async generator function call
            # to get the actual async generator object.
            return await generator_coroutine # Return the awaitable generator object
        elif provider in ["anthropic", "ollama", "lmstudio"]:
             # This part needs to be an async generator that yields the *single* result
             async def wrap_response():
                 # Call the non-streaming function
                 if provider == "anthropic":
                     result = await generate_with_anthropic(conversation, model_cfg, all_functions)
                 elif provider == "ollama":
                     result = await generate_with_ollama(conversation, model_cfg, all_functions)
                 elif provider == "lmstudio":
                     result = await generate_with_lmstudio(conversation, model_cfg, all_functions)
                 else: # Should not happen based on outer check, but good practice
                     result = {"assistant_text": f"Unsupported provider '{provider}'", "tool_calls": []}
                 # Yield the complete result as a single item in the stream
                 yield result
             # *** Return the RESULT OF CALLING wrap_response() ***
             return wrap_response() # Return the async generator OBJECT
        else:
             # Fallback for unsupported streaming providers
             async def empty_gen():
                 yield {"assistant_text": f"Unsupported streaming provider '{provider}'", "tool_calls": []}
                 # The 'if False:' trick ensures this is treated as an async generator
                 if False: yield
             return empty_gen()

    # --- Non-Streaming Case ---
    else:
        if provider == "openai":
            return await generate_with_openai(conversation, model_cfg, all_functions, stream=False)
        elif provider == "deepseek":
            return await generate_with_deepseek(conversation, model_cfg, all_functions, stream=False)
        elif provider == "zhipu":
            return await generate_with_zhipu(conversation, model_cfg, all_functions, stream=False)
        elif provider == "bytedance":
            return await generate_with_bytedance(conversation, model_cfg, all_functions, stream=False)
        elif provider == "vllm":
            return await generate_with_vllm(conversation, model_cfg, all_functions, stream=False)
        elif provider == "anthropic":
            return await generate_with_anthropic(conversation, model_cfg, all_functions)
        elif provider == "ollama":
            return await generate_with_ollama(conversation, model_cfg, all_functions)
        elif provider == "lmstudio":
            return await generate_with_lmstudio(conversation, model_cfg, all_functions)
        else:
            return {"assistant_text": f"Unsupported provider '{provider}'", "tool_calls": []}

async def log_messages_to_file(messages: List[Dict], functions: List[Dict], log_path: str):
    """
    Log messages and function definitions to a JSONL file.

    Args:
        messages: List of messages to log
        functions: List of function definitions
        log_path: Path to the log file
    """
    try:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Append to file
        with open(log_path, "a") as f:
            f.write(json.dumps({
                "messages": messages,
                "functions": functions
            }) + "\n")
    except Exception as e:
        logger.error(f"Error logging messages to {log_path}: {str(e)}")

async def process_tool_call(tc: Dict, servers: Dict[str, MCPClient], quiet_mode: bool) -> Optional[Dict]:
    """Process a single tool call and return the result"""
    func_name = tc["function"]["name"]
    func_args_str = tc["function"].get("arguments", "{}")
    try:
        func_args = json.loads(func_args_str)
    except:
        func_args = {}

    parts = func_name.split("_", 1)
    if len(parts) != 2:
        return {
            "role": "tool",
            "tool_call_id": tc["id"],
            "name": func_name,
            "content": json.dumps({"error": "Invalid function name format"})
        }

    srv_name, tool_name = parts
    print(f"\n调用process_tool_call开始获取运行MCP工具{tool_name} from {srv_name} {json.dumps(func_args, ensure_ascii=False)}")

    if srv_name not in servers:
        print(f"错误：注意，模型生成的服务器{srv_name}不在服务器列表中，请检查配置文件，或者查看你的mcp配置是否包含了特殊字符_")
        return {
            "role": "tool",
            "tool_call_id": tc["id"],
            "name": func_name,
            "content": json.dumps({"error": f"Unknown server: {srv_name}"})
        }

    # Get the tool's schema
    tool_schema = None
    for tool in servers[srv_name].tools:
        if tool.name == tool_name:
            tool_schema = tool.input_schema
            break

    if tool_schema:
        # Ensure required parameters are present
        required_params = tool_schema.get("required", [])
        for param in required_params:
            if param not in func_args:
                return {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": func_name,
                    "content": json.dumps({"error": f"Missing required parameter: {param}"})
                }
    print(f"开始调用call_tool")
    result = await servers[srv_name].call_tool(tool_name, func_args)
    print(f"工具{tool_name}运行结果:")
    result_content = "\n".join(content.text for content in result.content)

    return {
        "role": "tool",
        "tool_call_id": tc["id"],
        "name": func_name,
        "content": {"text": result_content}
    }

async def run_interaction(
    user_query: str,
    model_name: Optional[str] = None,
    config: Optional[dict] = None,
    config_path: str = "mcp_config.json",
    quiet_mode: bool = False,
    log_messages_path: Optional[str] = None,
    stream: bool = False
) -> Union[str, AsyncGenerator[str, None]]:
    """
    Run an interaction with the MCP servers.

    Args:
        user_query: The user's query
        model_name: Name of the model to use (optional)
        config: Configuration dict (optional, if not provided will load from config_path)
        config_path: Path to the configuration file (default: mcp_config.json)
        quiet_mode: Whether to suppress intermediate output (default: False)
        log_messages_path: Path to log messages in JSONL format (optional)
        stream: Whether to stream the response (default: False)

    Returns:
        If stream=False: The final text response
        If stream=True: AsyncGenerator yielding chunks of the response
    """
    # 1) If config is not provided, load from file:
    if config is None:
        config = await load_mcp_config_from_file(config_path)

    servers_cfg = config.get("mcpServers", {})
    models_cfg = config.get("models", [])

    # 2) Choose a model
    chosen_model = None
    if model_name:
        for m in models_cfg:
            if m.get("model") == model_name or m.get("title") == model_name:
                chosen_model = m
                break
        if not chosen_model:
            # fallback to default or fail
            for m in models_cfg:
                if m.get("default"):
                    chosen_model = m
                    break
    else:
        # if model_name not specified, pick default
        for m in models_cfg:
            if m.get("default"):
                chosen_model = m
                break
        if not chosen_model and models_cfg:
            chosen_model = models_cfg[0]

    if not chosen_model:
        error_msg = "No suitable model found in config."
        if stream:
            async def error_gen():
                yield error_msg
            return error_gen()
        return error_msg

    # 3) Start servers
    servers = {}
    all_functions = []
    for server_name, conf in servers_cfg.items():
        if "url" in conf:  # SSE server
            client = SSEMCPClient(server_name, conf["url"])
        else:  # Local process-based server
            client = MCPClient(
                server_name=server_name,
                command=conf.get("command"),
                args=conf.get("args", []),
                env=conf.get("env", {})
            )
        ok = await client.start()
        if not ok:
            if not quiet_mode:
                print(f"[WARN] Could not start server {server_name}")
            continue
        else:
            print(f"[OK] {server_name}")

        # gather tools
        tools = await client.list_tools()
        for t in tools:
            input_schema = t.get("inputSchema") or {"type": "object", "properties": {}}
            fn_def = {
                "name": f"{server_name}_{t['name']}",
                "description": t.get("description", ""),
                "parameters": input_schema
            }
            all_functions.append(fn_def)

        servers[server_name] = client

    if not servers:
        error_msg = "No MCP servers could be started."
        if stream:
            async def error_gen():
                yield error_msg
            return error_gen()
        return error_msg

    conversation = []
    logger.info(f"all_functions: {all_functions}")
    # 4) Build conversation
    # Get system message - either from systemMessageFile, systemMessage, or default
    system_msg = "You are a helpful assistant."
    if "systemMessageFile" in chosen_model:
        try:
            with open(chosen_model["systemMessageFile"], "r", encoding="utf-8") as f:
                system_msg = f.read()
        except Exception as e:
            logger.warning(f"Failed to read system message file: {e}")
            # Fall back to direct systemMessage if available
            conversation.append({"role": "system", "content": chosen_model.get("systemMessage", system_msg)})
    else:
        conversation.append({"role": "system", "content": chosen_model.get("systemMessage", system_msg)})
    if "systemMessageFiles" in chosen_model:
        for file in chosen_model["systemMessageFiles"]:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    system_msg = f.read()
                    conversation.append({"role": "system", "content": "File: " + file + "\n" + system_msg})
            except Exception as e:
                logger.warning(f"Failed to read system message file: {e}")

    conversation.append({"role": "user", "content": user_query})

    async def cleanup():
        """Clean up servers and log messages"""
        if log_messages_path:
            await log_messages_to_file(conversation, all_functions, log_messages_path)
        for cli in servers.values():
            await cli.stop()

    if stream:
        async def stream_response():
            try:
                while True:  # Main conversation loop
                    generator = await generate_text(conversation, chosen_model, all_functions, stream=True)
                    accumulated_text = ""
                    tool_calls_processed = False
                    while True:
                        try:
                            anext_task = asyncio.create_task(generator.__anext__())
                        except StopAsyncIteration:
                            break  # 生成器结束

                        chunk = None
                        while True:
                            timer_task = asyncio.create_task(asyncio.sleep(2))  # 设置超时时间2秒
                            done, pending = await asyncio.wait(
                                [anext_task, timer_task],
                                return_when=asyncio.FIRST_COMPLETED
                            )

                            if anext_task in done:
                                timer_task.cancel()
                                try:
                                    chunk = await anext_task
                                except StopAsyncIteration:
                                    break
                                except Exception as e:
                                    raise e
                                break  # 成功获取到chunk，处理它
                            else:
                                # 发送thinking提示
                                yield {
                                    "assistant_text": " ",
                                    "tool_calls": [],
                                    "is_chunk": True,
                                    "token": True
                                }
                        if not chunk:
                            break  # 生成器已结束
                        if chunk.get("is_chunk", False):
                            # Immediately yield each token without accumulation
                            if chunk.get("token", False):
                                yield chunk["assistant_text"]
                            accumulated_text += chunk["assistant_text"]
                        else:
                            # This is the final chunk with tool calls
                            if accumulated_text != chunk["assistant_text"]:
                                # If there's any remaining text, yield it
                                remaining = chunk["assistant_text"][len(accumulated_text):]
                                if remaining:
                                    yield remaining

                            # Process any tool calls from the final chunk
                            tool_calls = chunk.get("tool_calls", [])
                            if tool_calls:
                                # Add type field to each tool call
                                for tc in tool_calls:
                                    tc["type"] = "function"
                                # Add the assistant's message with tool calls
                                assistant_message = {
                                    "role": "assistant",
                                    "content": chunk["assistant_text"],
                                    "tool_calls": tool_calls
                                }
                                conversation.append(assistant_message)

                                # Process each tool call
                                for tc in tool_calls:
                                    if tc.get("function", {}).get("name"):
                                        task = asyncio.create_task(process_tool_call(tc, servers, quiet_mode))

                                        # 每1秒 yield 一次"running"直到 task 完成
                                        while not task.done():
                                            await asyncio.sleep(1)
                                            yield {
                                                "assistant_text": ".",
                                                "tool_calls": [],
                                                "is_chunk": True,
                                                "token": True
                                            }

                                        # 一旦任务完成
                                        result = await task
                                        if result:
                                            conversation.append(result)
                                            tool_calls_processed = True
                    
                    # Break the loop if no tool calls were processed
                    if not tool_calls_processed:
                        break
                    
            finally:
                await cleanup()
        
        return stream_response()
    else:
        try:
            final_text = ""
            while True:
                gen_result = await generate_text(conversation, chosen_model, all_functions, stream=False)
                
                assistant_text = gen_result["assistant_text"]
                final_text = assistant_text
                tool_calls = gen_result.get("tool_calls", [])

                # Add the assistant's message
                assistant_message = {"role": "assistant", "content": assistant_text}
                if tool_calls:
                    # Add type field to each tool call
                    for tc in tool_calls:
                        tc["type"] = "function"
                    assistant_message["tool_calls"] = tool_calls
                conversation.append(assistant_message)
                logger.info(f"Added assistant message: {json.dumps(assistant_message, indent=2)}")

                if not tool_calls:
                    break

                for tc in tool_calls:
                    result = await process_tool_call(tc, servers, quiet_mode)
                    if result:
                        conversation.append(result)
                        logger.info(f"Added tool result: {json.dumps(result, indent=2)}")

            return final_text
        finally:
            await cleanup()
