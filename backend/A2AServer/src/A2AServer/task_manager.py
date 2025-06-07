import json
import os
from typing import AsyncIterable
from A2AServer.common.A2Atypes import (
    SendTaskRequest,
    TaskSendParams,
    Message,
    TaskStatus,
    Artifact,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TextPart,
    TaskState,
    Task,
    SendTaskResponse,
    InternalError,
    JSONRPCResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent
)
from A2AServer.common.server.task_manager import InMemoryTaskManager
from A2AServer.agent import BasicAgent
import A2AServer.common.server.utils as utils
import asyncio
import logging
import traceback

logger = logging.getLogger(__name__)

if os.environ.get("DECODE_TOOL"):
    from decode_tool import decode_tool_calls_to_string, decode_tool_result_to_string
else:
    def decode_tool_calls_to_string(content):
        return content
    def decode_tool_result_to_string(content):
        return content


class AgentTaskManager(InMemoryTaskManager):
    """Task manager for AG2 MCP agent."""

    def __init__(self, agent: BasicAgent):
        super().__init__()
        self.agent = agent

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle synchronous task requests.
        
        This method processes one-time task requests and returns a complete response.
        Unlike streaming tasks, this waits for the full agent response before returning.
        """
        validation_error = self._validate_request(request)
        if validation_error:
            return SendTaskResponse(id=request.id, error=validation_error.error)

        await self.upsert_task(request.params)
        # Update task store to WORKING state (return value not used)
        await self.update_store(
            request.params.id, TaskStatus(state=TaskState.WORKING), None
        )

        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)

        try:
            agent_response = self.agent.invoke(query, task_send_params.sessionId)
            return await self._handle_send_task(request, agent_response)
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            return SendTaskResponse(
                id=request.id,
                error=InternalError(message=f"Error during on_send_task: {str(e)}")
            )

    async def on_send_task_subscribe(
            self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """
        Handle streaming task requests with SSE subscription.
        处理流式任务请求， 用户请求先到这里
        This method initiates a streaming task and returns incremental updates
        to the client as they become available. It uses Server-Sent Events (SSE)
        to push updates to the client as the agent generates them.
        """
        error = self._validate_request(request)
        if error:
            return error
        await self.upsert_task(request.params)
        return self._stream_generator(request)

    # -------------------------------------------------------------
    # Agent response handlers
    # -------------------------------------------------------------

    async def _handle_send_task(
            self, request: SendTaskRequest, agent_response: dict
    ) -> SendTaskResponse:
        """
        Handle the 'tasks/send' JSON-RPC method by processing agent response.
        
        This method processes the synchronous (one-time) response from the agent,
        transforms it into the appropriate task status and artifacts, and 
        returns a complete SendTaskResponse.
        """
        task_send_params: TaskSendParams = request.params
        task_id = task_send_params.id
        history_length = task_send_params.historyLength
        task_status = None

        parts = [TextPart(type="text", text=agent_response["content"])]
        artifact = None
        if agent_response["require_user_input"]:
            task_status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message=Message(role="agent", parts=parts),
            )
        else:
            task_status = TaskStatus(state=TaskState.COMPLETED)
            artifact = Artifact(parts=parts)
        # Update task store and get result for response
        updated_task = await self.update_store(
            task_id, task_status, None if artifact is None else [artifact]
        )
        # Use the updated task to create a response with correct history
        task_result = self.append_task_history(updated_task, history_length)
        return SendTaskResponse(id=request.id, result=task_result)

    async def _stream_generator(
            self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """
        Handle the 'tasks/sendSubscribe' JSON-RPC method for streaming responses.
        """
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)
        logger.info(f"发送过来的请求是 {query}, 参数是 {task_send_params}")
        is_first_token = True
        artifacts = []
        try:
            async for item in self.agent.stream(query, task_send_params.sessionId):
                logger.info("返回的item: ", item)
                if item.get("type") and item["type"] == "tool_call":
                    tool_data = decode_tool_calls_to_string(item["content"])
                    logger.info(f"CALL的工具的解析结果: {tool_data}")
<<<<<<< HEAD
                    # 处理不同类型的tool_data，确保最终是字典类型
                    if isinstance(tool_data, str):
                        try:
                            import json
                            parsed_data = json.loads(tool_data)
                            # 如果解析后是列表，包装成字典
                            if isinstance(parsed_data, list):
                                tool_data = {"tool_calls": parsed_data}
                            else:
                                tool_data = parsed_data
                        except json.JSONDecodeError:
                            logger.error(f"无法解析工具调用数据: {tool_data}")
                            tool_data = {"error": "无法解析工具调用数据"}
                    elif isinstance(tool_data, list):
                        # 如果是列表，包装成字典
                        tool_data = {"tool_calls": tool_data}
                    elif isinstance(tool_data, dict):
                        # 如果已经是字典，直接使用
                        pass
                    else:
                        # 其他类型，转换为字典
                        tool_data = {"data": tool_data}
                    # 创建符合Pydantic模型的DataPart
                    from A2AServer.common.A2Atypes import DataPart
                    data_part = DataPart(type="data", data=tool_data)
                    message = Message(role="agent", parts=[data_part])
=======
                    if isinstance(tool_data, str):
                        parts = [{"type": "text", "text": tool_data}]
                    else:
                        parts = [{"type": "data", "data": tool_data}]
                    message = Message(role="agent", parts=parts)
>>>>>>> 284a1102a106dbcfa9e85dbc6c8cb09d5fe51a85
                    task_status = TaskStatus(state=TaskState.WORKING, message=message)
                    task_update_event = TaskStatusUpdateEvent(
                        id=task_send_params.id,
                        status=task_status,
                        final=False,
                    )
                    logger.info(f"发送的item的更新消息是: {task_update_event}")
                    yield SendTaskStreamingResponse(id=request.id, result=task_update_event)
                elif item.get("type") and item["type"] == "tool_result":
                    tool_data = decode_tool_result_to_string(item["content"])
                    logger.info(f"RESULT的工具的解析结果: {tool_data}")
<<<<<<< HEAD
                    # 处理不同类型的tool_data，确保最终是字典类型
                    if isinstance(tool_data, str):
                        try:
                            parsed_data = json.loads(tool_data)
                            # 如果解析后是列表，包装成字典
                            if isinstance(parsed_data, list):
                                tool_data = {"tool_results": parsed_data}
                            else:
                                tool_data = parsed_data
                        except json.JSONDecodeError:
                            logger.error(f"无法解析工具结果数据: {tool_data}")
                            tool_data = {"error": "无法解析工具结果数据"}
                    elif isinstance(tool_data, list):
                        # 如果是列表，包装成字典
                        tool_data = {"tool_results": tool_data}
                    elif isinstance(tool_data, dict):
                        # 如果已经是字典，直接使用
                        pass
                    else:
                        # 其他类型，转换为字典
                        tool_data = {"data": tool_data}
                    # 创建符合Pydantic模型的DataPart
                    data_part = DataPart(type="data", data=tool_data)
                    message = Message(role="agent", parts=[data_part])
=======
                    if isinstance(tool_data, str):
                        parts = [{"type": "text", "text": tool_data}]
                    else:
                        parts = [{"type": "data", "data": tool_data}]
                    message = Message(role="agent", parts=parts)
>>>>>>> 284a1102a106dbcfa9e85dbc6c8cb09d5fe51a85
                    task_status = TaskStatus(state=TaskState.WORKING, message=message)
                    task_update_event = TaskStatusUpdateEvent(
                        id=task_send_params.id,
                        status=task_status,
                        final=False,
                    )
                    logger.info(f"发送的item的更新消息是: {task_update_event}")
                    yield SendTaskStreamingResponse(id=request.id, result=task_update_event)
                elif item.get("type") and item["type"] == "reasoning":
                    content = item["content"]
                    if content is None:
                        content = ""
                    logger.info(f"推理的解析的结果: {content}")
                    # 创建符合Pydantic模型的TextPart
                    text_part = TextPart(type="text", text=content)
                    message = Message(role="agent", parts=[text_part])
                    task_status = TaskStatus(state=TaskState.WORKING, message=message)
                    task_update_event = TaskStatusUpdateEvent(
                        id=task_send_params.id,
                        status=task_status,
                        final=False,
                    )
                    logger.info(f"发送的item的更新消息是: {task_update_event}")
                    yield SendTaskStreamingResponse(id=request.id, result=task_update_event)
                elif item.get("type") and item["type"] == "normal":  # 正常的文本内容
                    is_task_complete = item["is_task_complete"]
                    # 初始化task_state变量
                    task_state = TaskState.WORKING
                    if not is_task_complete:
                        if item.get("content"):
                            # 创建符合Pydantic模型的TextPart
                            text_part = TextPart(type="text", text=item["content"])
                            append_value = not is_first_token
                            artifact = Artifact(parts=[text_part], index=0, append=append_value, lastChunk=False)
                            # 逐条发送每个生成的内容
                            logger.info(f"发送的artifact是: {artifact}")
                            yield SendTaskStreamingResponse(
                                id=request.id,
                                result=TaskArtifactUpdateEvent(
                                    id=task_send_params.id,
                                    artifact=artifact,
                                )
                            )
                            is_first_token = False
                            artifacts.append(artifact)
                    else:
                        # 初始化task_state变量
                        task_state = TaskState.COMPLETED
                        if isinstance(item["content"], dict):
                            if ("response" in item["content"]
                                    and "result" in item["content"]["response"]):
                                data = json.loads(item["content"]["response"]["result"])
                                task_state = TaskState.INPUT_REQUIRED
                            else:
                                data = item["content"]
                                task_state = TaskState.COMPLETED
                            # 创建符合Pydantic模型的DataPart
                            data_part = DataPart(type="data", data=data)
                            parts = [data_part]
                        else:
                            task_state = TaskState.COMPLETED
                            # 创建符合Pydantic模型的TextPart
                            text_part = TextPart(type="text", text=item["content"])
                            parts = [text_part]
                        logger.info(f"现在发送的parts是: {parts}")
                        artifact = Artifact(parts=parts, index=0, append=True, lastChunk=True)
                        yield SendTaskStreamingResponse(
                            id=request.id,
                            result=TaskArtifactUpdateEvent(
                                id=task_send_params.id,
                                artifact=artifact,
                            )
                        )
                        artifacts.append(artifact)
                else:
                    # 不带工具返回，状态消息
                    task_status = TaskStatus(
                        state=TaskState.WORKING,
                    )
                    task_update_event = TaskStatusUpdateEvent(
                        id=task_send_params.id,
                        status=task_status,
                        final=False,
                    )
                    logger.info(f"发送的item的更新消息是: {task_update_event}")
                    yield SendTaskStreamingResponse(id=request.id, result=task_update_event)
            if item["is_task_complete"]:
                task_status = TaskStatus(
                    state=TaskState.COMPLETED,
                )
            else:
                task_status = TaskStatus(
                    state=TaskState.WORKING,
                )
            await self.update_store(task_send_params.id, task_status, artifacts)
            task_update_event = TaskStatusUpdateEvent(
                id=task_send_params.id,
                status=task_status,
                final=False,
            )
            # logger.info(f"发送的更新消息是: {task_update_event}") # 暂时不用最后的更新消息了，只发送最后的结果
            # yield SendTaskStreamingResponse(id=request.id, result=task_update_event)
            if item["is_task_complete"]:
                logger.info(f"发送的任务完成消息")
                yield SendTaskStreamingResponse(
                    id=request.id,
                    result=TaskStatusUpdateEvent(
                        id=task_send_params.id,
                        status=TaskStatus(
                            state=task_status.state,
                        ),
                        final=True
                    )
                )
        except Exception as e:
            logger.error(f"An error occurred while streaming the response: {e}")
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            yield JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message="An error occurred while streaming the response"
                ),
            )

    def _validate_request(
            self, request: SendTaskRequest | SendTaskStreamingRequest
    ) -> JSONRPCResponse | None:
        """
        Validate task request parameters for compatibility with agent capabilities.
        
        Ensures that the client's requested output modalities are compatible with
        what the agent can provide.
        
        Returns:
            JSONRPCResponse with an error if validation fails, None otherwise.
        """
        task_send_params: TaskSendParams = request.params
        if not utils.are_modalities_compatible(
                task_send_params.acceptedOutputModes, BasicAgent.SUPPORTED_CONTENT_TYPES
        ):
            logger.warning(
                "Unsupported output mode. Received %s, Support %s",
                task_send_params.acceptedOutputModes,
                BasicAgent.SUPPORTED_CONTENT_TYPES,
            )
            return utils.new_incompatible_types_error(request.id)
        return None

    def _get_user_query(self, task_send_params: TaskSendParams) -> str:
        """
        Extract the user's text query from the task parameters.
        
        Extracts and returns the text content from the first part of the user's message.
        Currently only supports text parts.
        
        Args:
            task_send_params: The parameters of the task containing the user's message.
            
        Returns:
            str: The extracted text query.
            
        Raises:
            ValueError: If the message part is not a TextPart.
        """
        part = task_send_params.message.parts[0]
        if not isinstance(part, TextPart):
            raise ValueError("Only text parts are supported")
        return part.text
