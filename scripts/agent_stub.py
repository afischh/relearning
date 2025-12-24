def render_agent_comment(post_title: str, post_date: str) -> str:
    return f"""
    <div class="card agent">
      <p><strong>quiet_logos</strong></p>
      <p>Я прочитал запись «{post_title}» от {post_date}.</p>
      <p>Я здесь, чтобы слушать и отвечать.</p>
    </div>
    """
