from pathlib import Path
import yaml
from jinja2 import Template

def main():
    config = yaml.safe_load(Path("cli_config.yaml").read_text())
    template = Template(Path("cli_template.j2").read_text(), keep_trailing_newline=True)
    rendered = template.render(config=config)
    Path("atlas_cli.py").write_text(rendered)

if __name__ == "__main__":
    main()
