import streamlit as st
import base64
import os

def set_bg(main_bg_filename, sidebar_bg_filename=None, local=True, opacity=1.0, fixed=True):
    """
    Set Streamlit background for main and sidebar.

    Args:
        main_bg_filename (str): file name in ../images/ folder for main background.
        sidebar_bg_filename (str): file name in ../images/ folder for sidebar background.
        local (bool): True if using local images.
        opacity (float): transparency from 0.0 to 1.0.
        fixed (bool): True keeps background fixed during scroll.
    """

    def get_base64_of_bin_file(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()

    def get_mime_type(file_path):
        ext = os.path.splitext(file_path)[-1].lower()
        if ext in ['.jpg', '.jpeg']:
            return "image/jpeg"
        elif ext == '.png':
            return "image/png"
        return "image/png"

    # Build image paths from pro/images
    image_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
    main_bg_path = os.path.join(image_dir, main_bg_filename)
    sidebar_bg_path = os.path.join(image_dir, sidebar_bg_filename) if sidebar_bg_filename else None

    if local:
        main_bg = f"data:{get_mime_type(main_bg_path)};base64,{get_base64_of_bin_file(main_bg_path)}"
        sidebar_bg = f"data:{get_mime_type(sidebar_bg_path)};base64,{get_base64_of_bin_file(sidebar_bg_path)}" if sidebar_bg_path else None
    else:
        main_bg = main_bg_filename
        sidebar_bg = sidebar_bg_filename

    bg_fixed = "fixed" if fixed else "scroll"

    css = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("{main_bg}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: {bg_fixed};
        opacity: {opacity};
    }}
    """

    if sidebar_bg:
        css += f"""
        [data-testid="stSidebar"] {{
            background-image: url("{sidebar_bg}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: {bg_fixed};
            opacity: {opacity};
        }}
        """

    css += """
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0);
    }
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)

