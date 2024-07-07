import os
from flask import Flask, request, render_template, send_file, redirect
from PIL import Image
import io

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return redirect("/join")


@app.route("/join", methods=["GET", "POST"])
def upload_and_join():
    if request.method == "POST":
        if "file1" not in request.files or "file2" not in request.files:
            return "Please upload two images", 400

        file1 = request.files["file1"]
        file2 = request.files["file2"]

        if file1.filename == "" or file2.filename == "":
            return "No selected file", 400

        if not allowed_file(file1.filename) or not allowed_file(file2.filename):
            return "Invalid file type", 400

        try:
            img1 = Image.open(file1)
            img2 = Image.open(file2)

            max_height = max(img1.size[1], img2.size[1])

            # Create a new image with the combined width and max height
            new_img = Image.new(
                "RGB", (img1.size[0] + img2.size[0], max_height), color="white"
            )

            # Paste the images
            new_img.paste(img1, (0, 0))
            new_img.paste(img2, (img1.size[0], 0))

            # Save the result
            output = io.BytesIO()
            format = request.form.get("format", "JPEG")
            if format.upper() == "PNG":
                new_img.save(output, format="PNG")
            else:
                new_img.save(output, format="JPEG")
            output.seek(0)

            return send_file(
                output,
                mimetype=f"image/{format.lower()}",
                as_attachment=True,
                download_name=f"joined_image.{format.lower()}",
            )

        except Exception as e:
            return str(e), 500

    return render_template("upload.html")


@app.route("/overlay", methods=["GET", "POST"])
def upload_and_overlay():
    if request.method == "POST":
        if "file1" not in request.files or "file2" not in request.files:
            return "Please upload two images", 400

        file1 = request.files["file1"]
        file2 = request.files["file2"]

        if file1.filename == "" or file2.filename == "":
            return "No selected file", 400

        if not allowed_file(file1.filename) or not allowed_file(file2.filename):
            return "Invalid file type", 400

        try:
            img1 = Image.open(file1).convert("RGBA")
            img2 = Image.open(file2).convert("RGBA")

            # Determine which image is larger
            if img1.size[0] * img1.size[1] > img2.size[0] * img2.size[1]:
                larger_img, smaller_img = img1, img2
            else:
                larger_img, smaller_img = img2, img1

            # Calculate scaling factor
            scale_factor = max(
                larger_img.size[0] / smaller_img.size[0],
                larger_img.size[1] / smaller_img.size[1],
            )

            # Resize smaller image
            new_size = (
                int(smaller_img.size[0] * scale_factor),
                int(smaller_img.size[1] * scale_factor),
            )
            smaller_img = smaller_img.resize(new_size, Image.LANCZOS)

            # Create a new image with the size of the larger image
            new_img = Image.new("RGBA", larger_img.size, (0, 0, 0, 0))

            # Calculate position to paste smaller image (centered)
            paste_pos = (
                (larger_img.size[0] - smaller_img.size[0]) // 2,
                (larger_img.size[1] - smaller_img.size[1]) // 2,
            )

            # Paste larger image
            new_img = Image.alpha_composite(new_img, larger_img)

            # Create a semi-transparent version of the smaller image
            smaller_img_transparent = Image.blend(
                Image.new("RGBA", smaller_img.size, (0, 0, 0, 0)), smaller_img, 0.5
            )

            # Paste smaller image
            new_img.paste(smaller_img_transparent, paste_pos, smaller_img_transparent)

            # Save the result
            output = io.BytesIO()
            format = request.form.get("format", "PNG")
            if format.upper() == "JPEG":
                new_img = new_img.convert("RGB")
                new_img.save(output, format="JPEG")
            else:
                new_img.save(output, format="PNG")
            output.seek(0)

            return send_file(
                output,
                mimetype=f"image/{format.lower()}",
                as_attachment=True,
                download_name=f"overlaid_image.{format.lower()}",
            )

        except Exception as e:
            return str(e), 500

    return render_template("upload.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
