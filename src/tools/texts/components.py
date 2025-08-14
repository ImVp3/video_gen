""" High-level text UI components and wrappers. """
from tools.schema.dataclass import Payload
from .core import render_text_element
from .layout import wrapped_text_clip, structured_multiline_clip
from typing import Any, Dict
from moviepy import VideoClip
from typing import List, Callable

def title_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("course_title", payload, spec, **kw)
def subtitle_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("subtitle", payload, spec, **kw)
def lowerthird_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("lowerthird_name", payload, spec, **kw)
def section_marker_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("section_marker", payload, spec, **kw)
def heading_h1_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("heading_h1", payload, spec, **kw)
def heading_h2_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("heading_h2", payload, spec, **kw)
def heading_h3_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("heading_h3", payload, spec, **kw)
def body_bullet_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("body_bullet", payload, spec, **kw)
def definition_term_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("definition_term", payload, spec, **kw)
def step_label_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("step_label", payload, spec, **kw)
def code_snippet_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("code_snippet", payload, spec, **kw)
def equation_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("equation", payload, spec, **kw)
def chart_labels_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("chart_labels", payload, spec, **kw)
def data_labels_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("data_labels", payload, spec, **kw)
def captions_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("captions", payload, spec, **kw)
def speaker_label_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("speaker_label", payload, spec, **kw)
def quiz_question_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("quiz_question", payload, spec, **kw)
def quiz_choices_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("quiz_choices", payload, spec, **kw)
def quiz_feedback_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("quiz_feedback", payload, spec, **kw)
def cta_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("cta", payload, spec, **kw)
def progress_ui_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("progress_ui", payload, spec, **kw)
def timestamp_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("timestamp", payload, spec, **kw)
def legal_credits_clip(payload: Payload, spec: Dict[str, Any], **kw) -> VideoClip: return render_text_element("legal_credits", payload, spec, **kw)

def title_wrap(text, spec, **kw):           return wrapped_text_clip("course_title", text, spec, **kw)
def subtitle_wrap(text, spec, **kw):        return wrapped_text_clip("subtitle", text, spec, **kw)
def definition_wrap(text, spec, **kw):      return wrapped_text_clip("definition_term", text, spec, **kw)
def eq_wrap(text, spec, **kw):              return wrapped_text_clip("equation", text, spec, **kw)
def caption_wrap(text, spec, **kw):         return wrapped_text_clip("captions", text, spec, **kw)
def h1_wrap(text, spec, **kw):              return wrapped_text_clip("heading_h1", text, spec, **kw)
def h2_wrap(text, spec, **kw):              return wrapped_text_clip("heading_h2", text, spec, **kw)
def h3_wrap(text, spec, **kw):              return wrapped_text_clip("heading_h3", text, spec, **kw)

# Structured: dùng cho Bullets/Quiz choices… hiển thị so-le
def bullets_staggered_clip(items, spec, **kw):      return structured_multiline_clip("body_bullet", items, spec, **kw)
def quiz_choices_staggered_clip(items, spec, **kw): return structured_multiline_clip("quiz_choices", items, spec, **kw)