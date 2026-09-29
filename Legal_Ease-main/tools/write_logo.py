import base64
import os

PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII="
)

def main():
    here = os.path.dirname(__file__)
    assets_dir = os.path.join(here, '..', 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    out_path = os.path.join(assets_dir, 'logo.png')
    with open(out_path, 'wb') as f:
        f.write(base64.b64decode(PNG_B64))
    print('Wrote sample logo to', out_path)

if __name__ == '__main__':
    main()
