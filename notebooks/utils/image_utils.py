import base64
from typing import Union

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


def save_plot_png(fig_or_ax: Union["plt.Figure", "plt.Axes", None], path: str) -> str:
    """Save a matplotlib figure or current plot to PNG and return path."""
    if plt is None:
        raise ImportError("matplotlib is required to save plots")
    if fig_or_ax is None:
        plt.savefig(path, format='png', bbox_inches='tight')
    elif hasattr(fig_or_ax, 'savefig'):
        fig_or_ax.savefig(path, format='png', bbox_inches='tight')
    else:
        raise ValueError("Unsupported figure/axes object")
    return path


def build_image_payload(path: str, mime: str = 'image/png') -> dict:
    """Read image file and return a payload dict with MIME and base64 data."""
    with open(path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode('utf-8')
    return {"type": "image", "mimeType": mime, "data": b64}
