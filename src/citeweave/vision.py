"""Local visual caption verification with content- and model-keyed caching."""

import hashlib
import json
from pathlib import Path

from . import config
from .generation import GPU_LOCK
from .web import cache_image

PROMPT = (
    "Describe what is visibly shown in this image in 2-3 precise sentences. "
    "Include readable chart labels when clear. Do not invent identity, dates or measurements."
)


def caption_images(images, generator, limit=10):
    import gc

    import httpx
    import torch
    from PIL import Image
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

    directory = config.DATA / "cache/captions"
    directory.mkdir(parents=True, exist_ok=True)
    source = Path(config.VISION_MODEL) / "source.json"
    revision = source.read_text() if source.exists() else str(config.VISION_MODEL)
    results, pending = [], []
    for image in images[:limit]:
        try:
            path = cache_image(image["url"])
            key = hashlib.sha256(
                path.read_bytes() + revision.encode() + PROMPT.encode()
            ).hexdigest()
            cached = directory / (key + ".json")
            item = {**image, "publisher_caption": image["caption"], "local_path": str(path)}
            if cached.exists():
                item.update(
                    caption=json.loads(cached.read_text())["caption"],
                    caption_kind="local_visual_description",
                )
            else:
                pending.append((item, path, cached))
            results.append(item)
        except (ValueError, OSError, httpx.HTTPError) as e:
            results.append({**image, "image_error": str(e)[:150]})
    if not pending:
        return results + images[limit:]
    with GPU_LOCK:
        generator.unload()
        processor = AutoProcessor.from_pretrained(config.VISION_MODEL, local_files_only=True)
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            config.VISION_MODEL,
            dtype=torch.bfloat16,
            device_map="cuda",
            local_files_only=True,
            attn_implementation="sdpa",
        ).eval()
        try:
            for item, path, cached in pending:
                with Image.open(path) as opened:
                    picture = opened.convert("RGB")
                prompt = processor.apply_chat_template(
                    [
                        {
                            "role": "user",
                            "content": [{"type": "image"}, {"type": "text", "text": PROMPT}],
                        }
                    ],
                    tokenize=False,
                    add_generation_prompt=True,
                )
                batch = processor(text=[prompt], images=[picture], return_tensors="pt").to("cuda")
                with torch.inference_mode():
                    output = model.generate(**batch, max_new_tokens=180, do_sample=False)
                caption = processor.batch_decode(
                    output[:, batch.input_ids.shape[1] :], skip_special_tokens=True
                )[0]
                item.update(caption=caption, caption_kind="local_visual_description")
                cached.write_text(json.dumps({"caption": caption}, ensure_ascii=False))
                del batch, output
        finally:
            del model, processor
            gc.collect()
            torch.cuda.empty_cache()
    return results + images[limit:]
