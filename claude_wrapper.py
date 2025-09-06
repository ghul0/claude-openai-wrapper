"""
Claude Code SDK wrapper for OpenAI API compatibility
"""
import os
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
from models import (
    ChatCompletionRequest, ChatCompletionResponse, 
    Message, Choice, Usage
)
from json_formatter import ensure_json_response, create_json_instruction
import json
import logging
import asyncio
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Set CLAUDE_CODE_PATH environment variable if provided
if claude_path := os.getenv("CLAUDE_CODE_PATH"):
    os.environ["CLAUDE_CODE_PATH"] = claude_path
    logger.info(f"Using Claude CLI at: {claude_path}")


class ClaudeCodeWrapper:
    """
    Wrapper class that bridges OpenAI API format with Claude Code SDK
    """
    
    def __init__(self, default_model: str = "claude-3-5-sonnet-20241022"):
        self.default_model = default_model
        self.model_mapping = {
            # Map OpenAI-style model names to Claude models
            "gpt-4": "claude-3-5-sonnet-20241022",
            "gpt-4-turbo": "claude-3-5-sonnet-20241022",
            "gpt-3.5-turbo": "claude-3-5-haiku-20241022",
            "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku": "claude-3-5-haiku-20241022",
            "claude-3-5-sonnet-20241022": "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022": "claude-3-5-haiku-20241022",
        }
    
    async def process_request(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Process an OpenAI-format chat completion request using Claude Code SDK.
        
        Args:
            request: OpenAI ChatCompletionRequest
            
        Returns:
            OpenAI ChatCompletionResponse
        """
        try:
            # Extract messages
            system_prompt = self._extract_system_prompt(request.messages)
            user_message = self._extract_user_message(request.messages)
            
            # Configure Claude options
            options = self._create_claude_options(request, system_prompt)
            
            # Process with Claude
            response_text = await self._call_claude(user_message, options, request)
            
            # Create OpenAI-format response
            return self._create_response(response_text, request)
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            raise
    
    def _extract_system_prompt(self, messages: List[Message]) -> Optional[str]:
        """Extract system prompt from messages"""
        system_messages = [msg.content for msg in messages if msg.role == "system"]
        return "\n".join(system_messages) if system_messages else None
    
    def _extract_user_message(self, messages: List[Message]) -> str:
        """Extract the latest user message"""
        user_messages = [msg for msg in messages if msg.role == "user"]
        if not user_messages:
            raise ValueError("No user message found in request")
        
        # Return the last user message (single-turn support only)
        return user_messages[-1].content
    
    def _create_claude_options(self, request: ChatCompletionRequest, system_prompt: Optional[str]) -> ClaudeCodeOptions:
        """Create ClaudeCodeOptions from the request"""
        # Map model name
        model = self.model_mapping.get(request.model, request.model)
        
        # Build options
        options_dict = {
            "model": model,
            "max_turns": 1,  # Single turn for API compatibility
            "permission_mode": "bypassPermissions",  # No interactive prompts
            "max_thinking_tokens": 8000,
        }
        
        # Add system prompt
        if system_prompt:
            options_dict["system_prompt"] = system_prompt
        
        # Add JSON instruction if needed
        if request.response_format and request.response_format.type == "json_object":
            json_instruction = create_json_instruction()
            if system_prompt:
                options_dict["append_system_prompt"] = json_instruction
            else:
                options_dict["system_prompt"] = json_instruction
        
        # Configure allowed tools (you can customize this based on your needs)
        # Available tools: Bash, Read, Write, Edit, Grep, Glob, LS, WebSearch, etc.
        options_dict["allowed_tools"] = ["Read", "Grep", "Glob", "LS"]
        
        return ClaudeCodeOptions(**options_dict)
    
    async def _call_claude(self, message: str, options: ClaudeCodeOptions, request: ChatCompletionRequest) -> str:
        """
        Call Claude Code SDK and collect the response.
        
        Args:
            message: User message to send
            options: Claude options
            request: Original request for additional context
            
        Returns:
            Response text from Claude
        """
        full_response = []
        
        try:
            async with ClaudeSDKClient(options=options) as client:
                # Send the query
                await client.query(message)
                
                # Collect response
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                full_response.append(block.text)
                    
                    # Log any errors
                    if type(msg).__name__ == "ErrorMessage":
                        logger.error(f"Claude error: {msg}")
                
        except Exception as e:
            logger.error(f"Error calling Claude: {str(e)}")
            # Return error as JSON if JSON mode is requested
            if request.response_format and request.response_format.type == "json_object":
                return json.dumps({"error": str(e)})
            else:
                raise
        
        response_text = ''.join(full_response)
        
        # Ensure JSON format if requested
        if request.response_format and request.response_format.type == "json_object":
            response_text = ensure_json_response(response_text)
        
        return response_text
    
    def _create_response(self, content: str, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Create OpenAI-format response"""
        # Create assistant message
        assistant_message = Message(role="assistant", content=content)
        
        # Create choice
        choice = Choice(
            index=0,
            message=assistant_message,
            finish_reason="stop"
        )
        
        # Estimate token usage (rough approximation)
        # Real implementation would use proper tokenization
        prompt_tokens = sum(len(msg.content.split()) for msg in request.messages) * 1.3
        completion_tokens = len(content.split()) * 1.3
        
        usage = Usage(
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            total_tokens=int(prompt_tokens + completion_tokens)
        )
        
        return ChatCompletionResponse(
            model=request.model,
            choices=[choice],
            usage=usage
        )