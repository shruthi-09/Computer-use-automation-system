from src.agent.planner import LLMPlanner


planner = LLMPlanner()

decision = planner.decide(
    goal="Search for member 12345.",
    observation={
        "title": "Member Search",
        "url": "http://127.0.0.1:8000/",
        "visible_text": (
            "Community Credit Union\n"
            "Member Search\n"
            "Member ID\n"
            "Search"
        ),
        "controls": [
            {
                "tag": "input",
                "type": "text",
                "name": "member_id",
                "id": "member_id",
            },
            {
                "tag": "button",
                "text": "Search",
            },
        ],
    },
    history=[],
)

print("\nLLM CONNECTION SUCCESSFUL\n")

print(
    decision.model_dump_json(
        indent=2
    )
)