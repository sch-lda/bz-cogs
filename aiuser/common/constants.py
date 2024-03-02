import re

### DEFAULTS ###

DEFAULT_PROMPT = "You are a helpful assistant called bugbot made by yeahsch \
You can help me by answering my questions. You can also ask me questions."
DEFAULT_PRESETS = {
    "cynical": DEFAULT_PROMPT,
    "neutral": "You are a helpful assistant called bugbot made by yeahsch. You can help me by answering my questions. You can also ask me questions.",
    "tsundere": "You are a helpful assistant called bugbot made by yeahsch. You can help me by answering my questions. You can also ask me questions.",
}
DEFAULT_RANDOM_PROMPTS = [
    "Talk about how today is {currentweekday}. You must state that today is {currentweekday}.",
    "Talk about how empty the Discord channel is",
    "Talk about how you are currently ordering takeout. State the specific cuisine ordered, and any other details you'd like to the Discord channel.",
    "Make up a topic in the news. State that you just read about it in the news. Talk about that topic."
]
DEFAULT_REMOVE_PATTERNS = [
    r'^As an AI language model,?',
    r'^(User )?"?{botname}"? (said|says|respond(ed|s)|replie[ds])( to [^":]+)?:?',
    r'^As "?{botname}"?, (I|you)( might| would| could)? (respond|reply|say)( with)?( something like)?:?',
    r'^You respond as "?{botname}"?:',
    r'^[<({{\[]{botname}[>)}}\]]',  # [name], {name}, <name>, (name)
    r'^{botname}:',
    r'^(User )?"?{authorname}"? (said|says|respond(ed|s)|replie[ds])( to [^":]+)?:?',
    r'^As "?{authorname}"?, (I|you)( might| would| could)? (respond|reply|say)( with)?( something like)?:?',
    r'^You respond as "?{authorname}"?:',
    r'^[<({{\[]{authorname}[>)}}\]]',  # [name], {name}, <name>, (name)
    r'^{authorname}:',
    r'\n*\[Image[^\]]+\]'
]
DEFAULT_IMAGE_REQUEST_TRIGGER_WORDS = [
    "image", "images", "picture", "pictures", "photo", "photos", "photograph", "photographs"]
DEFAULT_IMAGE_REQUEST_TRIGGER_SECOND_PERSON_WORDS = ["yourself", "you"]
DEFAULT_REPLY_PERCENT = 1.0

### END DEFAULTS ###

IMAGE_REQUEST_CHECK_PROMPT = "As an AI, named {botname}, you are tasked to analyze messages directed towards you. Your role is to identify whether each specific message is asking you to send a picture of yourself or not. Messages can be phrased in a variety of ways, so you should look for key contextual clues such as requests for images, photographs, selfies, or other synonyms, but make sure it's specifically asking for a picture of 'you'. If the message explicitly requests a picture of {botname}, you are to respond with 'True'. If the message doesn't solicit a picture of 'you', then respond with 'False'."
IMAGE_REQUEST_SD_GEN_PROMPT = """
I want you to act as a Stable Diffusion Art Prompt Generator. The formula for a prompt is made of parts, the parts are indicated by brackets. The [Subject] is the person place or thing the image is focused on. [Emotions] is the emotional look the subject or scene might have. [Verb] is What the subject is doing, such as standing, jumping, working and other varied that match the subject. [Adjectives] like beautiful, rendered, realistic, tiny, colorful and other varied that match the subject. The [Environment] in which the subject is in, [Lighting] of the scene like moody, ambient, sunny, foggy and others that match the Environment and compliment the subject. [Photography type] like Polaroid, long exposure, monochrome, GoPro, fisheye, bokeh and others. And [Quality] like High definition, 4K, 8K, 64K UHD, SDR and other. The subject and environment should match and have the most emphasis.
It is ok to omit one of the other formula parts. Each formula part should be less then four words.

Here is a sample output: "Beautiful woman, contemplative and reflective, sitting on a bench, cozy sweater, autumn park with colorful leaves, soft overcast light, muted color photography style, 4K quality."

Convert the below message to a Stable Diffusion Art Prompt.  The prompt should have no second person references, no line breaks, no delimiters, and be kept as concise as possible while still conveying a full scene.
"""
IMAGE_REQUEST_REPLY_PROMPT = "You sent the picture above. Respond accordingly."

# regex patterns
URL_PATTERN = re.compile(r"(https?://\S+)")
YOUTUBE_URL_PATTERN = re.compile(r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(.+)")
YOUTUBE_VIDEO_ID_PATTERN = re.compile(
    r"(?:youtube(?:-nocookie)?\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|v\/|t\/\S*?\/?)([a-zA-Z0-9_-]{11})")
SINGULAR_MENTION_PATTERN = re.compile(r"^<@!?&?(\d+)>$")


# misc
MIN_MESSAGE_LENGTH = 2
MAX_MESSAGE_LENGTH = 2000  # in words
OPENROUTER_URL = "https://openrouter.ai/api/"

# image captioning
IMAGE_UPLOAD_LIMIT = 2 * (1024 * 1024)  # 2 MB


# models
FUNCTION_CALLING_SUPPORTED_MODELS = [
    "gpt-4",
    "gpt-4-1106-preview",
    "gpt-4-0613",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo-0125",
    "openai/gpt-4",
    "openai/gpt-4-1106-preview",
    "openai/gpt-4-0613",
    "openai/gpt-3.5-turbo",
    "openai/gpt-3.5-turbo-1106",
    "openai/gpt-3.5-turbo-0613",
    "openai/gpt-3.5-turbo-0125"
]
VISION_SUPPORTED_MODELS = [
    "gpt-4-vision-preview",
    "openai/gpt-4-vision-preview",
    "haotian-liu/llava-13b",
    "nousresearch/nous-hermes-2-vision-7b"
]
OTHER_MODELS_LIMITS = {
    "gpt-3.5-turbo-1106": 12000,
    "gpt-4-1106-preview": 123000,
    "gpt-4-vision-preview": 123000,
    "claude-2": 98000,
    "claude-instant-v1": 98000,
    "dolphin-mixtral-8x7b": 31000,
    "mistral-tiny": 31000,
    "mistral-small": 31000,
    "mistral-medium": 31000,
    "toppy-m-7b": 31000,
    "nous-capybara-34b": 31000,
    "stripedhyena-hessian-7b": 31000,
    "stripedhyena-nous-7b": 31000,
    "mythomist-7b": 31000,
    "cinematika-7b": 31000,
    "mixtral-8x7b-instruct": 31000,
    "mixtral-8x7b": 31000,
    "gemini-pro": 31000,
    "gemini-pro-vision": 15000,
    "rwkv-5-world-3b": 9000,
    "rwkv-5-3b-ai-town": 9000,
    "noromaid-mixtral-8x7b-instruct": 7000,
    "bagel-34b": 7000,
    "pplx-7b-chat": 7000,
    "noromaid-20b": 7000,
    "palm-2-chat-bison": 7000,
    "claude-v1": 7000,
    "claude-1.2": 7000,
    "claude-instant-1.0": 7000,
    "codellama-34b-instruct": 6000,
    "synthia-70b": 6000,
    "mistral-7b-instruct": 6000,
    "mistral-7b-openorca": 6000,
    "mythalion-13b": 6000,
    "xwin-lm-70b": 6000,
    "goliath-120b": 6000,
    "weaver": 6000,
    "palm-2-codechat-bison": 6000,
    "openchat-7b": 6000,
    "remm-slerp-l2-13b": 5000
}
