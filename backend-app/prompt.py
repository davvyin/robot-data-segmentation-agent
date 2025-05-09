prompt_v1 = {
    "text": (
        "You are given a sequence of dashcam video frames from a robotic task execution."
        "The object starts in the **center of the top-down view** and remains visible during manipulation. "
        "Each frame contains four camera views:\n"
        "1. **Stationary Top-down View** — overview of the workspace\n"
        "2. **Stationary Side View** — perspective of object manipulation (counter clocked wise 90 degree)\n"
        "The main object is in the center of the Top-down view"

        "### Task:\n"
        "Analyze the frames and identify key object interactions, or how the key object interacte with other object."
        # "Describe only the **main action** performed, focusing on the objective being achieved (may be use the object to do something or modify the object). "
        "Describe only the **main actions** performed, emphasizing the goal achieved (e.g., using objects to perform task or tasks or altering the object's state such as opening the lid of a cup)."
        "Do not describe the movement of robotic arms unless it directly impacts the object's state or use the object do something "
        "If multiple frames show the same action, merge them into one segment. "
        "Each segment should represent a continuous **main action** performed by the robot arm."
        "Focus on **what is achieved**, not how it is done.\n\n"

        "### Output Format:\n"
        "Return the results as a JSON dictionary where:\n"
        "- Keys are time intervals in `MM:SS - MM:SS` format\n"
        "- Values are clear descriptions of the action performed.\n\n"

        "### Example Output:\n"
        "{\n"
        '  "00:01 - 00:07": "Closing the Ziploc bag",\n'
        '  "00:04 - 00:10": "Grip the tape and pull it out of the dispenser and tear or cut the tape from the dispenser",\n'
        '  "00:12 - 00:18": "Apply and press down the tape on the surface"\n'
        "}\n\n"
        """{\n
    "00:00 - 00:05": "Placing the shoe on the foot",\n
    "00:06 - 00:12": "Securing the laces",\n
    "00:13 - 00:25": "Adjusting the fit of the shoe"\n
    }\n\n"""
        """{\n
  "00:00 - 00:05": "Gripping the cup",\n
  "00:06 - 00:09": "Lifting the cup",\n
  "00:10 - 00:12": "Open the lid of the cup"\n
}\n\n"""


        "### Additional Instructions:\n"
        "- Skip idle movement or background shifts.\n"
        "- Merge consecutive frames if the action is the same.\n"
        "- Convert timestamps to `MM:SS` format.\n"
        "- Keep descriptions concise and focused only on the end goal."
    )
}

prompt_v2 = {
    "text": """
You are given a sequence of dashcam video frames from a robotic task execution. \n
The object starts in the **center of the top-down view** and remains visible during manipulation. \n
Each frame contains two camera views:\n
1. **Stationary Top-down View** — overview of the workspace.\n
2. **Stationary Side View** — perspective of object manipulation (counter-clockwise 90 degrees).\n\n

### Task:\n
Analyze the frames and identify the **main task objectives** being achieved, not just the physical movements. \n
You should interpret the robot's intention and group multiple movements into a single logical action whenever possible. \n\n

For example:\n
- If the robot arm grasps an object, lifts it, and places it somewhere, it should be described as **"Placing the object in position"**.\n
- If the robot rotates and adjusts an object multiple times, summarize it as **"Aligning the object for the next step"**.\n
- If the robot performs a sequence of fine movements, group them as **"Securing the object in place"**.\n\n

### Output Format:\n
Return the results as a JSON dictionary where:\n
- Keys are time intervals in `MM:SS - MM:SS` format.\n
- Values are **high-level descriptions** of the task completed, focusing on the **intended outcome**, not the individual motions.\n

### Example Output:\n
{\n
  "00:00 - 00:05": "Placing the shoe on the foot",\n
  "00:06 - 00:12": "Securing the laces",\n
  "00:13 - 00:25": "Adjusting the fit of the shoe"\n
}\n\n

### Additional Instructions:\n
- Skip idle movements or minor adjustments unless they complete a meaningful step.\n
- Focus on **why** the robot is moving, not just **how** it is moving.\n
- Merge consecutive frames if the action achieves a single goal.\n
- Convert timestamps to `MM:SS` format.\n
- Use verbs that reflect **completion of tasks** (e.g., "Placing", "Securing", "Adjusting")."""
}
