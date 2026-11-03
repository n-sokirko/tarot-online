"""Runway image-to-video adapter. Defaults to a local dry run, never a paid call.

One generation request is submitted only with --submit and a configured key.
Task IDs are saved before waiting, so --task-id can resume without generating again.
"""
from pathlib import Path
import argparse
import base64
import json
import os
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
PROMPT = (
    'First-person cinematic fantasy survival-choice scene. Slowly move forward toward '
    'three ornate doors in a ruined midnight garden. Keep all three doors and their '
    'sun, crescent moon, and star emblems consistent and visible throughout. '
    'Low mist drifts naturally across the wet reflective floor, a few golden dust '
    'particles float through the light, ivy gently sways. Subtle distant dawn light. '
    'No cuts, no door opening, no characters, no hands, no text, no logos. '
    'Preserve the image composition and elegant violet, obsidian and gold palette.'
)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--submit', action='store_true', help='Submit one potentially billable 5-second job')
    parser.add_argument('--dry-run', action='store_true', help='Validate local inputs only (default)')
    parser.add_argument('--task-id', help='Resume an existing task instead of creating a new one')
    args = parser.parse_args()
    image = ROOT / 'doors-keyframe.png'
    if not image.is_file():
        parser.error('Missing doors-keyframe.png')
    from runwayml import RunwayML
    configured = bool(os.environ.get('RUNWAYML_API_SECRET'))
    spec = {'model': 'gen4.5', 'ratio': '720:1280', 'duration': 5, 'prompt_text': PROMPT}
    print(json.dumps({'sdk': 'runwayml', 'image_exists': True, 'image_bytes': image.stat().st_size,
                      'api_key_present': configured, 'request': spec,
                      'mode': 'submit' if args.submit else 'resume' if args.task_id else 'dry-run'}, indent=2))
    if args.dry_run or not (args.submit or args.task_id):
        return
    if args.submit and args.task_id:
        parser.error('Use --submit OR --task-id, not both')
    if not configured:
        parser.error('RUNWAYML_API_SECRET is missing. Configure it securely outside source control; no request was sent.')
    client = RunwayML(max_retries=0)  # Never resubmit a creation request automatically.
    if args.task_id:
        task = client.tasks.retrieve(args.task_id)
    else:
        task = client.image_to_video.create(
            **spec, prompt_image='data:image/png;base64,' + base64.b64encode(image.read_bytes()).decode())
        (ROOT/'runway-task.json').write_text(json.dumps({'task_id': task.id, 'model': spec['model']}, indent=2))
    completed = task.wait_for_task_output()
    if not completed.output:
        raise RuntimeError('Task completed without an output URL')
    with urlopen(completed.output[0], timeout=120) as response:
        (ROOT/'doors-motion.mp4').write_bytes(response.read())
    print('Saved doors-motion.mp4')

if __name__ == '__main__':
    main()
