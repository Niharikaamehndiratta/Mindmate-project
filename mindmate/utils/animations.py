import requests
from streamlit_lottie import st_lottie

# Professional Animation URLs
LOGIN_ANIMATION = "https://assets9.lottiefiles.com/packages/lf20_hu9cd9.json"  # Clean login animation
LOADING_ANIMATION = "https://assets9.lottiefiles.com/packages/lf20_ra6kpuq6.json"  # Smooth loading spinner
SIGNUP_ANIMATION = "https://assets9.lottiefiles.com/packages/lf20_gn0y3jxk.json"  # Professional signup flow
PARTICLE_BG_ANIMATION = "https://assets9.lottiefiles.com/packages/lf20_ibtwig3i.json"  # Subtle particle effect

def load_lottie_animation(url: str):
    """Load Lottie animation from URL"""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def render_lottie(url: str, height: int = 300, key: str = None, loop: bool = True, 
                 quality: str = "high", speed: float = 1.0):
    """Helper to load and render a Lottie animation in Streamlit with professional settings"""
    animation_json = load_lottie_animation(url)
    if animation_json:
        st_lottie(
            animation_json,
            height=height,
            key=key,
            loop=loop,
            quality=quality,
            speed=speed
        )
