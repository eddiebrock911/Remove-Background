import streamlit as st
import os
from PIL import Image, ImageFilter, ImageEnhance
from rembg import remove
import io

# streamlit run remove.py

st.set_page_config(page_title="Background Remover Pro", layout="wide")

st.title("🎨 Advanced Background Removal Tool")
st.markdown("Upload an image and remove its background with custom styling options")

# Sidebar for options
st.sidebar.header("⚙️ Settings")

# Create columns for layout
col1, col2 = st.columns(2)

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file:
    # Read and display original image
    image = Image.open(uploaded_file)
    
    with col1:
        st.subheader("Original Image")
        st.image(image, use_container_width=True)
    
    # Background removal options
    st.sidebar.subheader("Background Removal")
    alpha_matting = st.sidebar.checkbox("Alpha Matting (Better edges)", value=False)
    alpha_matting_foreground_threshold = st.sidebar.slider(
        "Foreground Threshold", 0, 255, 240, disabled=not alpha_matting
    )
    alpha_matting_background_threshold = st.sidebar.slider(
        "Background Threshold", 0, 255, 10, disabled=not alpha_matting
    )
    alpha_matting_erode_size = st.sidebar.slider(
        "Erode Size", 0, 40, 10, disabled=not alpha_matting
    )
    
    # Background style options
    st.sidebar.subheader("Background Style")
    bg_option = st.sidebar.selectbox(
        "Background Type",
        ["Transparent", "Solid Color", "Gradient", "Blur Original", "Custom Image"]
    )
    
    bg_color = "#FFFFFF"
    gradient_color1 = "#FF6B6B"
    gradient_color2 = "#4ECDC4"
    blur_amount = 20
    custom_bg = None
    
    if bg_option == "Solid Color":
        bg_color = st.sidebar.color_picker("Pick a background color", "#FFFFFF")
    elif bg_option == "Gradient":
        gradient_color1 = st.sidebar.color_picker("Gradient Color 1", "#FF6B6B")
        gradient_color2 = st.sidebar.color_picker("Gradient Color 2", "#4ECDC4")
        gradient_direction = st.sidebar.selectbox("Direction", ["Vertical", "Horizontal", "Diagonal"])
    elif bg_option == "Blur Original":
        blur_amount = st.sidebar.slider("Blur Amount", 5, 50, 20)
    elif bg_option == "Custom Image":
        custom_bg_file = st.sidebar.file_uploader("Upload background image", type=["jpg", "jpeg", "png"])
        if custom_bg_file:
            custom_bg = Image.open(custom_bg_file)
    
    # Additional effects
    st.sidebar.subheader("Effects")
    add_shadow = st.sidebar.checkbox("Add Shadow")
    shadow_blur = st.sidebar.slider("Shadow Blur", 0, 50, 15, disabled=not add_shadow)
    shadow_offset = st.sidebar.slider("Shadow Offset", 0, 30, 10, disabled=not add_shadow)
    
    enhance_edges = st.sidebar.checkbox("Enhance Edges")
    
    brightness = st.sidebar.slider("Brightness", 0.5, 2.0, 1.0, 0.1)
    contrast = st.sidebar.slider("Contrast", 0.5, 2.0, 1.0, 0.1)
    
    # Output settings
    st.sidebar.subheader("Output Settings")
    output_format = st.sidebar.selectbox("Format", ["PNG", "WEBP", "JPG"])
    output_quality = st.sidebar.slider("Quality", 1, 100, 95)
    
    if st.button("🚀 Remove Background", type="primary"):
        with st.spinner("Processing image..."):
            # Remove background
            if alpha_matting:
                output = remove(
                    image,
                    alpha_matting=True,
                    alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                    alpha_matting_background_threshold=alpha_matting_background_threshold,
                    alpha_matting_erode_size=alpha_matting_erode_size
                )
            else:
                output = remove(image)
            
            # Enhance edges if selected
            if enhance_edges:
                output = output.filter(ImageFilter.SHARPEN)
            
            # Create background based on selection
            if bg_option == "Transparent":
                final_image = output
            else:
                # Create background canvas
                bg = Image.new("RGBA", output.size)
                
                if bg_option == "Solid Color":
                    # Solid color background
                    bg = Image.new("RGBA", output.size, bg_color)
                    
                elif bg_option == "Gradient":
                    # Create gradient
                    width, height = output.size
                    gradient = Image.new("RGBA", output.size)
                    
                    # Parse colors
                    r1, g1, b1 = tuple(int(gradient_color1[i:i+2], 16) for i in (1, 3, 5))
                    r2, g2, b2 = tuple(int(gradient_color2[i:i+2], 16) for i in (1, 3, 5))
                    
                    for i in range(height if gradient_direction != "Horizontal" else width):
                        if gradient_direction == "Vertical":
                            ratio = i / height
                            r = int(r1 + (r2 - r1) * ratio)
                            g = int(g1 + (g2 - g1) * ratio)
                            b = int(b1 + (b2 - b1) * ratio)
                            for j in range(width):
                                gradient.putpixel((j, i), (r, g, b, 255))
                        elif gradient_direction == "Horizontal":
                            ratio = i / width
                            r = int(r1 + (r2 - r1) * ratio)
                            g = int(g1 + (g2 - g1) * ratio)
                            b = int(b1 + (b2 - b1) * ratio)
                            for j in range(height):
                                gradient.putpixel((i, j), (r, g, b, 255))
                        else:  # Diagonal
                            ratio = i / max(width, height)
                            r = int(r1 + (r2 - r1) * ratio)
                            g = int(g1 + (g2 - g1) * ratio)
                            b = int(b1 + (b2 - b1) * ratio)
                            for j in range(min(width, height)):
                                if i < height and j < width:
                                    gradient.putpixel((j, i), (r, g, b, 255))
                    
                    bg = gradient
                    
                elif bg_option == "Blur Original":
                    # Blur the original image
                    bg = image.convert("RGBA").filter(ImageFilter.GaussianBlur(blur_amount))
                    
                elif bg_option == "Custom Image" and custom_bg:
                    # Resize custom background to match
                    bg = custom_bg.convert("RGBA").resize(output.size, Image.Resampling.LANCZOS)
                
                # Add shadow if selected
                if add_shadow:
                    shadow = Image.new("RGBA", output.size, (0, 0, 0, 0))
                    shadow_layer = Image.new("RGBA", output.size, (0, 0, 0, 128))
                    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
                    
                    # Offset shadow
                    shadow.paste(shadow_layer, (shadow_offset, shadow_offset))
                    shadow.paste(output, (0, 0), output)
                    bg.paste(shadow, (0, 0), shadow)
                    final_image = bg
                else:
                    bg.paste(output, (0, 0), output)
                    final_image = bg
            
            # Apply brightness and contrast
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(final_image)
                final_image = enhancer.enhance(brightness)
            
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(final_image)
                final_image = enhancer.enhance(contrast)
            
            # Display result
            with col2:
                st.subheader("Processed Image")
                st.image(final_image, use_container_width=True)
            
            # Save and download
            os.makedirs("output", exist_ok=True)
            output_filename = f"output.{output_format.lower()}"
            output_path = os.path.join("output", output_filename)
            
            if output_format == "JPG":
                # Convert to RGB for JPG
                rgb_image = Image.new("RGB", final_image.size, (255, 255, 255))
                rgb_image.paste(final_image, mask=final_image.split()[3] if final_image.mode == "RGBA" else None)
                rgb_image.save(output_path, quality=output_quality, optimize=True)
            else:
                final_image.save(output_path, quality=output_quality, optimize=True)
            
            st.success(f"✅ Background processed and saved to {output_path}")
            st.balloons()
            
            # Create download button
            with open(output_path, "rb") as file:
                btn = st.download_button(
                    label="⬇️ Download Image",
                    data=file,
                    file_name=output_filename,
                    mime=f"image/{output_format.lower()}"
                )
            
            # Show file info
            file_size = os.path.getsize(output_path) / 1024
            st.info(f"📊 File size: {file_size:.2f} KB | Format: {output_format} | Dimensions: {final_image.size[0]}x{final_image.size[1]}px")
else:
    st.info("👆 Please upload an image to get started")
    
# Footer
st.markdown("---")
st.markdown("Made with Ankit❤️")