from server import PromptServer
import os
from aiohttp import web
from io import BytesIO
import shutil
import json
import mimetypes
import folder_paths  # Required for ComfyUI image handling

datapath = os.path.join(os.path.dirname(__file__), 'promptImages')

# [Keep all original route handlers unchanged]
@PromptServer.instance.routes.get("/prompt_gallery/image")
async def view_image(request):
    if "filename" in request.rel_url.query:
        filename = request.rel_url.query["filename"]
        subfolder = request.rel_url.query.get("subfolder", "")

        # validation for security: prevent accessing arbitrary path
        if '..' in filename or '..' in subfolder:
            return web.Response(status=400)

        if subfolder == "custom":
            # For custom images, look directly in the 'custom' folder
            base_path = os.path.join(datapath, "custom")
        else:
            # For package thumbnails, look in the 'thumbnails' folder
            base_path = os.path.join(datapath, "thumbnails", subfolder)

        # Try different extensions
        for ext in ['', '.jpeg', '.jpg', '.png', '.webp']:
            fullpath = os.path.join(base_path, filename + ext)
            if os.path.exists(fullpath):
                with open(fullpath, 'rb') as f:
                    content = f.read()

                content_type, _ = mimetypes.guess_type(fullpath)
                if not content_type:
                    content_type = 'application/octet-stream'

                return web.Response(body=content, content_type=content_type,
                                    headers={"Content-Disposition": f"filename=\"{filename}{ext}\""})

        return web.Response(status=404)

    return web.Response(status=400)


@PromptServer.instance.routes.post("/prompt_gallery/upload")
async def upload_image(request):
    try:
        post = await request.post()
        image = post.get("image")

        if image and image.file:
            filename = image.filename
            if not filename:
                return web.json_response({"error": "No filename provided"}, status=400)

            subfolder = post.get("subfolder", "")
            upload_path = os.path.join(datapath, os.path.normpath(subfolder))
            fullpath = os.path.join(upload_path, filename)

            # validation for security: prevent accessing arbitrary path
            if subfolder[0] == '/' or '..' in fullpath or '..' in filename:
                return web.json_response({"error": "Invalid file path"}, status=400)

            if not os.path.exists(upload_path):
                os.makedirs(upload_path)

            # Save the file directly without processing
            with open(fullpath, "wb") as f:
                shutil.copyfileobj(image.file, f)

            relative_path = os.path.join(subfolder, filename)
            return web.json_response({"name": relative_path})
        else:
            return web.json_response({"error": "No image file provided"}, status=400)

    except Exception as e:
        print(f"Error in upload_image: {str(e)}")
        return web.json_response({"error": str(e)}, status=500)

@PromptServer.instance.routes.get("/prompt_gallery/yaml")
async def view_yaml(request):
    if "filename" in request.rel_url.query:
        filename = request.rel_url.query["filename"]

        if 'subfolder' in request.rel_url.query:
            subfolder = request.rel_url.query["subfolder"]
            filename = os.path.join(filename, subfolder)
        else:
            subfolder = ""

        # validation for security: prevent accessing arbitrary path
        if '..' in filename or '..' in subfolder:
            return web.Response(status=400)

        fullpath = os.path.join(datapath, filename)

        try:
            with open(fullpath) as yaml:
                text = yaml.read()
                return web.Response(text=text, content_type='text/html')
        except FileNotFoundError:
            return web.Response(text="", status=404)
        except Exception as e:
            print(f"Error reading YAML file {fullpath}: {str(e)}")
            return web.Response(text="", status=500)

    return web.Response(status=400)

@PromptServer.instance.routes.post("/prompt_gallery/update_libraries")
async def update_libraries(request):
    try:
        data = await request.json()
        filename = "promptGallery_libraries.json"
        fullpath = os.path.join(datapath, filename)

        with open(fullpath, 'w') as f:
            json.dump(data, f, indent=2)

        return web.Response(status=200)
    except Exception as e:
        print(f"Error updating libraries file: {str(e)}")
        return web.Response(status=500, text=str(e))


class LoadImageWithPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        images = [f for f in os.listdir(input_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        return {
            "required": {
                "image": (sorted(images), {"image_upload": True}),
                "prompt_text": ("STRING", {"multiline": False, "rows": 1, "cols": 30}),  # Adding a text area
            },
        }
    
    CATEGORY = "image"
    FUNCTION = "load_image"
    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("image", "prompt",)
    
    def load_image(self, image):
        image_path = folder_paths.get_annotated_filepath(image)
        #prompt = os.path.splitext(image)[0]  # Get filename without extension as prompt  
        prompt = text
        
        # Automatically set the prompt_text to the filename prompt if not provided
        if not prompt_text:
            prompt_text = prompt
            
        i = folder_paths.LoadImage()(image)
        return (i, prompt,)


NODE_CLASS_MAPPINGS = {
    "LoadImageWithPrompt": LoadImageWithPrompt
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageWithPrompt": "Load Image (With Prompt)"
}

WEB_DIRECTORY = "./web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
