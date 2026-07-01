import os

from enable_banking import EnableBanking

from storage.file_session_store import FileSessionStore
from storage.secret_manager_session_store import SecretManagerSessionStore


RUNNING_IN_CLOUD = os.getenv("K_SERVICE") is not None


def get_session_store():
    if RUNNING_IN_CLOUD:
        return SecretManagerSessionStore(
            project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
            secret_name="enablebanking-session",
        )

    return FileSessionStore("session.json")


def main():
    session_store = get_session_store()

    bank = EnableBanking(session_store)

    session = bank.authorize()

    session_store.save(session)

    print()
    print("✅ Session saved successfully.")
    print(f"Valid until: {session['access']['valid_until']}")


if __name__ == "__main__":
    main()