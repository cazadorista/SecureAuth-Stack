import json
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

KEYCLOAK_DIR = Path(__file__).parent
IMPORT_DIR = KEYCLOAK_DIR / "import"
OUTPUT_FILE = IMPORT_DIR / "realms-export.json"
USERS_FILE = KEYCLOAK_DIR / "users.json"
ENV_FILE = KEYCLOAK_DIR / ".env"
ROLES_FILE = KEYCLOAK_DIR / "playground_roles.json"


def load_playground_roles():
    if not ROLES_FILE.exists():
        print(f"[i] Brak pliku {ROLES_FILE.name} – role nie zostaną dodane.")
        return []
    try:
        with open(ROLES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[-] BŁĄD podczas odczytu {ROLES_FILE.name}: {e}")
        return []

def load_environment():
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=True)
        print(f"[i] Załadowano zmienne z pliku: {ENV_FILE.name}")
    else:
        load_dotenv(override=True)


def substitute_env_vars(data):
    if isinstance(data, dict):
        return {k: substitute_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [substitute_env_vars(i) for i in data]
    elif isinstance(data, str):
        exact_match = re.fullmatch(r"\$\{([^}]+)\}", data.strip())
        if exact_match:
            var_name = exact_match.group(1).strip()
            val = os.environ.get(var_name)
            if val is not None:
                if val.lower() == "true":
                    return True
                if val.lower() == "false":
                    return False
                if val.isdigit():
                    return int(val)
                return val
            return data

        def replace_match(match):
            var_name = match.group(1).strip()
            return os.environ.get(var_name, f"${{{var_name}}}")

        return re.sub(r"\$\{([^}]+)\}", replace_match, data)
    return data


def apply_pre_substitute_patches(data, file_name):
    if not isinstance(data, dict):
        return data

    PLAYGROUND_ROLES = load_playground_roles()

    realm_name = data.get("realm", "")

    if realm_name == "master" or "master" in file_name.lower():
        actions = data.get("requiredActions", [])
        for action in actions:
            if action.get("alias") == "webauthn-register-passwordless":
                action["defaultAction"] = "${KC_MASTER_REQUIRE_REGISTER_WEBAUTHN}"
                print(f"    [patch] Wstrzyknięto placeholder do 'webauthn-register-passwordless' w realmie master")

    if realm_name == "playground" or "playground" in file_name.lower():
        if "roles" not in data:
            data["roles"] = {}
        if "realm" not in data["roles"]:
            data["roles"]["realm"] = []

        existing_roles = {r.get("name") for r in data["roles"]["realm"]}
        for role in PLAYGROUND_ROLES:
            if role["name"] not in existing_roles:
                data["roles"]["realm"].append(role)
                print(f"    [patch] Dodano rolę '{role['name']}' do realmu playground")

    return data


def load_users():
    if not USERS_FILE.exists():
        print(f"[i] Brak pliku {USERS_FILE.name} – użytkownicy nie zostaną dodani.")
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            print(f"[i] Wczytano dane użytkowników z: {USERS_FILE.name}")
            return json.load(f)
    except Exception as e:
        print(f"[-] BŁĄD podczas odczytu {USERS_FILE.name}: {e}")
        sys.exit(1)


def process_realm_object(realm_obj, users_data):
    realm_name = realm_obj.get("realm")
    if realm_name and realm_name in users_data:
        realm_users = users_data[realm_name].get("users", [])
        if "users" not in realm_obj:
            realm_obj["users"] = []

        realm_obj["users"].extend(realm_users)
        print(f"    [+] Dodano {len(realm_users)} uż. do realmu '{realm_name}'")


def merge_realms():
    load_environment()

    IMPORT_DIR.mkdir(parents=True, exist_ok=True)

    source_files = [
        f
        for f in KEYCLOAK_DIR.glob("realm-export*.json")
        if f.resolve() != OUTPUT_FILE.resolve()
    ]

    source_files.sort(
        key=lambda p: (0 if "master" in p.name.lower() else 1, p.name)
    )

    if not source_files:
        if OUTPUT_FILE.exists():
            print(
                f"[!] Brak nowych plików realm-export-*.json. Używam istniejącego {OUTPUT_FILE.name}"
            )
            sys.exit(0)
        else:
            print(
                "[-] BŁĄD: Brak plików źródłowych realm-export-*.json oraz brak realms-export.json! Keycloak nie wystartuje."
            )
            sys.exit(1)

    users_data = substitute_env_vars(load_users())

    merged_data = []
    print(f"[i] Znaleziono {len(source_files)} plik(ów) realmów do scalenia:")

    for file_path in source_files:
        print(f"  - {file_path.name}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                if isinstance(data, dict):
                    data = apply_pre_substitute_patches(data, file_path.name)
                elif isinstance(data, list):
                    data = [apply_pre_substitute_patches(r, file_path.name) for r in data]

                data = substitute_env_vars(data)

                if isinstance(data, dict):
                    process_realm_object(data, users_data)
                    merged_data.append(data)
                elif isinstance(data, list):
                    for realm in data:
                        if isinstance(realm, dict):
                            process_realm_object(realm, users_data)
                    merged_data.extend(data)
                    
        except Exception as e:
            print(f"[-] BŁĄD podczas odczytu {file_path.name}: {e}")
            sys.exit(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)

    print(
        f"[+] Pomyślnie scalono {len(merged_data)} realm(y) w pliku: {OUTPUT_FILE.name}"
    )


if __name__ == "__main__":
    merge_realms()