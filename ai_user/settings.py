import importlib
import logging

import discord
import openai
from redbot.core import checks, commands
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from ai_user.abc import MixinMeta
from ai_user.prompts.constants import DEFAULT_PROMPT, PRESETS

logger = logging.getLogger("red.bz_cogs.ai_user")


class settings(MixinMeta):
    @commands.group()
    async def ai_user(self, _):
        pass

    @ai_user.command()
    async def config(self, message):
        """ Returns current config """
        whitelist = await self.config.guild(message.guild).channels_whitelist()
        channels = [f"<#{channel_id}>" for channel_id in whitelist]

        embed = discord.Embed(title="AI User Settings")
        embed.add_field(name="Scan Images", value=await self.config.guild(message.guild).scan_images(), inline=False)
        embed.add_field(name="Model", value=await self.config.guild(message.guild).model(), inline=False)
        embed.add_field(name="Filter Responses", value=await self.config.guild(message.guild).filter_responses(), inline=False)
        embed.add_field(name="Reply Percent", value=f"{await self.config.guild(message.guild).reply_percent() * 100}%", inline=False)
        embed.add_field(name="Whitelisted Channels", value=" ".join(
            channels) if channels else "None", inline=False)
        embed.add_field(name="Always Reply on Ping or Reply", value=await self.config.guild(message.guild).reply_to_mentions_replies(), inline=False)
        embed.add_field(name="Max Messages in History", value=f"{await self.config.guild(message.guild).messages_backread()}", inline=False)
        embed.add_field(name="Max Time (s) between each Message in History", value=f"{await self.config.guild(message.guild).messages_backread_seconds()}", inline=False)
        return await message.send(embed=embed)

    @ai_user.command()
    @checks.is_owner()
    async def scan_images(self, ctx):
        """ Toggle image scanning (see README.md)"""
        try:
            importlib.import_module("pytesseract")
            importlib.import_module("torch")
            importlib.import_module("transformers")
            value = not (await self.config.guild(ctx.guild).scan_images())
            await self.config.guild(ctx.guild).scan_images.set(value)
            embed = discord.Embed(
                title="⚠️ WILL CAUSE HEAVY CPU LOAD ⚠️")
            embed.add_field(
                name="Scanning Images for this server now set to", value=value)
            return await ctx.send(embed=embed)
        except:
            logger.error("Image processing dependencies import failed. ", exc_info=True)
            await self.config.guild(ctx.guild).scan_images.set(False)
            await ctx.send("Image processing dependencies not available. Please install them (see cog README.md) to use this feature.")

    @ai_user.command()
    @checks.is_owner()
    async def percent(self, ctx, new_value):
        """Change the bot's response chance """
        try:
            new_value = float(new_value)
        except ValueError:
            return await ctx.send("Value must be a number")
        await self.config.guild(ctx.guild).reply_percent.set(new_value / 100)
        await self.cache_guild_options(ctx)
        embed = discord.Embed(
            title="Chance that the bot will reply on this server is now:")
        embed.add_field(name="", value=f"{new_value}%")
        return await ctx.send(embed=embed)

    @ai_user.command()
    @checks.is_owner()
    async def model(self, ctx, new_value):
        """ Changes chat completion model """
        if not openai.api_key:
            await self.initalize_openai(ctx)

        models_list = openai.Model.list()
        gpt_models = [model.id for model in models_list['data']
                      if model.id.startswith('gpt')]

        if new_value not in gpt_models:
            return await ctx.send(f"Invalid model. Choose from: {', '.join(gpt_models)}")

        await self.config.guild(ctx.guild).set(new_value)
        embed = discord.Embed(
            title="This server's chat model is now set to")
        embed.add_field(name="", value=new_value)
        return await ctx.send(embed=embed)

    @ai_user.command()
    @checks.admin()
    async def filter_responses(self, ctx):
        """ Toggles rudimentary filtering of canned replies """
        value = not await self.config.filter_responses()
        await self.config.guild(ctx.guild).filter_responses.set(value)
        embed = discord.Embed(
            title="Filtering canned responses for this server now set to")
        embed.add_field(name="", value=value)
        return await ctx.send(embed=embed)

    @ai_user.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def add(self, ctx, channel: discord.TextChannel):
        """ Add a channel to the whitelist to allow the bot to reply in"""
        if channel is None:
            return await ctx.send("Invalid channel mention, use #channel")
        new_whitelist = await self.config.guild(ctx.guild).channels_whitelist()
        if channel.id in new_whitelist:
            return await ctx.send("Channel already in whitelist")
        new_whitelist.append(channel.id)
        await self.config.guild(ctx.guild).channels_whitelist.set(new_whitelist)
        await self.cache_guild_options(ctx)
        embed = discord.Embed(title="The server whitelist is now")
        channels = [f"<#{channel_id}>" for channel_id in new_whitelist]
        embed.add_field(name="", value=" ".join(
            channels) if channels else "None")
        return await ctx.send(embed=embed)

    @ai_user.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def remove(self, ctx, channel: discord.TextChannel):
        """ Remove a channel from the whitelist"""
        if channel is None:
            return await ctx.send("Invalid channel mention, use #channel")
        new_whitelist = await self.config.guild(ctx.guild).channels_whitelist()
        if channel.id not in new_whitelist:
            return await ctx.send("Channel not in whitelist")
        new_whitelist.remove(channel.id)
        await self.config.guild(ctx.guild).channels_whitelist.set(new_whitelist)
        await self.cache_guild_options(ctx)
        embed = discord.Embed(title="The server whitelist is now")
        channels = [f"<#{channel_id}>" for channel_id in new_whitelist]
        embed.add_field(name="", value=" ".join(
            channels) if channels else "None")
        return await ctx.send(embed=embed)

    @ai_user.command()
    @checks.is_owner()
    async def mentions_replies(self, ctx):
        """ Toggles bot always replying to mentions/replies """
        value = not await self.config.guild(ctx.guild).reply_to_mentions_replies()
        await self.config.guild(ctx.guild).reply_to_mentions_replies.set(value)
        embed = discord.Embed(
            title="Always replying to mentions or replies for this server now set to")
        embed.add_field(name="", value=value)
        return await ctx.send(embed=embed)

    @ai_user.group()
    @checks.is_owner()
    async def history(self, _):
        """ Change the prompt context settings for the current server"""
        pass

    @history.command()
    @checks.is_owner()
    async def backread(self, ctx, new_value):
        """ Set max amount of messages to be used"""
        try:
            new_value = int(new_value)
        except ValueError:
            return await ctx.send("Value must be a number")
        await self.config.guild(ctx.guild).messages_backread.set(new_value)
        embed = discord.Embed(
            title="The number of previous messages used for context on this server is now")
        embed.add_field(name="", value=f"{new_value}")
        return await ctx.send(embed=embed)

    @history.command()
    @checks.is_owner()
    async def time(self, ctx, new_value):
        """ Set max time (s) allowed between messages to be used """
        try:
            new_value = int(new_value)
        except ValueError:
            return await ctx.send("Value must be a number")
        await self.config.guild(ctx.guild).messages_backread_seconds.set(new_value)
        embed = discord.Embed(
            title="The max time (s) allowed between messages for context on this server is now")
        embed.add_field(name="", value=f"{new_value}")
        return await ctx.send(embed=embed)

    @ai_user.group()
    @checks.admin()
    async def prompt(self, _):
        """ Change the prompt settings for the current server"""
        pass

    @prompt.command()
    @checks.is_owner()
    async def reset(self, ctx):
        """ Reset ALL prompts (inc. user) to default (cynical)"""
        await self.config.guild(ctx.guild).custom_text_prompt.set(None)
        for member in ctx.guild.members:
            await self.config.member(member).custom_text_prompt.set(None)
        embed = discord.Embed(title="All prompts resetted")
        return await ctx.send(embed=embed)

    @prompt.group()
    async def show(self, _):
        """ Show prompts """
        pass

    @show.command(name="server")
    @checks.admin()
    async def server_prompt(self, ctx):
        """ Show current server prompt"""
        custom_text_prompt = await self.config.guild(ctx.guild).custom_text_prompt()
        res = "The prompt for this server is:\n"
        if custom_text_prompt:
            res += box(f"{self._truncate_prompt(custom_text_prompt)}")
        else:
            res += box(f"{DEFAULT_PROMPT}")
        return await ctx.send(res)

    @show.command()
    @checks.admin()
    async def users(self, ctx):
        """ Show all users with custom prompts """
        pages = []
        for member in ctx.guild.members:
            custom_text_prompt = await self.config.member(member).custom_text_prompt()
            if custom_text_prompt:
                page = f"The prompt for user {member.name} is:"
                page += box(f"\n{self._truncate_prompt(custom_text_prompt)}")
                pages.append(page)
        if not pages:
            return await ctx.send("No users with custom prompts")
        if len(pages) == 1:
            return await ctx.send(pages[0])
        return await menu(ctx, pages, DEFAULT_CONTROLS)

    @prompt.command()
    @checks.admin()
    async def preset(self, ctx, preset):
        """ List presets using 'list', or set a preset """
        if preset == 'list':
            embed = discord.Embed(
                title="Presets", description="Use `[p]prompt preset <preset>` to set a preset")
            embed.add_field(name="Available presets",
                            value="\n".join(PRESETS.keys()), inline=False)
            return await ctx.send(embed=embed)
        if preset not in PRESETS:
            return await ctx.send("Invalid preset. Use `list` to see available presets")
        await self.config.guild(ctx.guild).custom_text_prompt.set(PRESETS[preset])
        res = "The prompt for this server is now changed to:\n"
        res += box(f"{PRESETS[preset]}")
        return await ctx.send(res)

    @prompt.group()
    @checks.is_owner()
    async def custom(self, _):
        """ Customize the prompt sent to OpenAI """
        pass

    @custom.command()
    @checks.is_owner()
    async def server(self, ctx, prompt: str = ""):
        """ Set custom prompt for current server (Enclose with \" \") """
        if prompt == "":
            await self.config.guild(ctx.guild).custom_text_prompt.set(None)
            return await ctx.send(f"The prompt for this server is now reset to the default prompt")
        await self.config.guild(ctx.guild).custom_text_prompt.set(prompt)
        res = "The prompt for this server is now changed to:\n"
        res += box(f"{self._truncate_prompt(prompt)}")
        return await ctx.send(res)

    @custom.command()
    @checks.is_owner()
    async def user(self, ctx, member: discord.Member, prompt: str = ""):
        """ Set custom prompt per user in current server (Enclose \" \") """
        if prompt == "":
            await self.config.member(member).custom_text_prompt.set(None)
            return await ctx.send(f"The prompt for user {member.mention} is now reset to default server prompt")
        await self.config.member(member).custom_text_prompt.set(prompt)
        res = f"The prompt for user {member.mention} is now changed to:\n"
        res += box(f"{self._truncate_prompt(prompt)}")
        return await ctx.send(res)

    async def cache_guild_options(self, message):
        self.cached_options[message.guild.id] = {
            "channels_whitelist": await self.config.guild(message.guild).channels_whitelist(),
            "reply_percent": await self.config.guild(message.guild).reply_percent(),
        }

    def _truncate_prompt(self, prompt):
        return prompt[:1900] + "..." if len(prompt) > 1900 else prompt
