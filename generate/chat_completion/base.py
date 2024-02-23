from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, AsyncIterator, ClassVar, Iterator, Type, TypeVar, get_type_hints

from pydantic import BaseModel
from typing_extensions import Self, Unpack

from generate.chat_completion.message import Prompt
from generate.chat_completion.model_output import ChatCompletionOutput, ChatCompletionStreamOutput
from generate.http import HttpClient
from generate.model import GenerateModel, ModelParameters
from generate.platforms import PlatformSettings

O = TypeVar('O', bound=BaseModel)  # noqa: E741

if TYPE_CHECKING:
    from generate.modifiers.agent import Agent, AgentKwargs
    from generate.modifiers.session import Session
    from generate.modifiers.structure import Structure, StructureKwargs


logger = logging.getLogger(__name__)


class ChatCompletionModel(GenerateModel[Prompt, ChatCompletionOutput], ABC):
    model_task: ClassVar[str] = 'chat_completion'
    model_type: ClassVar[str]

    @abstractmethod
    def stream_generate(self, prompt: Prompt, **kwargs: Any) -> Iterator[ChatCompletionStreamOutput]:
        ...

    @abstractmethod
    def async_stream_generate(self, prompt: Prompt, **kwargs: Any) -> AsyncIterator[ChatCompletionStreamOutput]:
        ...

    def structure(
        self, output_structure_type: Type[O], instruction: str | None = None, **kwargs: Unpack['StructureKwargs']
    ) -> 'Structure[Self, O]':
        from generate.modifiers.structure import Structure

        return Structure(
            self,
            instruction=instruction,
            output_structure_type=output_structure_type,
            **kwargs,
        )

    def session(self) -> 'Session':
        from generate.modifiers.session import Session

        return Session(model=self)

    def agent(self, **kwargs: Unpack['AgentKwargs']) -> 'Agent':
        """Create an instance of the Agent class. An Agent is a wrapper around a model that allows tool use."""
        from generate.modifiers.agent import Agent

        return Agent(model=self, **kwargs)


class RemoteChatCompletionModel(ChatCompletionModel):
    settings: PlatformSettings
    http_client: HttpClient

    def __init__(
        self,
        parameters: ModelParameters,
        settings: PlatformSettings,
        http_client: HttpClient,
    ) -> None:
        self.parameters = parameters
        self.settings = settings
        self.http_client = http_client

    @classmethod
    def how_to_settings(cls) -> str:
        return f'{cls.__name__} Settings\n\n' + get_type_hints(cls)['settings'].how_to_settings()
