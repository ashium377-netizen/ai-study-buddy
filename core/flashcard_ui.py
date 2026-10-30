import html


def card_html(question, answer, topic):
    q = html.escape(question)
    a = html.escape(answer)
    t = html.escape(topic)
    return f"""
<style>
  html, body {{ margin: 0; padding: 0; background: transparent; font-family: "Source Sans Pro", sans-serif; }}
  .pop {{ animation: pop 0.3s ease-out; }}
  @keyframes pop {{
    from {{ opacity: 0; transform: scale(0.94); }}
    to   {{ opacity: 1; transform: scale(1); }}
  }}
  .scene {{ perspective: 1200px; width: 100%; height: 300px; cursor: pointer; outline: none; margin-top: 4px; }}
  .card {{
    position: relative; width: 100%; height: 100%;
    transition: transform 0.55s; transform-style: preserve-3d;
  }}
  .card.flipped {{ transform: rotateY(180deg); }}
  .face {{
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    backface-visibility: hidden; -webkit-backface-visibility: hidden;
    border-radius: 18px; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 32px 36px; box-sizing: border-box; text-align: center;
  }}
  .front {{ background: linear-gradient(160deg, #ffffff 0%, #f7f4ff 100%); border: 2px solid #7c5cff; color: #1f2340; box-shadow: 0 10px 28px rgba(124, 92, 255, .18); }}
  .back  {{ background: linear-gradient(160deg, #f1edff 0%, #e6deff 100%); border: 2px solid #7c5cff; color: #1f2340; transform: rotateY(180deg); box-shadow: 0 10px 28px rgba(124, 92, 255, .18); }}
  .label {{ position: absolute; top: 14px; left: 20px; font-size: 12px; color: #6a5acd; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; }}
  .topic {{ position: absolute; top: 14px; right: 20px; font-size: 12px; color: #6b7280; }}
  .text  {{ font-size: 22px; line-height: 1.45; max-height: 200px; overflow-y: auto; }}
  .hint  {{ position: absolute; bottom: 14px; font-size: 13px; color: #7c5cff; }}
</style>
<div class="pop">
  <div class="scene" id="scene" tabindex="0">
    <div class="card" id="c">
      <div class="face front">
        <div class="label">Question</div>
        <div class="topic">{t}</div>
        <div class="text">{q}</div>
        <div class="hint">Click the card or press Space to flip</div>
      </div>
      <div class="face back">
        <div class="label">Answer</div>
        <div class="topic">{t}</div>
        <div class="text">{a}</div>
        <div class="hint">Click to flip back</div>
      </div>
    </div>
  </div>
</div>
<script>
  const card = document.getElementById('c');
  const scene = document.getElementById('scene');
  const flip = () => card.classList.toggle('flipped');
  scene.addEventListener('click', flip);
  window.addEventListener('keydown', (e) => {{
    if (e.code === 'Space') {{ e.preventDefault(); flip(); }}
  }});
  scene.focus();
</script>
"""
