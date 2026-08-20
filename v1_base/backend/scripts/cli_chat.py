"""Chat interactif — comparaison transport de base."""

from app.agent import ShippingAgent


def main() -> None:
    agent = ShippingAgent()
    print(
        "AgenCurent v1_base — transport de base uniquement "
        "(Стандарт, sans options)."
    )
    print("Tapez 'exit' pour quitter.")

    while True:
        try:
            user_input = input("\nVous: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir.")
            break

        if user_input.lower() in {"exit", "quit", "q"}:
            print("Au revoir.")
            break

        if not user_input:
            continue

        try:
            reply = agent.chat(user_input)
        except Exception as exc:
            print(f"\nErreur: {exc}")
            continue

        print(f"\nAgent: {reply}")


if __name__ == "__main__":
    main()
