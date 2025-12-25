import yaml
import sys
import os

# Mock the imports or use the actual ones
sys.path.append(os.getcwd())
from app.routers.mods import LiteralString, literal_string_representer

def test_yaml_style():
    yaml.add_representer(LiteralString, literal_string_representer)
    
    projects = ["fabric-api:tV4Gc0Zo", "xaeros-minimap:hztxb2W2"]
    compose_data = {
        "version": "3",
        "services": {
            "mc": {
                "environment": {
                    "TYPE": "FABRIC",
                    "MODRINTH_PROJECTS": LiteralString("\n".join(projects) + "\n")
                }
            }
        }
    }
    
    output = yaml.dump(compose_data, sort_keys=False, default_flow_style=False)
    print("Generated YAML:")
    print(output)
    
    assert "MODRINTH_PROJECTS: |" in output
    assert "fabric-api:tV4Gc0Zo" in output
    assert "xaeros-minimap:hztxb2W2" in output
    print("Verification SUCCESS")

if __name__ == "__main__":
    test_yaml_style()
