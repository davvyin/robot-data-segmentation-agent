from moviepy.editor import VideoFileClip
from openai import OpenAI
import os
import base64
from config import config
from video_utils import frame_to_base64
from flask import current_app


def encode_image_base64(path):
    with open(path, "rb") as f:
        return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"


def describe_scene_with_gpt_vision(data):
    # data: [(ts, frame_image)]
    
    client = OpenAI(api_key=current_app.config["OPENAI_KEY"])
    
    #prompt
    content = [
                {
            "type": "text",
            "text": (
                "You are given a sequence of dashcam video frames from two robot arms. "
                "Each frame contains four horizontally aligned camera views:\n"
                "1. Top-down View — overview of the workspace\n"
                "2. Side View — perspective of object positioning\n"
                "3. Arm 1 View (front-facing)\n"
                "4. Arm 2 View (front-facing)\n\n"
                
                "Your task is to analyze the frames and identify key **object interactions** performed by the robot arms. "
                "Only describe meaningful interactions with objects — ignore idle motion or background activity. "
                "Focus on high-level tasks like gripping, pulling, tearing, pressing, cutting, and sealing. "
                "If multiple consecutive frames show the same action, summarize only the main action and skip redundancy.\n\n"

                "### Output Format\n"
                "Return the results as a JSON-style dictionary where:\n"
                "- Keys are time intervals in `MM:SS - MM:SS` format\n"
                "- Values are simple, clear descriptions of the main action being performed.\n\n"
                
                "### Example Output:\n"
                "{\n"
                '  "00:01 - 00:07": "Closing the Ziploc bag",\n'
                '  "00:04 - 00:10": "Grip the tape and pull it out of the dispenser and tear or cut the tape from the dispenser",\n'
                '  "00:12 - 00:18": "Apply and press down the tape on the surface"\n'
                "}\n\n"
                
                "### Additional Instructions:\n"
                "- Do not describe idle movement.\n"
                "- If both arms are involved in the same task, describe it as a single action (e.g., 'Both arms lift the object').\n"
                "- Prioritize descriptions that explain **object manipulation** over raw arm movement.\n"
                "- Convert timestamps from seconds to `MM:SS` format for readability."
            ),
        }
    ]
    

    for ts, base64_image in data:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            }
        )
        content.append(
            {"type": "text", "text": f"This image corresponds to timestamp: {ts:.1f}s"}
        )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        max_tokens=1000,
        response_format={"type": "json_object"},
    )

    return response.choices[0].message.content
