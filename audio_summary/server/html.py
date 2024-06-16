from audio_summary.__version__ import __version__

def dict_to_style(style:dict):
    return '; '.join([
        f"{k}: {v}" for k, v in style.items()
    ])

footer_style = {
    "position": "fixed",
    "bottom": "0px",
    "left": "0px",
    "color":"rgb(49, 51, 63)",
    "padding": "10px 0 10px 0",
    "background-color": "#E7ECEF",
    "width": "100%",
    "text-align": "center", 
    "font-size":"14px",
}

footer = (
    f"""<div style="{dict_to_style(footer_style)}">"""
    f"""<a href="https://github.com/thisishugow/audio-summary" target="_blank">Audio Summary</a> | """
    f"v{__version__} | "
    """<a  href="https://www.linkedin.com/in/thisisyuwang" target="_blank">Hugo Wang</a>"""
    "</div>"
)