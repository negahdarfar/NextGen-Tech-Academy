from nextgen_academy.cli import build_parser


def test_video_plan_parser_has_single_storyboard_argument():
    args = build_parser().parse_args([
        "video-plan", "--topic", "robotics", "--storyboard", "draft.json"
    ])
    assert args.storyboard == "draft.json"
    assert args.scene is None


def test_local_draft_command_defaults_to_small_ollama_model():
    args = build_parser().parse_args(["draft-script", "--topic", "robotics"])
    assert args.model == "qwen2.5:3b"
    assert args.output == "output/storyboard.json"
