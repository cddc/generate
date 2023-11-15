from __future__ import annotations

import asyncio
from typing import Type

import pytest

from generate.chat_completion import (
    ChatCompletionModel,
    ChatCompletionStreamOutput,
    ChatModelRegistry,
    ChatModels,
)
from generate.chat_completion.message import Prompt
from generate.http import HttpMixin
from generate.parameters import ModelParameters
from generate.test import get_pytest_params


def test_model_type_is_unique() -> None:
    assert len(ChatModels) == len(ChatModelRegistry)


@pytest.mark.parametrize('chat_completion_model', get_pytest_params('test_chat_completion', ChatModelRegistry, types='model'))
@pytest.mark.parametrize(
    'parameters',
    [
        {},
        {'temperature': 0.5, 'top_p': 0.85, 'max_tokens': 20},
        {'temperature': 0},
        {'top_p': 0},
    ],
)
def test_http_chat_model(chat_completion_model: ChatCompletionModel, parameters: dict) -> None:
    if isinstance(chat_completion_model, HttpMixin):
        chat_completion_model.timeout = 10
    prompt = '这是测试，只回复你好'
    sync_output = chat_completion_model.generate(prompt, **parameters)
    async_output = asyncio.run(chat_completion_model.async_generate(prompt))

    assert sync_output.reply != ''
    assert async_output.reply != ''


@pytest.mark.parametrize(
    'chat_completion_model',
    get_pytest_params('test_stream_chat_completion', ChatModelRegistry, types='model', exclude=['azure']),
)
def test_http_stream_chat_model(chat_completion_model: ChatCompletionModel) -> None:
    if isinstance(chat_completion_model, HttpMixin):
        chat_completion_model.timeout = 10
    prompt = '这是测试，只回复你好'
    sync_output = list(chat_completion_model.stream_generate(prompt))[-1]
    async_output = asyncio.run(async_stream_helper(chat_completion_model, prompt))

    assert sync_output.stream.control == 'finish'
    assert sync_output.reply != ''
    assert async_output.reply != ''


async def async_stream_helper(model: ChatCompletionModel, prompt: Prompt) -> ChatCompletionStreamOutput:
    async for output in model.async_stream_generate(prompt):
        if output.stream.control == 'finish':
            return output
    raise RuntimeError('Stream did not finish')


@pytest.mark.parametrize(
    ('model_cls', 'parameters'),
    get_pytest_params(
        'test_chat_parameters', ChatModelRegistry, types=('model_cls', 'parameter'), exclude=('zhipu-character', 'bailian')
    ),
)
def test_init_chat_parameters(
    model_cls: Type[ChatCompletionModel], parameters: ModelParameters, temperature: float = 0.8
) -> None:
    parameters.temperature = temperature

    model = model_cls(parameters=parameters)

    assert model.parameters.temperature == temperature
