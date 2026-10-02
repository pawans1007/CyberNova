from ui.desktop import main as desktop_main


def main():
    """Launch the CyberNova desktop application."""
    try:
        desktop_main()
    except KeyboardInterrupt:
        print("\nCyberNova stopped.")
    except Exception as error:
        print(f"\nCyberNova startup error: {error}")
        raise


if __name__ == "__main__":
    main()

