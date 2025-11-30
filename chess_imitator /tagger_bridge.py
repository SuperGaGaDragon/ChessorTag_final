"""Public entry point for the chess_imitator tagger bridge."""

from players.tagger_bridge import cli_main, tag_candidates_payload

__all__ = ["tag_candidates_payload"]


if __name__ == "__main__":
    cli_main()
