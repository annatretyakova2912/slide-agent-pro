from typing import TypedDict, List, Dict, Any


class OutlineSlide(TypedDict, total=False):
    slide_number: int
    title: str
    objective: str
    intent_type: str
    key_points: List[str]


class CopySlide(TypedDict, total=False):
    slide_number: int
    title: str
    subtitle: str
    body_bullets: List[str]
    slogan: str


class IntentSlide(TypedDict, total=False):
    slide_number: int
    slide_intent: str
    story_role: str
    structure_hint: str
    confidence: float


class LayoutSlide(TypedDict, total=False):
    slide_number: int
    template_id: str
    rationale: str
    slots: Dict[str, Any]


class AssetSlide(TypedDict, total=False):
    slide_number: int
    image_url: str
    image_prompt: str
    icon_ids: List[str]
    decorations: List[str]


class QualityIssue(TypedDict, total=False):
    slide_number: int
    severity: str
    issue: str
    recommendation: str


class GraphState(TypedDict, total=False):
    user_input: str
    topic: str
    audience: str
    desired_slide_count: int
    additional_information: str

    outline: Dict[str, Any]
    copydeck: Dict[str, Any]
    intent_map: Dict[str, Any]
    global_design_token: Dict[str, Any]
    layout_plan: Dict[str, Any]
    asset_plan: Dict[str, Any]
    rendered_presentation: Dict[str, Any]
    quality_report: Dict[str, Any]

    revision_count: int
    max_revision_rounds: int
    needs_revision: bool
    next_action: str
    error: str
