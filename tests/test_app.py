import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

# Assuming your application structure allows this import
# Adjust the import path based on your project structure
from audio_summary.app import _summarize
from audio_summary.api_utils import (
    get_openai_prompt_parts,
    get_openai_default_config,
    get_prompt_parts as get_gemini_prompt_parts, # Alias for clarity
    get_gemini_default_config,
    get_gemini_default_safety_setting
)
from audio_summary.exceptions import OpenaiApiKeyNotFound

# Mock environment variables before imports that might use them at module level
# or ensure they are set before tests run that rely on them.
# For _summarize, API keys are checked inside, so direct os.environ patching is better.

@pytest.mark.asyncio
async def test_summarize_function_calls_openai_when_specified():
    """
    Tests that _summarize calls the OpenAI API and utility functions
    when by_='openai'.
    """
    with patch('os.environ.get', return_value='fake_api_key'), \
         patch('openai.AsyncOpenAI') as mock_async_openai_client_constructor, \
         patch('audio_summary.app.get_openai_prompt_parts', return_value=[{"role": "system", "content": "Test"}]) as mock_get_openai_prompts, \
         patch('audio_summary.app.get_openai_default_config', return_value={"model": "test-model"}) as mock_get_openai_config:

        # Configure the mock AsyncOpenAI client instance
        mock_openai_instance = AsyncMock()
        mock_async_openai_client_constructor.return_value = mock_openai_instance
        
        # Configure the chat.completions.create method
        mock_chat_completions_create = AsyncMock()
        mock_chat_completions_create.return_value.choices = [MagicMock(message=MagicMock(content="OpenAI summary"))]
        mock_openai_instance.chat.completions.create = mock_chat_completions_create

        result = await _summarize(content="Test content", by_="openai", resp_lang="en")

        assert result == "OpenAI summary"
        mock_async_openai_client_constructor.assert_called_once_with(api_key='fake_api_key')
        mock_get_openai_prompts.assert_called_once_with(content="Test content", resp_lang="en")
        mock_get_openai_config.assert_called_once_with()
        mock_chat_completions_create.assert_called_once_with(
            messages=[{"role": "system", "content": "Test"}],
            model="test-model"
        )

@pytest.mark.asyncio
async def test_summarize_function_calls_gemini_when_specified():
    """
    Tests that _summarize calls the Gemini API and utility functions
    when by_='gemini'.
    """
    with patch('os.environ.get', return_value='fake_api_key'), \
         patch('google.generativeai.GenerativeModel') as mock_generative_model_constructor, \
         patch('google.generativeai.configure') as mock_gemini_configure, \
         patch('audio_summary.app.get_prompt_parts', return_value=["Gemini prompt"]) as mock_get_gemini_prompts, \
         patch('audio_summary.app.get_gemini_default_config', return_value={"temperature": 0.8}) as mock_get_gemini_config, \
         patch('audio_summary.app.get_gemini_default_safety_setting', return_value=[]) as mock_get_gemini_safety:

        # Configure the mock GenerativeModel instance
        mock_gemini_instance = MagicMock()
        mock_generative_model_constructor.return_value = mock_gemini_instance
        mock_gemini_instance.generate_content.return_value = MagicMock(text="Gemini summary")

        result = await _summarize(content="Test content", by_="gemini", resp_lang="en")

        assert result == "Gemini summary"
        mock_gemini_configure.assert_called_once_with(api_key='fake_api_key')
        mock_generative_model_constructor.assert_called_once_with(
            model_name="gemini-1.5-pro",
            generation_config={"temperature": 0.8},
            safety_settings=[]
        )
        mock_get_gemini_prompts.assert_called_once_with("Test content", "en")
        mock_get_gemini_config.assert_called_once_with()
        mock_get_gemini_safety.assert_called_once_with()
        mock_gemini_instance.generate_content.assert_called_once_with(["Gemini prompt"])


@pytest.mark.asyncio
async def test_summarize_openai_raises_exception_if_no_key():
    """
    Tests that _summarize raises OpenaiApiKeyNotFound if the OPENAI_API_KEY is not set
    when by_='openai'.
    """
    # Simulate that os.environ.get("OPENAI_API_KEY") returns None
    with patch('os.environ.get', side_effect=lambda key, default=None: None if key == "OPENAI_API_KEY" else 'fake_key_for_google'), \
         patch('openai.AsyncOpenAI') as mock_async_openai_client_constructor: # Also mock the client so it's not actually called
        
        with pytest.raises(OpenaiApiKeyNotFound):
            await _summarize(content="Test content", by_="openai", resp_lang="en")
        
        mock_async_openai_client_constructor.assert_not_called()

# It might be good to add a test for by_ being an invalid value,
# but the function signature uses Literal, which should ideally be caught by type checkers.
# A runtime check is also present.

def main():
    """
    Main function to run pytest.
    This allows running tests with `python tests/test_app.py`.
    """
    pytest.main([__file__])

if __name__ == "__main__":
    # This is to ensure that asyncio event loop is managed correctly when running the file directly
    asyncio.run(main())
    # For direct execution, it's often simpler to just call pytest.main()
    # but since tests are async, running pytest.main() within asyncio.run() might be needed
    # depending on pytest's own asyncio handling capabilities or if we had async fixtures
    # at the module/session scope.
    # However, pytest handles asyncio tests well on its own when run via `pytest` command.
    # The `main` and `if __name__ == "__main__":` block is optional.
    pass # Pytest will collect and run tests regardless of this block.
