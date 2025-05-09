from moviepy.editor import VideoFileClip
from openai import OpenAI
import os
import base64
from config import config
from video_utils import frame_to_base64
from prompt import prompt_v1, prompt_v2
import logging
# from flask import current_app
import copy
import time


def encode_image_base64(path):
    with open(path, "rb") as f:
        return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"


def describe_scene_with_gpt_vision(data, api_key, logger=None):
    # data: [(ts, frame_image)]
    client = OpenAI(api_key=api_key)

    # prompt
    content = [
        {
            "type": "text",
            "text": prompt_v1['text']}
    ]

    for ts, base64_image in data:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            }
        )
        content.append(
            {"type": "text",
                "text": f"This frame corresponds to timestamp (MM:SS) {int(ts // 60):02}:{int(ts % 60):02}"}
        )

    # log the sending content
    cpy_content = copy.deepcopy(content)
    for item in cpy_content:
        if "image_url" in item:
            item['image_url'] = "redacted"

    if logger:
        logger.info(
            f"Sent Content: {cpy_content}"
        )
    # time.sleep(10)
    # dummy = '{"00:00 - 00:10": "Hello World"}'
    # return dummy

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        max_tokens=1000,
        response_format={"type": "json_object"},
        temperature=0,
        top_p=1
    )

    return response.choices[0].message.content
