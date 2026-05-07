from PIL import Image
from pathlib import Path


def parse_size(size: str) -> int:
    size = size.strip().lower()

    units = {
        "kb": 1024,
        "mb": 1024 ** 2,
        "gb": 1024 ** 3,
    }

    for unit, multiplier in units.items():
        if size.endswith(unit):
            value = float(size.replace(unit, "").strip())
            return int(value * multiplier)

    raise ValueError("Use tamanhos como: 500kb, 2mb ou 1gb")


def adjust_file_to_exact_size(output_path: Path, target_bytes: int):
    current_size = output_path.stat().st_size

    if current_size > target_bytes:
        raise ValueError(
            f"O arquivo ficou maior que o alvo. "
            f"Atual: {current_size} bytes | Alvo: {target_bytes} bytes"
        )

    missing_bytes = target_bytes - current_size

    if missing_bytes > 0:
        with open(output_path, "ab") as file:
            file.write(b"\0" * missing_bytes)


def compress_image_to_exact_size(input_path: str, output_path: str, target_size: str):
    target_bytes = parse_size(target_size)

    img = Image.open(input_path)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    output_path = Path(output_path)

    scale = 1.0

    while True:
        resized_img = img.copy()

        if scale < 1.0:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)

        quality_min = 5
        quality_max = 100
        best_quality = None

        while quality_min <= quality_max:
            quality = (quality_min + quality_max) // 2

            resized_img.save(
                output_path,
                format="JPEG",
                quality=quality,
                optimize=False
            )

            current_size = output_path.stat().st_size

            if current_size <= target_bytes:
                best_quality = quality
                quality_min = quality + 1
            else:
                quality_max = quality - 1

        if best_quality is not None:
            resized_img.save(
                output_path,
                format="JPEG",
                quality=best_quality,
                optimize=False
            )

            adjust_file_to_exact_size(output_path, target_bytes)

            final_size = output_path.stat().st_size

            print(f"Imagem salva em: {output_path}")
            print(f"Tamanho final: {final_size} bytes")
            print(f"Tamanho final: {final_size / 1024:.2f} KB")
            print(f"Qualidade usada: {best_quality}")
            print(f"Escala usada: {scale:.2f}")

            return

        scale *= 0.9

        if scale < 0.1:
            raise Exception("Não foi possível comprimir a imagem para o tamanho desejado.")


compress_image_to_exact_size(input_path="assets/input.jpg", output_path="assets/imagem_2mb.jpg", target_size="2mb")
compress_image_to_exact_size(input_path="assets/input.jpg", output_path="assets/imagem_300kb.jpg", target_size="300kb")