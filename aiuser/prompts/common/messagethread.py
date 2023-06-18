import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import List

import discord
import tiktoken
from discord import Message
from redbot.core import Config
from redbot.core.bot import Red

from aiuser.common.constants import OPENAI_MODEL_TOKEN_LIMIT
from aiuser.common.types import ContextOptions, RoleType
from aiuser.prompts.common.helpers import (format_embed_content,
                                           format_sticker_content,
                                           format_text_content, is_embed_valid)
from aiuser.prompts.common.messageentry import MessageEntry

logger = logging.getLogger("red.bz_cogs.aiuser")


@dataclass()
class MessageThread:
    bot: Red
    config: Config
    initial_message: Message
    messages: list = field(default_factory=list)
    messages_ids: set = field(default_factory=set)
    tokens: int = 0
    _encoding: tiktoken.Encoding = None
    model: str = None
    ignore_regex: re.Pattern = None,
    cached_messages = None

    async def add_msg(self, content: str, message: Message, prepend: bool = False, force: bool = False):
        if message.id in self.messages_ids and not force:
            logger.debug(f"Skipping duplicate message in {message.guild.name} when creating context")
            return

        if not await self.bot.allowed_by_whitelist_blacklist(message.author):
            return
        if message.author.id in await self.config.optout():
            return
        if not message.author.id in await self.config.optin() and not await self.config.guild(message.guild).optin_by_default():
            return

        # noinspection PyTypeChecker
        role: RoleType = "user" if message.author.id != self.bot.user.id else "assistant"
        messages_item = MessageEntry(role, content)

        insertion_index = self._get_insertion_index(prepend)
        self.messages.insert(insertion_index, messages_item)
        self.messages_ids.add(message.id)
        await self._add_tokens(content)

    async def add_system(self, content: str, prepend: bool = False):
        messages_item = MessageEntry("system", content)
        insertion_index = self._get_insertion_index(prepend)
        self.messages.insert(insertion_index, messages_item)
        await self._add_tokens(content)

    async def _add_tokens(self, content):
        if not self._encoding:
            await self.initialize_encoding()
        tokens = self._encoding.encode(content, disallowed_special=())
        self.tokens += len(tokens)

    async def initialize_encoding(self):
        self.model = (await self.config.guild(self.initial_message.guild).model())
        try:
            self._encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            self._encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    def _get_insertion_index(self, prepend: bool) -> int:
        return 0 if prepend else len(self.messages)

    def get_messages(self):
        result = []
        for message in self.messages:
            result.append(asdict(message))
        return result

    async def create_context(self, context_options: ContextOptions):
        limit = await self.config.guild(self.initial_message.guild).messages_backread()
        max_seconds_gap = await self.config.guild(self.initial_message.guild).messages_backread_seconds()
        start_time: datetime = context_options.start_time + \
            timedelta(seconds=1) if context_options.start_time else None
        self.ignore_regex = context_options.ignore_regex
        self.cached_messages = context_options.cached_messages
        if not self.model:
            self.model = (await self.config.guild(self.initial_message.guild).model())

        past_messages = [message async for message in self.initial_message.channel.history(limit=limit,
                                                                                           before=self.initial_message,
                                                                                           after=start_time,
                                                                                           oldest_first=False)]

        if past_messages and abs((past_messages[0].created_at - self.initial_message.created_at).total_seconds()) > max_seconds_gap:
            return

        for message in past_messages:
            if await self.config.guild(message.guild).optin_by_default():
                break
            if (not message.author.bot) and (message.author.id not in await self.config.optin()) and (message.author.id not in await self.config.optout()):
                prefix = (await self.bot.get_prefix(message))[0]
                embed = discord.Embed(title=":information_source: AI User Opt-In / Opt-Out", color=await self.bot.get_embed_color(message))
                embed.description = f"Hey there! Looks like some user(s) has not opted in or out of AI User! \n Please use `{prefix}aiuser optin` or `{prefix}aiuser optout` to opt in or out of sending messages to OpenAI or an external endpoint. \n This embed will stop showing up if all users chatting have opted in or out."
                await message.channel.send(embed=embed)
                break

        for i in range(len(past_messages)-1):
            if self.model.startswith("gpt-") and self.tokens > OPENAI_MODEL_TOKEN_LIMIT.get(self.model, 3000):
                return logger.debug(f"{self.tokens} tokens used - nearing limit, stopping context creation for {self.initial_message.id}")
            if await self._valid_time_between_messages(past_messages, i, max_seconds_gap):
                await self._add_contextual_message(past_messages[i])
            else:
                await self._add_contextual_message(past_messages[i])
                break

    @staticmethod
    async def _valid_time_between_messages(past_messages: List[Message], index, max_gap) -> bool:
        time_between_messages = abs(past_messages[index].created_at - past_messages[index+1].created_at).total_seconds()
        if time_between_messages > max_gap:
            return False
        return True

    async def _add_contextual_message(self, message: Message):
        if self.ignore_regex and self.ignore_regex.search(message.content):
            return

        if message.reference:
            # TODO: handle references
            pass

        if message.stickers:
            return await self.add_msg(await format_sticker_content(message), message, prepend=True)

        if message.id in self.cached_messages:
            await self.add_msg(self.cached_messages[message.id], message, prepend=True)
            if message.content:
                await self.add_msg(format_text_content(message), message, prepend=True, force=True)
        elif message.attachments:
            return await self.add_system("A message was skipped", prepend=True)

        if len(message.embeds) > 0 and is_embed_valid(message):
            return await self.add_msg(format_embed_content(message), message, prepend=True)

        if message.content:
            await self.add_msg(format_text_content(message), message, prepend=True)
